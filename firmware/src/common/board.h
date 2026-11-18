// SPDX-License-Identifier: GPL-2.0-only
// Heltec WiFi LoRa 32 V3 pins and radio settings. Proposed map: check every row against Heltec's current V3
// pinout before soldering (build guide Stage 2 and section 11). Pins the board itself uses are left alone:
// SX1262 on 8–14, on-board OLED 17/18/21, Vext 36, LED 35, PRG 0, USB-serial 43/44, battery sense 1/37.
#pragma once
#include <cstdint>

namespace board {

// SX1262 (on the module)
constexpr int kLoraNss = 8, kLoraSck = 9, kLoraMosi = 10, kLoraMiso = 11, kLoraRst = 12, kLoraBusy = 13, kLoraDio1 = 14;
constexpr float kTcxoVolts = 1.8f;   // Heltec V3 radio runs from a TCXO on DIO3
constexpr int kI2cSda = 17, kI2cScl = 18;
constexpr int kVext = 36;            // LOW = on-board OLED/Vext powered

// Radio. One fixed channel; 500 kHz bandwidth so the signal meets FCC 15.247's ≥ 500 kHz rule for a
// non-hopping digital-modulation system in 902–928 MHz (check current rules for your country and use).
#if defined(RELAY6_REGION_EU868)
constexpr float kFreqMHz = 869.525f, kBwKHz = 250.0f;
constexpr int kPowerDbm = 14;
#else
constexpr float kFreqMHz = 915.0f, kBwKHz = 500.0f;
constexpr int kPowerDbm = 14;
#endif
constexpr int kSf = 8, kCr = 5;      // ≈ 40 ms for a full 42-byte packet
constexpr uint8_t kSyncWord = 0x12;  // private LoRa network

}  // namespace board
