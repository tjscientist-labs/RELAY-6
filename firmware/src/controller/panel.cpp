// SPDX-License-Identifier: GPL-2.0-or-later
#include "panel.h"

#include <Adafruit_ADS1X15.h>
#include <Adafruit_MCP23X17.h>
#include <Adafruit_NeoPixel.h>
#include <Arduino.h>

#include "config.h"

using namespace relay6;

namespace panel {
namespace pins {
constexpr int kKey = 26, kFire = 42, kCover = 41, kEncA = 38, kEncB = 34, kLed = 19, kMcpInt = 20;
}

namespace {

#if defined(PANEL_HALO)
constexpr int kRing = 46, kPixels = cfg::kPads + kRing;
#elif defined(PANEL_FLIGHTDECK)
constexpr int kPixels = cfg::kPads * 8;
#else
constexpr int kLever = 8, kColumn = 8, kPixels = cfg::kPads * (kLever + kColumn) + 1;
#endif

Adafruit_NeoPixel px(kPixels, pins::kLed, NEO_GRB + NEO_KHZ800);
#if defined(PANEL_MONOLITH)
Adafruit_ADS1115 lev1, lev2;   // 0x48 levers 1–4, 0x49 levers 5–6
Adafruit_MCP23X17 mcp;         // MODE + encoder push
#else
Adafruit_MCP23X17 mcp;         // GPA0–5 pad keys/toggles, GPA6 MODE, GPA7 encoder push
#endif
uint8_t lastPads = 0;
bool lastMode = false;
int encState = 0, encAcc = 0;

void encoderPoll() {
  static const int8_t table[16] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};
  const int s = (digitalRead(pins::kEncA) << 1) | digitalRead(pins::kEncB);
  encAcc += table[(encState << 2) | s];
  encState = s;
}

uint32_t padColour(int i, const Controller& c, uint8_t selected) {
  const PadView& pv = c.pad();
  const bool sel = (selected >> i) & 1;
  const uint16_t mo = pv.ohmMilli[i];
  if (c.state() == CtlState::Counting || c.state() == CtlState::Firing) return sel ? px.Color(255, 0, 0) : 0;
  if (sel) return px.Color(255, 110, 0);                    // selected: amber
  if (mo == 0xFFFF) return px.Color(8, 8, 8);               // nothing connected
  if (mo < cfg::kOhmMinMilli || mo > cfg::kOhmMaxMilli) return px.Color(200, 0, 0);
  return px.Color(0, 140, 0);                               // continuity in the window
}

}  // namespace

const char* name() {
#if defined(PANEL_HALO)
  return "HALO";
#elif defined(PANEL_FLIGHTDECK)
  return "FLIGHTDECK";
#else
  return "MONOLITH";
#endif
}

bool selectionIsLevel() {
#if defined(PANEL_HALO)
  return false;
#else
  return true;
#endif
}

bool begin() {
  pinMode(pins::kKey, INPUT_PULLUP);
  pinMode(pins::kFire, INPUT_PULLUP);
  pinMode(pins::kCover, INPUT_PULLUP);
  pinMode(pins::kEncA, INPUT_PULLUP);
  pinMode(pins::kEncB, INPUT_PULLUP);
  px.begin();
  px.setBrightness(80);
  px.clear();
  px.show();
  bool ok = mcp.begin_I2C(0x20);
  if (ok) for (int i = 0; i < 8; ++i) mcp.pinMode(i, INPUT_PULLUP);
#if defined(PANEL_MONOLITH)
  ok = ok && lev1.begin(0x48) && lev2.begin(0x49);
  lev1.setGain(GAIN_ONE);
  lev2.setGain(GAIN_ONE);
#endif
  return ok;
}

void read(Read& r) {
  encoderPoll();
  r.keyOn = digitalRead(pins::kKey) == LOW;
  r.fireHeld = digitalRead(pins::kFire) == LOW;     // FLIGHTDECK: ARM and FIRE wired in series into this input
#if defined(PANEL_FLIGHTDECK)
  r.coverOk = true;                                  // the two-hand zone is the guard
#else
  r.coverOk = digitalRead(pins::kCover) == LOW;      // HALO cover lifted / MONOLITH collar at 90°
#endif
  const uint16_t gp = mcp.readGPIOAB();
  const uint8_t pads = static_cast<uint8_t>(~gp & 0x3F);
  const bool mode = !(gp & (1 << 6)) || !(gp & (1 << 7));
#if defined(PANEL_MONOLITH)
  uint8_t lv = 0;
  for (int i = 0; i < cfg::kPads; ++i) {
    const float v = i < 4 ? lev1.computeVolts(lev1.readADC_SingleEnded(i)) : lev2.computeVolts(lev2.readADC_SingleEnded(i - 4));
    if (v > 3.3f * 0.9f) lv |= static_cast<uint8_t>(1 << i);   // top 10 % of travel = committed
  }
  r.padsLevel = lv;
#else
  r.padsLevel = pads;
#endif
  r.padsPressed = static_cast<uint8_t>(pads & ~lastPads);
  lastPads = pads;
  r.modePressed = mode && !lastMode;
  lastMode = mode;
  r.encoderSteps = encAcc / 4;
  encAcc -= r.encoderSteps * 4;
}

void lights(uint32_t now, uint8_t selected, const Controller& c) {
  px.clear();
#if defined(PANEL_HALO)
  for (int i = 0; i < cfg::kPads; ++i) px.setPixelColor(i, padColour(i, c, selected));
  // Halo ring: cyan when linked, drains in amber during the count, red while firing.
  const int cd = c.countdown();
  for (int j = 0; j < kRing; ++j) {
    uint32_t col = c.linkUp() ? px.Color(0, 90, 120) : px.Color(10, 10, 10);
    if (c.state() == CtlState::Counting) {
      const float frac = (cfg::kCountdownMs - (cd > 0 ? (cd - 1) * 1000.0f : 0)) / cfg::kCountdownMs;
      if (j < kRing * frac) col = px.Color(255, 110, 0);
    }
    if (c.state() == CtlState::Firing) col = ((now / 120) % 2) ? px.Color(255, 0, 0) : 0;
    px.setPixelColor(cfg::kPads + j, col);
  }
#elif defined(PANEL_FLIGHTDECK)
  for (int i = 0; i < cfg::kPads; ++i)
    for (int k = 0; k < 8; ++k) px.setPixelColor(i * 8 + k, padColour(i, c, selected));
#else
  for (int i = 0; i < cfg::kPads; ++i) {
    const uint32_t col = padColour(i, c, selected);
    for (int k = 0; k < kLever; ++k) px.setPixelColor(i * (kLever + kColumn) + k, col);
    for (int k = 0; k < kColumn; ++k)                    // firing-order column: fills as its turn approaches
      px.setPixelColor(i * (kLever + kColumn) + kLever + k, ((selected >> i) & 1) && k < 2 + i ? px.Color(90, 120, 255) : 0);
  }
  px.setPixelColor(kPixels - 1, c.state() == CtlState::Counting ? px.Color(255, 255, 255) : px.Color(60, 80, 200));  // core
#endif
  px.show();
}

}  // namespace panel
