// SPDX-License-Identifier: GPL-2.0-only
// Controller logic, shared by HALO, FLIGHTDECK and MONOLITH (they differ only in how the panel is read).
// Arming happens only while FIRE is held: hold FIRE -> ARM_REQ -> CHALLENGE -> ARM -> ARMED -> 5 s count
// -> FIRE -> FIRED. Releasing FIRE (or the key, or the cover) at any point sends SAFE.
#pragma once
#include <cstddef>
#include <cstdint>

#include "config.h"
#include "padbox.h"
#include "protocol.h"

namespace relay6 {

enum class CtlState : uint8_t { NoLink, Ready, Requesting, Arming, Counting, Firing, Done, Aborted };

struct CtlInputs {
  uint32_t now = 0;
  bool keyOn = false;
  bool fireHeld = false;    // FLIGHTDECK: ARM and FIRE in series
  bool coverOk = true;      // HALO cover open / MONOLITH collar turned; true where there is none
  uint8_t pads = 0;
  Mode mode = Mode::Single;
  uint16_t rippleMs = 1000;
};

struct PadView {               // what the pad box last told us
  PadState state = PadState::Safe;
  Reason reason = Reason::None;
  bool keyArm = false, padLive = false;
  uint16_t ohmMilli[cfg::kPads] = {0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF};
  bool ohmFresh = false;
  uint16_t battMv = 0, windDms = 0;
  int16_t rssi = 0;
  int8_t snr = 0;
  uint16_t fired[cfg::kPads] = {0};
  bool firedValid = false;
};

class Controller {
 public:
  Controller(const LinkKeys& keys, uint32_t firstTxCounter, uint32_t lastRxCounter);
  void tick(const CtlInputs& in);
  OpenResult onPacket(const uint8_t* pkt, size_t len);
  bool nextTx(uint8_t* out, size_t& len);

  CtlState state() const { return state_; }
  Reason reason() const { return reason_; }
  const PadView& pad() const { return pv_; }
  bool linkUp() const;
  int countdown() const;              // 5..1 while counting, else 0
  uint32_t txCounter() const { return seal_.counter(); }
  uint32_t rxCounter() const { return open_.lastAccepted(); }

 private:
  void queue(Msg m, const uint8_t* p, size_t n);
  void abort(Reason r, bool tellPad);
  void sendArmReq();
  void sendArm();
  void sendFire();

  Sealer seal_;
  Opener open_;
  CtlInputs in_{};
  PadView pv_{};
  CtlState state_ = CtlState::NoLink;
  Reason reason_ = Reason::None;
  uint32_t stateAt_ = 0, lastRx_ = 0, lastHb_ = 0, lastSend_ = 0;
  uint8_t nonce_[8] = {0};
  uint8_t pads_ = 0;
  Mode mode_ = Mode::Single;
  uint16_t step_ = 0;

  uint8_t txq_[4][kMaxPacket];
  size_t txlen_[4] = {0};
  uint8_t txHead_ = 0, txCount_ = 0;
};

}  // namespace relay6
