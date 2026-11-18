// SPDX-License-Identifier: GPL-2.0-only
#include "measure.h"

namespace relay6 {

OhmReading igniterOhms(float vTest, float vPad, float rTest, uint16_t offsetMilli, uint16_t minMilli, uint16_t maxMilli,
                       float openFrac) {
  OhmReading r;
  if (vTest < 0.5f) return r;                       // no TEST rail: nothing measured
  if (vPad >= vTest * openFrac) {                   // no path through the igniter
    r.cls = OhmClass::Open;
    return r;
  }
  const float i = (vTest - vPad) / rTest;           // amps through Rt and the igniter
  float ohms = vPad / i;
  float milli = ohms * 1000.0f - static_cast<float>(offsetMilli);
  if (milli < 0) milli = 0;
  r.milli = milli > 65000.0f ? 65000 : static_cast<uint16_t>(milli + 0.5f);
  if (r.milli < cfg::kOhmShortMilli) r.cls = OhmClass::Short;
  else if (r.milli < minMilli || r.milli > maxMilli) r.cls = OhmClass::OutOfWindow;
  else r.cls = OhmClass::Ok;
  return r;
}

void IgnitionTimer::start(uint32_t nowMs) {
  start_ = nowMs ? nowMs : 1;
  litAt_ = 0;
  peak_ = 0;
  rose_ = false;
}

void IgnitionTimer::sample(uint32_t nowMs, float amps) {
  if (litAt_) return;
  if (amps > peak_) peak_ = amps;
  if (!rose_) {
    if (amps > cfg::kIgniteRiseA) rose_ = true;
    return;
  }
  if (amps < peak_ * cfg::kIgniteDropFrac) litAt_ = nowMs ? nowMs : 1;
}

}  // namespace relay6
