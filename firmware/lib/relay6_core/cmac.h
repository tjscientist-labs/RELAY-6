// SPDX-License-Identifier: GPL-2.0-or-later
// AES-128-CMAC (RFC 4493 / NIST SP 800-38B) and a constant-time tag compare.
#pragma once
#include <cstddef>
#include <cstdint>

#include "aes128.h"

namespace relay6 {

class Cmac {
 public:
  explicit Cmac(const uint8_t key[16]);
  void setKey(const uint8_t key[16]);
  // Full 16-byte MAC of msg[0..len).
  void compute(const uint8_t* msg, size_t len, uint8_t mac[16]) const;

 private:
  Aes128 aes_;
  uint8_t k1_[16] = {0}, k2_[16] = {0};
};

// Compares n bytes without an early exit, so timing does not leak where a forged tag first differs.
bool tagEqual(const uint8_t* a, const uint8_t* b, size_t n);

}  // namespace relay6
