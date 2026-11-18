// SPDX-License-Identifier: GPL-2.0-only
// Controller application (HALO / FLIGHTDECK / MONOLITH, chosen at build time). Reads the panel into
// relay6::Controller, draws the OLED screens from the concept sheet, beeps the count, and moves packets.
#include <Arduino.h>
#include <SPI.h>
#include <U8g2lib.h>
#include <Wire.h>
#include <driver/i2s.h>

#include "board.h"
#include "config.h"
#include "controller.h"
#include "link.h"
#include "panel.h"

using namespace relay6;

namespace pins {
constexpr int kOledSck = 5, kOledMosi = 6, kOledCs = 7, kOledDc = 4, kOledRst = 3, kOled2Cs = 2;
constexpr int kI2sBclk = 47, kI2sLrc = 48, kI2sDout = 33;
}  // namespace pins

namespace {

U8G2_SSD1322_NHD_256X64_F_4W_HW_SPI oled(U8G2_R0, pins::kOledCs, pins::kOledDc, pins::kOledRst);
#if defined(PANEL_MONOLITH)
U8G2_SSD1322_NHD_256X64_F_4W_HW_SPI oled2(U8G2_R0, pins::kOled2Cs, pins::kOledDc, U8X8_PIN_NONE);
#endif
LinkKeys keys;
Controller* ctl = nullptr;
CtlInputs in;
uint8_t selected = 0;
uint16_t rippleMs = 1000;
uint32_t lastDraw = 0;
int lastCount = 0;
bool audioOk = false;

// ---- audio: short beeps for the count (voice clips are an open item)
void audioBegin() {
  i2s_config_t cfg = {};
  cfg.mode = static_cast<i2s_mode_t>(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = 16000;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.dma_buf_count = 4;
  cfg.dma_buf_len = 256;
  i2s_pin_config_t pc = {};
  pc.bck_io_num = pins::kI2sBclk;
  pc.ws_io_num = pins::kI2sLrc;
  pc.data_out_num = pins::kI2sDout;
  pc.data_in_num = I2S_PIN_NO_CHANGE;
  audioOk = i2s_driver_install(I2S_NUM_0, &cfg, 0, nullptr) == ESP_OK && i2s_set_pin(I2S_NUM_0, &pc) == ESP_OK;
}

void beep(int hz, int ms) {
  if (!audioOk) return;
  static int16_t buf[256];
  const int total = 16000 * ms / 1000;
  const int half = 16000 / (2 * hz);
  for (int done = 0; done < total;) {
    const int n = total - done < 256 ? total - done : 256;
    for (int i = 0; i < n; ++i) buf[i] = ((done + i) / half) % 2 ? 6000 : -6000;
    size_t w;
    i2s_write(I2S_NUM_0, buf, n * 2, &w, 20);
    done += n;
  }
}

// ---- screens (concept sheet "One flight, six screens")
void drawPads(U8G2& d) {
  const PadView& pv = ctl->pad();
  d.setFont(u8g2_font_6x12_tf);
  d.drawStr(0, 10, "PADS");
  char w[24];
  snprintf(w, sizeof w, "WIND %u.%u m/s", pv.windDms / 10, pv.windDms % 10);
  d.drawStr(150, 10, w);
  for (int i = 0; i < cfg::kPads; ++i) {
    const int x = i * 42;
    const bool sel = (selected >> i) & 1;
    if (sel) d.drawBox(x, 18, 40, 30); else d.drawFrame(x, 18, 40, 30);
    d.setDrawColor(sel ? 0 : 1);
    char t[12];
    snprintf(t, sizeof t, "%d", i + 1);
    d.drawStr(x + 17, 30, t);
    if (pv.ohmMilli[i] == 0xFFFF) snprintf(t, sizeof t, "OPEN");
    else snprintf(t, sizeof t, "%u.%02u", pv.ohmMilli[i] / 1000, (pv.ohmMilli[i] % 1000) / 10);
    d.drawStr(x + 4, 44, t);
    d.setDrawColor(1);
  }
  snprintf(w, sizeof w, "%s %s%s", toString(in.mode), in.mode == Mode::Ripple ? "" : "",
           pv.ohmFresh ? "" : "  (ohms stale)");
  d.drawStr(0, 62, w);
  if (in.mode == Mode::Ripple) {
    snprintf(w, sizeof w, "STEP %u.%02u s", rippleMs / 1000, (rippleMs % 1000) / 10);
    d.drawStr(90, 62, w);
  }
  snprintf(w, sizeof w, "%d dBm %ddB", pv.rssi, pv.snr);
  d.drawStr(170, 62, w);
}

void drawScreen() {
  U8G2& d = oled;
  d.clearBuffer();
  d.setFont(u8g2_font_6x12_tf);
  char t[40];
  switch (ctl->state()) {
    case CtlState::NoLink:
      d.drawStr(0, 10, "LINK");
      d.setFont(u8g2_font_logisoso16_tr);
      d.drawStr(0, 40, "SEARCHING...");
      d.setFont(u8g2_font_6x12_tf);
      snprintf(t, sizeof t, "SYSTEM %08lX  BANK %u", static_cast<unsigned long>(keys.system), keys.bank);
      d.drawStr(0, 62, t);
      break;
    case CtlState::Ready:
    case CtlState::Requesting:
    case CtlState::Arming:
      drawPads(d);
      if (ctl->state() != CtlState::Ready) d.drawStr(200, 10, "ARMING");
      break;
    case CtlState::Counting:
      d.drawStr(0, 12, "ARMED - HOLD FIRE");
      d.setFont(u8g2_font_logisoso42_tn);
      snprintf(t, sizeof t, "%d", ctl->countdown());
      d.drawStr(190, 60, t);
      break;
    case CtlState::Firing:
      d.setFont(u8g2_font_logisoso16_tr);
      d.drawStr(0, 40, "FIRING");
      break;
    case CtlState::Done: {
      d.drawStr(0, 10, "LIFTOFF");
      const PadView& pv = ctl->pad();
      int k = 0;
      for (int i = 0; i < cfg::kPads; ++i)
        if (pv.firedValid && pv.fired[i]) {
          if (pv.fired[i] == 0xFFFF) snprintf(t, sizeof t, "P%d NO FIRE", i + 1);
          else snprintf(t, sizeof t, "P%d %ums", i + 1, pv.fired[i]);
          d.drawStr((k % 3) * 85, 28 + (k / 3) * 14, t);
          ++k;
        }
      d.drawStr(0, 62, pv.firedValid ? "PAD BOX SAFED - release FIRE" : "waiting for report...");
      break;
    }
    case CtlState::Aborted:
      d.drawStr(0, 10, "LOCKOUT");
      d.setFont(u8g2_font_logisoso16_tr);
      d.drawStr(0, 40, toString(ctl->reason()));
      d.setFont(u8g2_font_6x12_tf);
      d.drawStr(0, 62, "release FIRE to reset");
      break;
  }
  d.sendBuffer();
#if defined(PANEL_MONOLITH)
  oled2.clearBuffer();
  oled2.setFont(u8g2_font_6x12_tf);
  snprintf(t, sizeof t, "MONOLITH // %s", toString(in.mode));
  oled2.drawStr(0, 12, t);
  snprintf(t, sizeof t, "BATT %u.%02u V", ctl->pad().battMv / 1000, (ctl->pad().battMv % 1000) / 10);
  oled2.drawStr(0, 40, t);
  oled2.sendBuffer();
#endif
}

void console() {
  const String line = r6link::readLine();
  if (!line.length()) return;
  if (r6link::console(line, keys)) return;
  Serial.println("commands: show | pair <32 hex key> <8 hex system> [bank]");
}

}  // namespace

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.printf("\nRELAY-6 controller (%s), firmware Rev A\n", panel::name());
  pinMode(board::kVext, OUTPUT);
  digitalWrite(board::kVext, LOW);
  Wire.begin(board::kI2cSda, board::kI2cScl);
  SPI.begin(pins::kOledSck, -1, pins::kOledMosi, pins::kOledCs);   // OLED bus (the radio has its own SPI host)
  oled.begin();
#if defined(PANEL_MONOLITH)
  oled2.begin();
#endif
  audioBegin();
  if (!panel::begin()) Serial.println("panel chip missing (MCP23017 / ADS1115)");
  if (!r6link::radioBegin()) Serial.println("RADIO FAILED");
  if (!r6link::loadKeys(keys)) {
    Serial.println("NOT PAIRED. Use: pair <32 hex key> <8 hex system> [bank]");
    return;
  }
  ctl = new Controller(keys, r6link::bootTxCounter(), r6link::bootRxFloor());
  rippleMs = r6link::getU16("ripple", 1000);
}

void loop() {
  const uint32_t now = millis();
  console();
  if (!ctl) {
    if (now - lastDraw > 500) {
      lastDraw = now;
      oled.clearBuffer();
      oled.setFont(u8g2_font_6x12_tf);
      oled.drawStr(0, 30, "NOT PAIRED - see serial console");
      oled.sendBuffer();
    }
    return;
  }

  panel::Read r;
  panel::read(r);
  const bool idle = ctl->state() == CtlState::Ready || ctl->state() == CtlState::NoLink;
  if (idle) {                                     // selection and mode can change only when nothing is in progress
    if (panel::selectionIsLevel()) selected = r.padsLevel;
    else if (r.padsPressed) selected = in.mode == Mode::Single ? r.padsPressed & static_cast<uint8_t>(-r.padsPressed)
                                                                : static_cast<uint8_t>(selected ^ r.padsPressed);
    if (r.encoderSteps) {
      if (r.modePressed || in.mode == Mode::Ripple) {
        int ms = rippleMs + r.encoderSteps * 250;
        if (ms < static_cast<int>(cfg::kRippleMinMs)) ms = cfg::kRippleMinMs;
        if (ms > static_cast<int>(cfg::kRippleMaxMs)) ms = cfg::kRippleMaxMs;
        rippleMs = static_cast<uint16_t>(ms);
        r6link::putU16("ripple", rippleMs);
      }
    }
    if (r.modePressed) in.mode = static_cast<Mode>((static_cast<int>(in.mode) + 1) % 5);
    if (in.mode == Mode::Salvo) selected = 0x3F;
  }
  in.now = now;
  in.keyOn = r.keyOn;
  in.fireHeld = r.fireHeld;
  in.coverOk = r.coverOk;
  in.pads = selected;
  in.rippleMs = rippleMs;

  ctl->tick(in);
  uint8_t out[kMaxPacket];
  size_t n;
  bool sent = false;
  while (ctl->nextTx(out, n)) {
    r6link::send(out, n);
    r6link::afterSend(ctl->txCounter());
    sent = true;
  }
  (void)sent;
  r6link::Rx rx;
  if (r6link::receive(rx) && ctl->onPacket(rx.buf, rx.len) == OpenResult::Ok) r6link::afterReceive(ctl->rxCounter());

  const int cd = ctl->countdown();
  if (cd != lastCount) {
    if (cd > 0) beep(880, 120);
    else if (lastCount == 1) beep(1760, 400);
    lastCount = cd;
  }
  if (now - lastDraw >= 100) {
    lastDraw = now;
    drawScreen();
    panel::lights(now, selected, *ctl);
  }
}
