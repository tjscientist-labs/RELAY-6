// SPDX-License-Identifier: GPL-2.0-or-later
// Igniter resistance from the two ADS1115 readings, and the ignition timer from the shunt current.
#pragma once
#include <cstdint>

#include "config.h"

namespace relay6 {

enum class OhmClass : uint8_t { Empty, Open, Short, Ok, OutOfWindow };

struct OhmReading {
  uint16_t milli = 0xFFFF;   // 0xFFFF = open / no reading
  OhmClass cls = OhmClass::Empty;
};

// vTest: TEST rail (V); vPad: PAD-n (V); rTest: the 3.30 kΩ resistor (Ω); offsetMilli: lead/contact
// offset stored at calibration. Returns the igniter resistance; OPEN when vPad is within openFrac of vTest.
OhmReading igniterOhms(float vTest, float vPad, float rTest, uint16_t offsetMilli, uint16_t minMilli = cfg::kOhmMinMilli,
                       uint16_t maxMilli = cfg::kOhmMaxMilli, float openFrac = 0.9f);

// One firing step = a set of pads switched on together (salvo: one step; ripple: one per pad).
class IgnitionTimer {
 public:
  void start(uint32_t nowMs);
  void sample(uint32_t nowMs, float amps);
  bool lit() const { return litAt_ != 0; }
  uint16_t litMs() const { return litAt_ ? static_cast<uint16_t>(litAt_ - start_) : 0xFFFF; }  // 0xFFFF = NO FIRE
  float peak() const { return peak_; }

 private:
  uint32_t start_ = 0, litAt_ = 0;
  float peak_ = 0;
  bool rose_ = false;
};

}  // namespace relay6
