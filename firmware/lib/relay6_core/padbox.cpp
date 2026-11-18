// SPDX-License-Identifier: GPL-2.0-or-later
#include "padbox.h"

#include <cstring>

namespace relay6 {
namespace {

int bits(uint8_t m) {
  int n = 0;
  while (m) { n += m & 1; m >>= 1; }
  return n;
}

}  // namespace

PadBox::PadBox(const LinkKeys& keys, uint32_t firstTxCounter, uint32_t lastRxCounter, Rng rng)
    : seal_(keys, true, firstTxCounter), open_(keys, false, lastRxCounter), rng_(rng) {}

bool PadBox::linkUp() const { return lastRx_ != 0 && in_.now - lastRx_ < cfg::kLinkLossMs; }

void PadBox::queue(Msg m, const uint8_t* p, size_t n) {
  if (txCount_ == 4) {  // drop the oldest: fresh state matters more than history
    txHead_ = static_cast<uint8_t>((txHead_ + 1) % 4);
    --txCount_;
  }
  const uint8_t slot = static_cast<uint8_t>((txHead_ + txCount_) % 4);
  txlen_[slot] = seal_.seal(m, p, n, txq_[slot]);
  ++txCount_;
}

bool PadBox::nextTx(uint8_t* out, size_t& len) {
  if (!txCount_) return false;
  len = txlen_[txHead_];
  std::memcpy(out, txq_[txHead_], len);
  txHead_ = static_cast<uint8_t>((txHead_ + 1) % 4);
  --txCount_;
  return true;
}

void PadBox::sendSafe(Reason r) {
  const uint8_t p[1] = {static_cast<uint8_t>(r)};
  queue(Msg::Safe, p, 1);
}

void PadBox::toSafe(Reason r) {
  const bool wasLive = state_ == PadState::Armed || state_ == PadState::Firing || state_ == PadState::Checking;
  if (state_ == PadState::Firing && r == Reason::Done) {
    firedPending_ = true;  // FIRED goes out after the post-fire Ω reading (or a timeout)
  }
  state_ = PadState::Safe;
  stateAt_ = in_.now;
  safeAt_ = in_.now;
  reason_ = r;
  pads_ = 0;
  nSteps_ = 0;
  std::memset(nonce_, 0, sizeof nonce_);  // a used or abandoned nonce is never valid again
  out_.armEn = false;
  out_.gates = 0;
  out_.siren = false;
  if (wasLive && r != Reason::Done) sendSafe(r);
}

bool PadBox::validRequest(uint8_t pads, Mode mode, uint16_t stepMs) {
  if (pads == 0 || (pads & 0xC0)) return false;
  switch (mode) {
    case Mode::Single: return bits(pads) == 1;
    case Mode::Select: case Mode::Salvo: return true;
    case Mode::Drag: return bits(pads) >= 2;
    case Mode::Ripple: return bits(pads) >= 2 && stepMs >= cfg::kRippleMinMs && stepMs <= cfg::kRippleMaxMs;
  }
  return false;
}

bool PadBox::checksFor(uint8_t pads, Reason& why) const {
  if (!in_.keyArm) { why = Reason::KeyOff; return false; }
  if (in_.battMv < cfg::kBattCutMv) { why = Reason::Battery; return false; }
  if (in_.windDms > cfg::kWindLimitDms) { why = Reason::Wind; return false; }
  if (in_.ohmAt == 0 || in_.now - in_.ohmAt > cfg::kOhmMaxAgeMs) { why = Reason::OhmStale; return false; }
  for (int i = 0; i < cfg::kPads; ++i)
    if ((pads >> i) & 1)
      if (in_.ohm[i].cls != OhmClass::Ok) { why = Reason::OhmWindow; return false; }
  return true;
}

OpenResult PadBox::onPacket(const uint8_t* pkt, size_t len) {
  Header h;
  const uint8_t* p = nullptr;
  size_t n = 0;
  const OpenResult r = open_.open(pkt, len, h, p, n);
  if (r != OpenResult::Ok) return r;  // silently dropped: no reply to anything unauthenticated
  lastRx_ = in_.now ? in_.now : 1;
  ++out_.validRx;
  handle(static_cast<Msg>(h.type), p, n);
  return r;
}

void PadBox::handle(Msg m, const uint8_t* p, size_t n) {
  switch (m) {
    case Msg::Heartbeat:
      if (n >= 1) {
        ctrlFireHeld_ = (p[0] & 0x02) != 0;
        if (!ctrlFireHeld_ && (state_ == PadState::Checking || state_ == PadState::Armed || state_ == PadState::Firing))
          toSafe(Reason::Operator);
      }
      break;
    case Msg::Safe:
      if (state_ != PadState::Safe && state_ != PadState::Fault) toSafe(Reason::Operator);
      break;
    case Msg::ArmReq: {
      if (n < 4) break;
      const uint8_t pads = p[0];
      const Mode mode = static_cast<Mode>(p[1]);
      const uint16_t step = get16(p + 2);
      if (state_ == PadState::Checking && pads == pads_ && mode == mode_) {  // retry: same challenge
        uint8_t c[9];
        std::memcpy(c, nonce_, 8);
        c[8] = pads_;
        queue(Msg::Challenge, c, 9);
        break;
      }
      if (state_ != PadState::Safe) break;
      Reason why = Reason::None;
      if (!validRequest(pads, mode, step)) { sendSafe(Reason::BadRequest); break; }
      if (!checksFor(pads, why)) { reason_ = why; sendSafe(why); break; }
      for (int i = 0; i < 2; ++i) put32(nonce_ + 4 * i, rng_());
      pads_ = pads; mode_ = mode; stepMs_ = step;
      state_ = PadState::Checking;
      stateAt_ = in_.now;
      uint8_t c[9];
      std::memcpy(c, nonce_, 8);
      c[8] = pads_;
      queue(Msg::Challenge, c, 9);
      break;
    }
    case Msg::Arm: {
      if (n < 12) break;
      const bool same = p[0] == pads_ && static_cast<Mode>(p[1]) == mode_ && get16(p + 2) == stepMs_ &&
                        tagEqual(p + 4, nonce_, 8);
      if (state_ == PadState::Armed && same) {  // retry: repeat the ACK
        uint8_t a[9];
        a[0] = pads_;
        std::memcpy(a + 1, nonce_, 8);
        queue(Msg::Armed, a, 9);
        break;
      }
      if (state_ != PadState::Checking) break;
      if (!same) { toSafe(Reason::NonceBad); break; }
      Reason why = Reason::None;
      if (!checksFor(pads_, why)) { toSafe(why); break; }
      state_ = PadState::Armed;
      stateAt_ = in_.now;
      out_.armEn = true;
      uint8_t a[9];
      a[0] = pads_;
      std::memcpy(a + 1, nonce_, 8);
      queue(Msg::Armed, a, 9);
      break;
    }
    case Msg::Fire: {
      if (n < 12 || state_ != PadState::Armed) break;  // in FIRING a resent FIRE is ignored
      const bool same = p[0] == pads_ && static_cast<Mode>(p[1]) == mode_ && get16(p + 2) == stepMs_ &&
                        tagEqual(p + 4, nonce_, 8);
      if (!same) { toSafe(Reason::NonceBad); break; }
      if (!in_.padLive) { toSafe(Reason::KeyOff); break; }
      state_ = PadState::Firing;
      stateAt_ = in_.now;
      plan(in_.now);
      break;
    }
    default:
      break;  // SELECT and anything else: informational only
  }
}

void PadBox::plan(uint32_t now) {
  nSteps_ = 0;
  for (auto& f : fired_) f = 0;
  if (mode_ == Mode::Ripple) {
    const uint32_t len = stepMs_ < cfg::kFirePulseMs ? stepMs_ : cfg::kFirePulseMs;  // one pad on at a time
    uint32_t at = now;
    for (int i = 0; i < cfg::kPads; ++i)
      if ((pads_ >> i) & 1) {
        steps_[nSteps_++] = Step{static_cast<uint8_t>(1 << i), at, len, IgnitionTimer{}, false, false};
        at += stepMs_;
      }
  } else {
    steps_[nSteps_++] = Step{pads_, now, cfg::kFirePulseMs, IgnitionTimer{}, false, false};
  }
}

void PadBox::runFiring(uint32_t now) {
  uint8_t gates = 0;
  bool allEnded = true;
  uint32_t lastEnd = 0;
  for (int s = 0; s < nSteps_; ++s) {
    Step& st = steps_[s];
    if (!st.started && now >= st.at) { st.started = true; st.timer.start(now); }
    if (st.started && !st.ended) {
      st.timer.sample(now, in_.amps);
      const bool single = bits(st.mask) == 1;
      // A single igniter that has burnt through can be switched off early; a cluster cannot (a slow one may still be heating).
      if (now - st.at >= st.len || (single && st.timer.lit() && now - st.at > st.timer.litMs() + 50u)) st.ended = true;
      else gates |= st.mask;
    }
    if (!st.ended) allEnded = false;
    const uint32_t end = st.at + st.len;
    if (end > lastEnd) lastEnd = end;
  }
  out_.gates = gates;
  if (allEnded) {
    for (int s = 0; s < nSteps_; ++s)
      for (int i = 0; i < cfg::kPads; ++i)
        if ((steps_[s].mask >> i) & 1) fired_[i] = steps_[s].timer.litMs();
    if (now - lastEnd >= cfg::kDoneHoldMs) toSafe(Reason::Done);
  }
}

void PadBox::periodic(uint32_t now) {
  if (now - lastHb_ >= cfg::kHeartbeatMs) {
    lastHb_ = now;
    const uint8_t hb[4] = {static_cast<uint8_t>(state_), static_cast<uint8_t>(reason_),
                           static_cast<uint8_t>((in_.keyArm ? 1 : 0) | (in_.padLive ? 2 : 0) | (linkUp() ? 4 : 0)), pads_};
    queue(Msg::Heartbeat, hb, 4);
  }
  if (now - lastStatus_ >= cfg::kStatusMs) {
    lastStatus_ = now;
    uint8_t st[20];
    for (int i = 0; i < cfg::kPads; ++i) put16(st + 2 * i, in_.ohm[i].cls == OhmClass::Open || in_.ohm[i].cls == OhmClass::Empty ? 0xFFFF : in_.ohm[i].milli);
    put16(st + 12, in_.battMv);
    put16(st + 14, in_.windDms);
    put16(st + 16, static_cast<uint16_t>(in_.rssi));
    st[18] = static_cast<uint8_t>(in_.snr);
    st[19] = static_cast<uint8_t>(in_.ohmAt != 0 && now - in_.ohmAt <= cfg::kOhmMaxAgeMs ? 1 : 0);
    queue(Msg::Status, st, 20);
  }
}

void PadBox::tick(const PadInputs& in) {
  in_ = in;
  const uint32_t now = in.now;

  // K1 welded or miswired: the bus is live while nothing asks for it.
  if (!out_.armEn && in.padLive) {
    if (!k1Since_) k1Since_ = now ? now : 1;
    if (now - k1Since_ >= cfg::kK1StuckMs && state_ != PadState::Fault) {
      toSafe(Reason::Fault);
      state_ = PadState::Fault;
      faultSawKeyOff_ = false;
      sendSafe(Reason::Fault);
    }
  } else {
    k1Since_ = 0;
  }

  switch (state_) {
    case PadState::Safe:
      if (firedPending_ && ((in.ohmAt > safeAt_) || now - safeAt_ > 1500)) {
        firedPending_ = false;
        uint8_t f[12];
        for (int i = 0; i < cfg::kPads; ++i) {
          uint16_t v = fired_[i];
          // Bridge still intact after the shot: that pad did not fire, whatever the current said.
          if (in.ohmAt > safeAt_ && v != 0 && in.ohm[i].cls == OhmClass::Ok) v = 0xFFFF;
          put16(f + 2 * i, v);
        }
        queue(Msg::Fired, f, 12);
      }
      break;
    case PadState::Checking:
      if (!linkUp()) toSafe(Reason::LinkLost);
      else if (!in.keyArm) toSafe(Reason::KeyOff);
      else if (now - stateAt_ > cfg::kNonceLifeMs) toSafe(Reason::Timeout);
      break;
    case PadState::Armed:
      if (!linkUp()) toSafe(Reason::LinkLost);
      else if (!in.keyArm) toSafe(Reason::KeyOff);
      else if (now - stateAt_ > cfg::kK1PullInMs && !in.padLive) toSafe(Reason::KeyOff);
      else if (in.windDms > cfg::kWindLimitDms) toSafe(Reason::Wind);
      else if (now - stateAt_ > cfg::kArmedMaxMs) toSafe(Reason::Timeout);
      break;
    case PadState::Firing:
      if (!linkUp()) toSafe(Reason::LinkLost);
      else if (!in.keyArm) toSafe(Reason::KeyOff);
      else runFiring(now);
      break;
    case PadState::Fault:
      out_.armEn = false;
      out_.gates = 0;
      if (!in.keyArm) faultSawKeyOff_ = true;
      if (faultSawKeyOff_ && in.keyArm && !in.padLive) { state_ = PadState::Safe; reason_ = Reason::None; }
      break;
  }

  out_.siren = state_ == PadState::Armed || state_ == PadState::Firing;
  switch (state_) {
    case PadState::Safe: out_.beacon = linkUp() ? Beacon::Safe : Beacon::NoLink; break;
    case PadState::Checking: case PadState::Armed: out_.beacon = Beacon::Armed; break;
    case PadState::Firing: out_.beacon = Beacon::Firing; break;
    case PadState::Fault: out_.beacon = Beacon::Fault; break;
  }
  if (state_ != PadState::Armed && state_ != PadState::Firing) out_.armEn = false;
  if (state_ != PadState::Firing) out_.gates = 0;

  periodic(now);
}

}  // namespace relay6
