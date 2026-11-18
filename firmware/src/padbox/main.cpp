// SPDX-License-Identifier: GPL-2.0-or-later
// RELAY-6 pad box application: reads the hardware (E-2, E-3) into relay6::PadBox and drives the pins from it.
// All decisions are in lib/relay6_core/padbox.cpp; this file only moves data. Radio turn-taking: the pad box
// transmits only immediately after it has received a valid packet, so the two ends never talk over each other.
#include <Adafruit_ADS1X15.h>
#include <INA228.h>
#include <Adafruit_NeoPixel.h>
#include <Arduino.h>
#include <Wire.h>

#include "board.h"
#include "config.h"
#include "link.h"
#include "measure.h"
#include "padbox.h"

using namespace relay6;

namespace pins {
constexpr int kFire[cfg::kPads] = {2, 3, 4, 5, 6, 7};
constexpr int kArmEn = 26, kHeartbeat = 47, kSiren = 48, kBeacon = 33, kK1Sense = 41, kKeySense = 42;
}  // namespace pins

namespace {

constexpr float kRTest = 3300.0f;        // Rt1–Rt6, 0.1 %
constexpr float kShuntOhm = 0.0015f;     // 50 A / 75 mV
constexpr int kBeaconPixels = 16;

Adafruit_ADS1115 ads1, ads2;             // 0x48: TEST, PAD1–3; 0x49: PAD4–6, WIND
INA228 ina(0x40);
Adafruit_NeoPixel beacon(kBeaconPixels, pins::kBeacon, NEO_GRB + NEO_KHZ800);
LinkKeys keys;
PadBox* box = nullptr;
PadInputs in;
uint16_t offsetMilli[cfg::kPads] = {0};
uint32_t lastOhm = 0, lastSlow = 0, lastValid = 0;
bool hbLevel = false, haveAds = false, haveIna = false;
int16_t lastRssi = 0;
int8_t lastSnr = 0;

uint32_t hwRandom() { return esp_random(); }

float padVolts(Adafruit_ADS1115& a, int ch) {
  a.setGain(GAIN_SIXTEEN);                    // ±0.256 V: 7.8 µV per count
  int16_t raw = a.readADC_SingleEnded(ch);
  if (raw >= 32700) {                         // over range: open (or a high-resistance) igniter
    a.setGain(GAIN_ONE);                      // ±4.096 V
    raw = a.readADC_SingleEnded(ch);
  }
  return a.computeVolts(raw);
}

void readOhms(uint32_t now) {
  if (!haveAds) return;
  ads1.setGain(GAIN_ONE);
  const float vTest = ads1.computeVolts(ads1.readADC_SingleEnded(0));
  for (int i = 0; i < cfg::kPads; ++i) {
    const float v = i < 3 ? padVolts(ads1, i + 1) : padVolts(ads2, i - 3);
    in.ohm[i] = igniterOhms(vTest, v, kRTest, offsetMilli[i]);
  }
  in.ohmAt = now ? now : 1;
}

void readSlow() {
  if (haveAds) {
    ads2.setGain(GAIN_TWO);                   // ±2.048 V
    const float v = ads2.computeVolts(ads2.readADC_SingleEnded(3));
    // Adafruit 1733: 0.4 V = 0 m/s, 2.0 V = 32.4 m/s
    float ms = (v - 0.4f) * (32.4f / 1.6f);
    if (ms < 0) ms = 0;
    in.windDms = static_cast<uint16_t>(ms * 10.0f + 0.5f);
  }
  if (haveIna) in.battMv = static_cast<uint16_t>(ina.getBusVoltage() * 1000.0f + 0.5f);   // volts -> mV
}

void showBeacon(Beacon b, uint32_t now) {
  uint32_t c = 0;
  const bool blink = (now / 250) % 2;
  switch (b) {
    case Beacon::Off: c = 0; break;
    case Beacon::NoLink: c = blink ? beacon.Color(20, 20, 20) : 0; break;
    case Beacon::Safe: c = beacon.Color(0, 160, 0); break;
    case Beacon::Armed: c = beacon.Color(255, 110, 0); break;
    case Beacon::Firing: c = blink ? beacon.Color(255, 0, 0) : 0; break;
    case Beacon::Fault: c = blink ? beacon.Color(160, 0, 160) : beacon.Color(40, 0, 40); break;
  }
  beacon.fill(c);
  beacon.show();
}

void console() {
  const String line = r6link::readLine();
  if (!line.length()) return;
  if (r6link::console(line, keys)) return;
  if (line == "status" && box) {
    Serial.printf("state=%d reason=%s key=%d live=%d batt=%umV wind=%u.%u m/s\n", static_cast<int>(box->state()),
                  toString(box->lastReason()), in.keyArm, in.padLive, in.battMv, in.windDms / 10, in.windDms % 10);
    for (int i = 0; i < cfg::kPads; ++i)
      Serial.printf("  pad %d: %u mOhm (class %d, offset %u)\n", i + 1, in.ohm[i].milli, static_cast<int>(in.ohm[i].cls), offsetMilli[i]);
    return;
  }
  if (line.startsWith("offset ")) {  // offset <pad 1-6> <mOhm>: lead and contact resistance (Stage 5)
    const int sp = line.indexOf(' ', 7);
    const int pad = line.substring(7, sp).toInt();
    const int mo = line.substring(sp + 1).toInt();
    if (pad >= 1 && pad <= 6 && mo >= 0 && mo < 5000) {
      offsetMilli[pad - 1] = static_cast<uint16_t>(mo);
      char key[8];
      snprintf(key, sizeof key, "off%d", pad);
      r6link::putU16(key, offsetMilli[pad - 1]);
      Serial.printf("pad %d offset %d mOhm saved\n", pad, mo);
    }
    return;
  }
  Serial.println("commands: show | status | pair <key> <system> [bank] | offset <pad> <mOhm>");
}

}  // namespace

void setup() {
  // Outputs low before anything else: no gate, no arm.
  for (int p : pins::kFire) { digitalWrite(p, LOW); pinMode(p, OUTPUT); }
  digitalWrite(pins::kArmEn, LOW); pinMode(pins::kArmEn, OUTPUT);
  digitalWrite(pins::kSiren, LOW); pinMode(pins::kSiren, OUTPUT);
  pinMode(pins::kHeartbeat, OUTPUT);
  pinMode(pins::kK1Sense, INPUT);
  pinMode(pins::kKeySense, INPUT);
  pinMode(board::kVext, OUTPUT); digitalWrite(board::kVext, LOW);

  Serial.begin(115200);
  delay(300);
  Serial.println("\nRELAY-6 pad box, firmware Rev A");
  Wire.begin(board::kI2cSda, board::kI2cScl);
  haveAds = ads1.begin(0x48) && ads2.begin(0x49);
  haveIna = ina.begin();
  if (haveIna) ina.setMaxCurrentShunt(50.0f, kShuntOhm);
  Serial.printf("ADS1115 x2: %s   INA228: %s\n", haveAds ? "ok" : "MISSING", haveIna ? "ok" : "MISSING");
  beacon.begin();
  for (int i = 0; i < cfg::kPads; ++i) {
    char key[8];
    snprintf(key, sizeof key, "off%d", i + 1);
    offsetMilli[i] = r6link::getU16(key, 0);
  }
  if (!r6link::radioBegin()) Serial.println("RADIO FAILED: the pad box cannot arm without a link.");
  if (!r6link::loadKeys(keys)) {
    Serial.println("NOT PAIRED: will not arm. Use: pair <32 hex key> <8 hex system> [bank]");
    return;
  }
  box = new PadBox(keys, r6link::bootTxCounter(), r6link::bootRxFloor(), hwRandom);
  Serial.printf("paired, system %08lX bank %u\n", static_cast<unsigned long>(keys.system), keys.bank);
}

void loop() {
  const uint32_t now = millis();
  console();
  if (!box) {                                 // unpaired: everything stays off
    showBeacon(Beacon::Fault, now);
    delay(20);
    return;
  }

  in.now = now;
  in.keyArm = digitalRead(pins::kKeySense) == HIGH;
  in.padLive = digitalRead(pins::kK1Sense) == HIGH;
  in.rssi = lastRssi;
  in.snr = lastSnr;
  if (haveIna) in.amps = ina.getCurrent();            // amps
  if (now - lastSlow >= 500) { lastSlow = now; readSlow(); }
  if (box->state() == PadState::Safe && now - lastOhm >= 1000) { lastOhm = now; readOhms(now); }

  box->tick(in);
  const PadOutputs& o = box->out();
  for (int i = 0; i < cfg::kPads; ++i) digitalWrite(pins::kFire[i], (o.gates >> i) & 1 ? HIGH : LOW);
  digitalWrite(pins::kArmEn, o.armEn ? HIGH : LOW);
  digitalWrite(pins::kSiren, o.siren ? HIGH : LOW);
  if (o.validRx != lastValid) {               // feed the hardware watchdog U2 on every authenticated packet
    lastValid = o.validRx;
    hbLevel = !hbLevel;
    digitalWrite(pins::kHeartbeat, hbLevel ? HIGH : LOW);
  }
  showBeacon(o.beacon, now);

  r6link::Rx rx;
  if (r6link::receive(rx)) {
    lastRssi = rx.rssi;
    lastSnr = rx.snr;
    if (box->onPacket(rx.buf, rx.len) == OpenResult::Ok) {
      r6link::afterReceive(box->rxCounter());
      box->tick(in);                          // act on it now, then reply in our turn
      uint8_t out[kMaxPacket];
      size_t n;
      for (int k = 0; k < 2 && box->nextTx(out, n); ++k) {
        r6link::send(out, n);
        r6link::afterSend(box->txCounter());
      }
    }
  }
}
