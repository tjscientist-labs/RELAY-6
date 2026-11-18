// SPDX-License-Identifier: GPL-2.0-or-later
#include "protocol.h"

#include <cstring>

namespace relay6 {

bool LinkKeys::paired() const {
  if (system == 0) return false;
  uint8_t any = 0;
  for (uint8_t b : key) any = static_cast<uint8_t>(any | b);
  return any != 0;
}

Sealer::Sealer(const LinkKeys& k, bool padBox, uint32_t firstCounter)
    : keys_(k), cmac_(k.key), padBox_(padBox), counter_(firstCounter) {}

size_t Sealer::seal(Msg type, const uint8_t* payload, size_t n, uint8_t* out) {
  if (n > kMaxPayload) return 0;
  put32(out, keys_.system);
  out[4] = keys_.bank;
  out[5] = static_cast<uint8_t>(static_cast<uint8_t>(type) | (padBox_ ? kFromPadBox : 0));
  put32(out + 6, counter_++);
  if (n) std::memcpy(out + kHeader, payload, n);
  uint8_t mac[16];
  cmac_.compute(out, kHeader + n, mac);
  std::memcpy(out + kHeader + n, mac, kTag);
  return kHeader + n + kTag;
}

Opener::Opener(const LinkKeys& k, bool expectFromPadBox, uint32_t lastAccepted)
    : keys_(k), cmac_(k.key), fromPadBox_(expectFromPadBox), last_(lastAccepted) {}

OpenResult Opener::open(const uint8_t* pkt, size_t len, Header& h, const uint8_t*& payload, size_t& n) {
  if (len < kHeader + kTag || len > kMaxPacket) return OpenResult::TooShort;
  h.system = get32(pkt);
  h.bank = pkt[4];
  h.type = pkt[5];
  h.counter = get32(pkt + 6);
  if (h.system != keys_.system || h.bank != keys_.bank) return OpenResult::WrongSystem;
  if (((h.type & kFromPadBox) != 0) != fromPadBox_) return OpenResult::WrongDirection;
  n = len - kHeader - kTag;
  uint8_t mac[16];
  cmac_.compute(pkt, kHeader + n, mac);
  if (!tagEqual(mac, pkt + kHeader + n, kTag)) return OpenResult::BadTag;
  if (h.counter <= last_) return OpenResult::Replay;  // only after the tag is proven
  last_ = h.counter;
  payload = pkt + kHeader;
  h.type = static_cast<uint8_t>(h.type & ~kFromPadBox);
  return OpenResult::Ok;
}

const char* toString(OpenResult r) {
  switch (r) {
    case OpenResult::Ok: return "ok";
    case OpenResult::TooShort: return "length";
    case OpenResult::WrongSystem: return "system";
    case OpenResult::WrongDirection: return "direction";
    case OpenResult::BadTag: return "tag";
    case OpenResult::Replay: return "replay";
  }
  return "?";
}

const char* toString(Reason r) {
  static const char* names[] = {"none", "operator", "link lost", "pad key off", "ohm reading stale", "ohm out of window",
                                "wind", "battery", "nonce", "timeout", "fault", "done", "bad request"};
  const auto i = static_cast<uint8_t>(r);
  return i < sizeof(names) / sizeof(names[0]) ? names[i] : "?";
}

const char* toString(Mode m) {
  static const char* names[] = {"SINGLE", "SELECT", "SALVO", "RIPPLE", "DRAG"};
  const auto i = static_cast<uint8_t>(m);
  return i < 5 ? names[i] : "?";
}

}  // namespace relay6
