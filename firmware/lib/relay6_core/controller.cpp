// SPDX-License-Identifier: GPL-2.0-only
#include "controller.h"

#include <cstring>

namespace relay6 {

Controller::Controller(const LinkKeys& keys, uint32_t firstTxCounter, uint32_t lastRxCounter)
    : seal_(keys, false, firstTxCounter), open_(keys, true, lastRxCounter) {}

bool Controller::linkUp() const { return lastRx_ != 0 && in_.now - lastRx_ < cfg::kLinkLossMs; }

int Controller::countdown() const {
  if (state_ != CtlState::Counting) return 0;
  const uint32_t left = cfg::kCountdownMs - (in_.now - stateAt_);
  return static_cast<int>((left + 999) / 1000);
}

void Controller::queue(Msg m, const uint8_t* p, size_t n) {
  if (txCount_ == 4) { txHead_ = static_cast<uint8_t>((txHead_ + 1) % 4); --txCount_; }
  const uint8_t slot = static_cast<uint8_t>((txHead_ + txCount_) % 4);
  txlen_[slot] = seal_.seal(m, p, n, txq_[slot]);
  ++txCount_;
  lastSend_ = in_.now;
}

bool Controller::nextTx(uint8_t* out, size_t& len) {
  if (!txCount_) return false;
  len = txlen_[txHead_];
  std::memcpy(out, txq_[txHead_], len);
  txHead_ = static_cast<uint8_t>((txHead_ + 1) % 4);
  --txCount_;
  return true;
}

void Controller::abort(Reason r, bool tellPad) {
  if (tellPad) {
    const uint8_t p[1] = {static_cast<uint8_t>(r)};
    queue(Msg::Safe, p, 1);
  }
  std::memset(nonce_, 0, sizeof nonce_);
  reason_ = r;
  state_ = CtlState::Aborted;
  stateAt_ = in_.now;
}

void Controller::sendArmReq() {
  uint8_t p[4] = {pads_, static_cast<uint8_t>(mode_), 0, 0};
  put16(p + 2, step_);
  queue(Msg::ArmReq, p, 4);
}

void Controller::sendArm() {
  uint8_t p[16] = {pads_, static_cast<uint8_t>(mode_)};
  put16(p + 2, step_);
  std::memcpy(p + 4, nonce_, 8);
  put32(p + 12, 0);  // RSO card ID: filled by the application when NFC is fitted (logged by the pad box)
  queue(Msg::Arm, p, 16);
}

void Controller::sendFire() {
  uint8_t p[12] = {pads_, static_cast<uint8_t>(mode_)};
  put16(p + 2, step_);
  std::memcpy(p + 4, nonce_, 8);
  queue(Msg::Fire, p, 12);
}

OpenResult Controller::onPacket(const uint8_t* pkt, size_t len) {
  Header h;
  const uint8_t* p = nullptr;
  size_t n = 0;
  const OpenResult r = open_.open(pkt, len, h, p, n);
  if (r != OpenResult::Ok) return r;
  lastRx_ = in_.now ? in_.now : 1;
  switch (static_cast<Msg>(h.type)) {
    case Msg::Heartbeat:
      if (n >= 4) {
        pv_.state = static_cast<PadState>(p[0]);
        pv_.reason = static_cast<Reason>(p[1]);
        pv_.keyArm = p[2] & 1;
        pv_.padLive = p[2] & 2;
        if (state_ == CtlState::Firing && pv_.state == PadState::Firing) lastSend_ = in_.now;  // FIRE was received
      }
      break;
    case Msg::Status:
      if (n >= 20) {
        for (int i = 0; i < cfg::kPads; ++i) pv_.ohmMilli[i] = get16(p + 2 * i);
        pv_.battMv = get16(p + 12);
        pv_.windDms = get16(p + 14);
        pv_.rssi = static_cast<int16_t>(get16(p + 16));
        pv_.snr = static_cast<int8_t>(p[18]);
        pv_.ohmFresh = p[19] != 0;
      }
      break;
    case Msg::Challenge:
      if (state_ == CtlState::Requesting && n >= 9 && p[8] == pads_) {
        std::memcpy(nonce_, p, 8);
        state_ = CtlState::Arming;
        stateAt_ = in_.now;
        sendArm();
      }
      break;
    case Msg::Armed:
      if (state_ == CtlState::Arming && n >= 9 && p[0] == pads_ && tagEqual(p + 1, nonce_, 8)) {
        state_ = CtlState::Counting;
        stateAt_ = in_.now;
      }
      break;
    case Msg::Fired:
      if (n >= 12) {
        for (int i = 0; i < cfg::kPads; ++i) pv_.fired[i] = get16(p + 2 * i);
        pv_.firedValid = true;
        if (state_ == CtlState::Firing) { state_ = CtlState::Done; stateAt_ = in_.now; }
      }
      break;
    case Msg::Safe:
      if (n >= 1 && state_ >= CtlState::Requesting && state_ <= CtlState::Firing) abort(static_cast<Reason>(p[0]), false);
      if (n >= 1) pv_.reason = static_cast<Reason>(p[0]);
      break;
    default:
      break;
  }
  return r;
}

void Controller::tick(const CtlInputs& in) {
  in_ = in;
  const uint32_t now = in.now;
  const bool held = in.fireHeld && in.keyOn && in.coverOk;

  // Heartbeat carries the operator's hands: bit0 key on, bit1 FIRE held (with key and cover).
  if (now - lastHb_ >= cfg::kHeartbeatMs) {
    lastHb_ = now;
    const uint8_t hb[1] = {static_cast<uint8_t>((in.keyOn ? 1 : 0) | (held ? 2 : 0))};
    queue(Msg::Heartbeat, hb, 1);
  }

  if (!linkUp() && state_ != CtlState::NoLink) {
    if (state_ >= CtlState::Requesting && state_ <= CtlState::Firing) abort(Reason::LinkLost, false);
    else if (state_ != CtlState::Aborted || !held) { state_ = CtlState::NoLink; stateAt_ = now; }
  }

  switch (state_) {
    case CtlState::NoLink:
      if (linkUp()) { state_ = CtlState::Ready; stateAt_ = now; }
      break;
    case CtlState::Ready:
      if (held && in.pads && pv_.state == PadState::Safe) {
        pads_ = in.pads; mode_ = in.mode; step_ = in.mode == Mode::Ripple ? in.rippleMs : 0;
        pv_.firedValid = false;
        state_ = CtlState::Requesting;
        stateAt_ = now;
        sendArmReq();
      }
      break;
    case CtlState::Requesting:
    case CtlState::Arming:
      if (!held) { abort(Reason::Operator, true); break; }
      if (now - stateAt_ > 3000) { abort(Reason::Timeout, true); break; }
      if (now - lastSend_ >= cfg::kRetryMs) state_ == CtlState::Requesting ? sendArmReq() : sendArm();
      break;
    case CtlState::Counting:
      if (!held) { abort(Reason::Operator, true); break; }
      if (now - stateAt_ >= cfg::kCountdownMs) {
        state_ = CtlState::Firing;
        stateAt_ = now;
        sendFire();
      }
      break;
    case CtlState::Firing:
      if (!held) { abort(Reason::Operator, true); break; }  // stops the rest of a ripple
      if (pv_.state != PadState::Firing && now - lastSend_ >= cfg::kRetryMs && now - stateAt_ < 2000) sendFire();
      if (now - stateAt_ > 15000) { state_ = CtlState::Done; stateAt_ = now; }
      break;
    case CtlState::Done:
    case CtlState::Aborted:
      if (!held && linkUp()) { state_ = CtlState::Ready; stateAt_ = now; }
      break;
  }
}

}  // namespace relay6
