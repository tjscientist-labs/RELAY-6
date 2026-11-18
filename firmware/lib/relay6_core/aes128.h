// SPDX-License-Identifier: GPL-2.0-only
// AES-128 block encryption (FIPS-197), encrypt direction only — all CMAC needs.
// Portable C++, no platform code. On the ESP32-S3 the hardware AES could replace it later;
// this version is used on every target so the host tests check the exact code that ships.
#pragma once
#include <cstdint>

namespace relay6 {

class Aes128 {
 public:
  explicit Aes128(const uint8_t key[16]) { setKey(key); }
  Aes128() = default;
  void setKey(const uint8_t key[16]);
  void encryptBlock(const uint8_t in[16], uint8_t out[16]) const;

 private:
  uint8_t rk_[176] = {0};  // 11 round keys
};

}  // namespace relay6
