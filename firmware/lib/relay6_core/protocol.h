// SPDX-License-Identifier: GPL-2.0-or-later
// RELAY-6 link protocol: packet layout, message types, sealing (CMAC) and opening (verify + replay check).
//
//   offset  size  field
//   0       4     system ID (random, written at pairing)
//   4       1     bank (1..99)
//   5       1     type (bit 7 = sent by the pad box)
//   6       4     sender counter, big-endian, strictly increasing
//   10      n     payload (0..kMaxPayload)
//   10+n    8     tag = first 8 bytes of AES-128-CMAC(key, bytes 0 .. 10+n-1)
//   (the LoRa radio adds and checks its own CRC-16)
//
// The direction bit is inside the MAC, so a packet cannot be reflected back at its sender.
#pragma once
#include <cstddef>
#include <cstdint>

#include "cmac.h"

namespace relay6 {

constexpr size_t kHeader = 10;
constexpr size_t kTag = 8;
constexpr size_t kMaxPayload = 24;
constexpr size_t kMaxPacket = kHeader + kMaxPayload + kTag;
constexpr uint8_t kFromPadBox = 0x80;

enum class Msg : uint8_t {
  Heartbeat = 0x01,
  Status = 0x02,
  Select = 0x10,
  ArmReq = 0x11,
  Challenge = 0x12,
  Arm = 0x13,
  Armed = 0x14,
  Fire = 0x20,
  Fired = 0x21,
  Safe = 0x30,
};

enum class Mode : uint8_t { Single = 0, Select = 1, Salvo = 2, Ripple = 3, Drag = 4 };

enum class Reason : uint8_t {
  None = 0,
  Operator = 1,      // controller asked (FIRE released, key off, E-STOP path)
  LinkLost = 2,
  KeyOff = 3,        // pad box key in SAFE
  OhmStale = 4,
  OhmWindow = 5,
  Wind = 6,
  Battery = 7,
  NonceBad = 8,
  Timeout = 9,
  Fault = 10,
  Done = 11,         // firing sequence finished
  BadRequest = 12,
};

struct Header {
  uint32_t system = 0;
  uint8_t bank = 1;
  uint8_t type = 0;  // includes kFromPadBox
  uint32_t counter = 0;
};

// Shared secrets and identity, set at pairing.
struct LinkKeys {
  uint8_t key[16] = {0};
  uint32_t system = 0;
  uint8_t bank = 1;
  bool paired() const;
};

// Seals outgoing packets: fills header, counter, tag.
class Sealer {
 public:
  Sealer(const LinkKeys& k, bool padBox, uint32_t firstCounter);
  // Returns the packet length written to out (kMaxPacket bytes available), or 0 if payload too long.
  size_t seal(Msg type, const uint8_t* payload, size_t n, uint8_t* out);
  uint32_t counter() const { return counter_; }

 private:
  LinkKeys keys_;
  Cmac cmac_;
  bool padBox_;
  uint32_t counter_;
};

enum class OpenResult : uint8_t { Ok, TooShort, WrongSystem, WrongDirection, BadTag, Replay };

// Opens incoming packets from the peer: checks system, direction, tag, then counter > last accepted.
class Opener {
 public:
  Opener(const LinkKeys& k, bool expectFromPadBox, uint32_t lastAccepted);
  OpenResult open(const uint8_t* pkt, size_t len, Header& h, const uint8_t*& payload, size_t& n);
  uint32_t lastAccepted() const { return last_; }

 private:
  LinkKeys keys_;
  Cmac cmac_;
  bool fromPadBox_;
  uint32_t last_;
};

const char* toString(OpenResult r);
const char* toString(Reason r);
const char* toString(Mode m);

// Counter reservation: persist a block boundary, not every packet. On boot, counters restart at the
// stored boundary, so they still increase across power cycles; the store is rewritten once per block.
struct CounterBlock {
  static constexpr uint32_t kBlock = 1024;
  // Given the stored boundary, the first counter to use and the new boundary to store before using it.
  static void onBoot(uint32_t stored, uint32_t& first, uint32_t& newStored) {
    first = stored + 1;
    newStored = stored + kBlock;
  }
  // Call after each send; true when the boundary must be advanced (store newStored first).
  static bool needAdvance(uint32_t counter, uint32_t stored, uint32_t& newStored) {
    if (counter + 1 < stored) return false;
    newStored = stored + kBlock;
    return true;
  }
};

inline void put32(uint8_t* p, uint32_t v) {
  p[0] = static_cast<uint8_t>(v >> 24); p[1] = static_cast<uint8_t>(v >> 16);
  p[2] = static_cast<uint8_t>(v >> 8); p[3] = static_cast<uint8_t>(v);
}
inline uint32_t get32(const uint8_t* p) {
  return (static_cast<uint32_t>(p[0]) << 24) | (static_cast<uint32_t>(p[1]) << 16) |
         (static_cast<uint32_t>(p[2]) << 8) | p[3];
}
inline void put16(uint8_t* p, uint16_t v) { p[0] = static_cast<uint8_t>(v >> 8); p[1] = static_cast<uint8_t>(v); }
inline uint16_t get16(const uint8_t* p) { return static_cast<uint16_t>((p[0] << 8) | p[1]); }

}  // namespace relay6
