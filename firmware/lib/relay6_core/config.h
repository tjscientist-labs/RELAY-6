// SPDX-License-Identifier: GPL-2.0-only
// Timing and limits. The build guide's section 11 ("Timing and limits") lists the same values; change both together.
#pragma once
#include <cstdint>

namespace relay6 {
namespace cfg {

constexpr uint32_t kHeartbeatMs = 250;        // both directions
constexpr uint32_t kLinkLossMs = 1000;        // no valid packet for this long -> SAFE (hardware watchdog U2 ≈ 1 s too)
constexpr uint32_t kStatusMs = 1000;          // pad box STATUS period
constexpr uint32_t kNonceLifeMs = 30000;      // CHALLENGE valid for
constexpr uint32_t kArmedMaxMs = 60000;       // ARMED without FIRE for this long -> SAFE
constexpr uint32_t kOhmMaxAgeMs = 10000;      // a reading older than this cannot arm
constexpr uint16_t kOhmMinMilli = 300;        // default window per pad, mΩ
constexpr uint16_t kOhmMaxMilli = 5000;
constexpr uint16_t kOhmShortMilli = 200;
constexpr uint32_t kFirePulseMs = 1000;       // per pad
constexpr uint32_t kRippleMinMs = 250, kRippleMaxMs = 5000;
constexpr uint32_t kDoneHoldMs = 2000;        // after the last pulse, then SAFE
constexpr uint32_t kCountdownMs = 5000;       // controller count, FIRE held throughout
constexpr uint32_t kRetryMs = 300;            // controller resend for ARM_REQ / ARM / FIRE
constexpr uint16_t kWindLimitDms = 89;        // 20 mph gust = 8.9 m/s, in 0.1 m/s
constexpr uint16_t kBattLowMv = 11800;        // warning (SLA at rest)
constexpr uint16_t kBattCutMv = 10500;        // refuse to arm
constexpr uint32_t kK1StuckMs = 200;          // PAD+ live while ARM_EN low for this long -> FAULT
constexpr uint32_t kK1PullInMs = 300;         // ARM_EN high but PAD+ not live after this -> SAFE (key/relay)
constexpr float kIgniteRiseA = 0.3f;          // current above this = an igniter is conducting
constexpr float kIgniteDropFrac = 0.3f;       // falls below this fraction of the step's peak = burnt through
constexpr uint8_t kPads = 6;

}  // namespace cfg
}  // namespace relay6
