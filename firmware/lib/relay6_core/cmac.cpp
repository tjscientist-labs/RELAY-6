// SPDX-License-Identifier: GPL-2.0-only
#include "cmac.h"

#include <cstring>

namespace relay6 {
namespace {

void leftShift1(const uint8_t in[16], uint8_t out[16]) {
  uint8_t carry = 0;
  for (int i = 15; i >= 0; --i) {
    out[i] = static_cast<uint8_t>((in[i] << 1) | carry);
    carry = static_cast<uint8_t>((in[i] & 0x80) ? 1 : 0);
  }
}

void subkey(const uint8_t in[16], uint8_t out[16]) {
  leftShift1(in, out);
  if (in[0] & 0x80) out[15] ^= 0x87;
}

}  // namespace

Cmac::Cmac(const uint8_t key[16]) { setKey(key); }

void Cmac::setKey(const uint8_t key[16]) {
  aes_.setKey(key);
  uint8_t zero[16] = {0}, l[16];
  aes_.encryptBlock(zero, l);
  subkey(l, k1_);
  subkey(k1_, k2_);
}

void Cmac::compute(const uint8_t* msg, size_t len, uint8_t mac[16]) const {
  const size_t n = (len + 15) / 16;  // number of blocks, at least 1
  const size_t blocks = n == 0 ? 1 : n;
  const bool complete = len != 0 && (len % 16) == 0;
  uint8_t x[16] = {0}, y[16];
  for (size_t b = 0; b + 1 < blocks; ++b) {
    for (int i = 0; i < 16; ++i) y[i] = static_cast<uint8_t>(x[i] ^ msg[b * 16 + i]);
    aes_.encryptBlock(y, x);
  }
  uint8_t last[16] = {0};
  const size_t off = (blocks - 1) * 16;
  const size_t rem = len - off;
  if (complete) {
    for (int i = 0; i < 16; ++i) last[i] = static_cast<uint8_t>(msg[off + i] ^ k1_[i]);
  } else {
    std::memcpy(last, msg + off, rem);
    last[rem] = 0x80;
    for (int i = 0; i < 16; ++i) last[i] ^= k2_[i];
  }
  for (int i = 0; i < 16; ++i) y[i] = static_cast<uint8_t>(x[i] ^ last[i]);
  aes_.encryptBlock(y, mac);
}

bool tagEqual(const uint8_t* a, const uint8_t* b, size_t n) {
  uint8_t diff = 0;
  for (size_t i = 0; i < n; ++i) diff = static_cast<uint8_t>(diff | (a[i] ^ b[i]));
  return diff == 0;
}

}  // namespace relay6
