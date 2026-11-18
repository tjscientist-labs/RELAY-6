// SPDX-License-Identifier: GPL-2.0-only
#include "link.h"

#include <Preferences.h>
#include <RadioLib.h>
#include <SPI.h>

#include "board.h"

namespace r6link {
namespace {

SPIClass radioSpi(HSPI);
SX1262 radio = new Module(board::kLoraNss, board::kLoraDio1, board::kLoraRst, board::kLoraBusy, radioSpi);
volatile bool rxFlag = false;
Preferences prefs;
uint32_t txStored = 0, rxStored = 0;

#if defined(ESP8266) || defined(ESP32)
ICACHE_RAM_ATTR
#endif
void onRadio() { rxFlag = true; }

bool hex(const String& s, uint8_t* out, size_t n) {
  if (s.length() != n * 2) return false;
  for (size_t i = 0; i < n; ++i) {
    char b[3] = {s[2 * i], s[2 * i + 1], 0};
    char* end = nullptr;
    out[i] = static_cast<uint8_t>(strtoul(b, &end, 16));
    if (*end) return false;
  }
  return true;
}

}  // namespace

bool radioBegin() {
  radioSpi.begin(board::kLoraSck, board::kLoraMiso, board::kLoraMosi, board::kLoraNss);
  int st = radio.begin(board::kFreqMHz, board::kBwKHz, board::kSf, board::kCr, board::kSyncWord, board::kPowerDbm, 8,
                       board::kTcxoVolts, false);
  if (st != RADIOLIB_ERR_NONE) {
    Serial.printf("radio begin failed: %d\n", st);
    return false;
  }
  radio.setDio2AsRfSwitch(true);
  radio.setCRC(2);
  radio.setPacketReceivedAction(onRadio);
  radio.startReceive();
  return true;
}

bool receive(Rx& rx) {
  if (!rxFlag) return false;
  rxFlag = false;
  const size_t n = radio.getPacketLength();
  if (n == 0 || n > sizeof rx.buf) {
    radio.startReceive();
    return false;
  }
  const int st = radio.readData(rx.buf, n);
  rx.len = n;
  rx.rssi = static_cast<int16_t>(radio.getRSSI());
  rx.snr = static_cast<int8_t>(radio.getSNR());
  radio.startReceive();
  return st == RADIOLIB_ERR_NONE;  // CRC errors are dropped here
}

bool send(const uint8_t* p, size_t n) {
  const int st = radio.transmit(const_cast<uint8_t*>(p), n);
  rxFlag = false;
  radio.startReceive();
  return st == RADIOLIB_ERR_NONE;
}

bool loadKeys(relay6::LinkKeys& k) {
  prefs.begin("relay6", true);
  const bool have = prefs.getBytes("key", k.key, 16) == 16;
  k.system = prefs.getUInt("sys", 0);
  k.bank = static_cast<uint8_t>(prefs.getUChar("bank", 1));
  prefs.end();
  return have && k.paired();
}

void saveKeys(const relay6::LinkKeys& k) {
  prefs.begin("relay6", false);
  prefs.putBytes("key", k.key, 16);
  prefs.putUInt("sys", k.system);
  prefs.putUChar("bank", k.bank);
  prefs.putUInt("txs", 0);   // new pairing: counters start again on both sides
  prefs.putUInt("rxs", 0);
  prefs.end();
}

uint32_t bootTxCounter() {
  prefs.begin("relay6", false);
  const uint32_t stored = prefs.getUInt("txs", 0);
  uint32_t first, ns;
  relay6::CounterBlock::onBoot(stored, first, ns);
  prefs.putUInt("txs", ns);  // reserve the block before using any of it
  prefs.end();
  txStored = ns;
  return first;
}

void afterSend(uint32_t nextCounter) {
  uint32_t ns;
  if (relay6::CounterBlock::needAdvance(nextCounter, txStored, ns)) {
    prefs.begin("relay6", false);
    prefs.putUInt("txs", ns);
    prefs.end();
    txStored = ns;
  }
}

uint32_t bootRxFloor() {
  prefs.begin("relay6", true);
  rxStored = prefs.getUInt("rxs", 0);
  prefs.end();
  return rxStored;
}

void afterReceive(uint32_t lastAccepted) {
  if (lastAccepted >= rxStored + relay6::CounterBlock::kBlock) {
    rxStored = lastAccepted;
    prefs.begin("relay6", false);
    prefs.putUInt("rxs", rxStored);
    prefs.end();
  }
}

uint16_t getU16(const char* key, uint16_t def) {
  prefs.begin("relay6", true);
  const uint16_t v = prefs.getUShort(key, def);
  prefs.end();
  return v;
}

void putU16(const char* key, uint16_t v) {
  prefs.begin("relay6", false);
  prefs.putUShort(key, v);
  prefs.end();
}

String readLine() {
  static String acc;
  while (Serial.available()) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\r') continue;
    if (c == '\n') {
      String line = acc;
      acc = "";
      line.trim();
      return line;
    }
    if (acc.length() < 120) acc += c;
  }
  return String();
}

bool console(const String& line, const relay6::LinkKeys& k) {
  if (line == "show") {
    Serial.printf("paired=%s system=%08lX bank=%u freq=%.3f MHz bw=%.0f kHz sf=%d\n", k.paired() ? "yes" : "NO",
                  static_cast<unsigned long>(k.system), k.bank, board::kFreqMHz, board::kBwKHz, board::kSf);
    return true;
  }
  if (line.startsWith("pair ")) {
    // pair <32 hex key> <8 hex system> [bank]
    String rest = line.substring(5);
    rest.trim();
    const int sp = rest.indexOf(' ');
    if (sp < 0) { Serial.println("usage: pair <32 hex key> <8 hex system> [bank]"); return true; }
    relay6::LinkKeys nk;
    String sys = rest.substring(sp + 1);
    sys.trim();
    int sp2 = sys.indexOf(' ');
    String bank = sp2 > 0 ? sys.substring(sp2 + 1) : String("1");
    if (sp2 > 0) sys = sys.substring(0, sp2);
    uint8_t s4[4];
    if (!hex(rest.substring(0, sp), nk.key, 16) || !hex(sys, s4, 4)) { Serial.println("bad hex"); return true; }
    nk.system = relay6::get32(s4);
    nk.bank = static_cast<uint8_t>(bank.toInt() > 0 && bank.toInt() < 100 ? bank.toInt() : 1);
    if (!nk.paired()) { Serial.println("refused: zero key or system"); return true; }
    saveKeys(nk);
    Serial.println("paired; restarting");
    delay(200);
    ESP.restart();
    return true;
  }
  return false;
}

}  // namespace r6link
