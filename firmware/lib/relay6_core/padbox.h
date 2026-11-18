// SPDX-License-Identifier: GPL-2.0-only
// RELAY-6 pad box logic (drawing E-6). Pure logic: the application reads the hardware into Inputs,
// calls tick(), drives the pins from out(), and moves packets between the radio and onPacket()/nextTx().
// The pad box is the authority: every path back to SAFE is automatic, every path forward needs a fresh,
// authenticated request. The hardware watchdog and key (E-2) drop K1 even if this code is wrong or hung.
#pragma once
#include <cstddef>
#include <cstdint>

#include "config.h"
#include "measure.h"
#include "protocol.h"

namespace relay6 {

enum class PadState : uint8_t { Safe = 0, Checking = 1, Armed = 2, Firing = 3, Fault = 4 };
enum class Beacon : uint8_t { Off, NoLink, Safe, Armed, Firing, Fault };

struct PadInputs {
  uint32_t now = 0;
  bool keyArm = false;      // S2 in ARM (sensed)
  bool padLive = false;     // PAD+ bus voltage present (K1 pulled in)
  uint16_t battMv = 0;
  uint16_t windDms = 0;     // 0.1 m/s
  OhmReading ohm[cfg::kPads];
  uint32_t ohmAt = 0;       // time the readings were taken (0 = never)
  float amps = 0;           // shunt current
  int16_t rssi = 0;         // of the last received packet
  int8_t snr = 0;
};

struct PadOutputs {
  bool armEn = false;       // to U3 (with the watchdog) -> K1
  uint8_t gates = 0;        // FIRE_1..6 bit mask
  bool siren = false;
  Beacon beacon = Beacon::Off;
  uint32_t validRx = 0;     // increments on each authenticated packet: toggle HEARTBEAT on change
};

class PadBox {
 public:
  using Rng = uint32_t (*)();
  PadBox(const LinkKeys& keys, uint32_t firstTxCounter, uint32_t lastRxCounter, Rng rng);

  void tick(const PadInputs& in);
  OpenResult onPacket(const uint8_t* pkt, size_t len);
  bool nextTx(uint8_t* out, size_t& len);   // pops one queued packet

  const PadOutputs& out() const { return out_; }
  PadState state() const { return state_; }
  Reason lastReason() const { return reason_; }
  uint8_t armedPads() const { return pads_; }
  bool linkUp() const;
  uint32_t txCounter() const { return seal_.counter(); }
  uint32_t rxCounter() const { return open_.lastAccepted(); }
  uint16_t firedMs(int pad) const { return fired_[pad]; }

 private:
  struct Step { uint8_t mask; uint32_t at; uint32_t len; IgnitionTimer timer; bool started; bool ended; };

  void toSafe(Reason r);
  void queue(Msg m, const uint8_t* p, size_t n);
  void sendSafe(Reason r);
  bool checksFor(uint8_t pads, Reason& why) const;
  static bool validRequest(uint8_t pads, Mode mode, uint16_t stepMs);
  void handle(Msg m, const uint8_t* p, size_t n);
  void plan(uint32_t now);
  void runFiring(uint32_t now);
  void periodic(uint32_t now);

  Sealer seal_;
  Opener open_;
  Rng rng_;
  PadInputs in_{};
  PadOutputs out_{};
  PadState state_ = PadState::Safe;
  Reason reason_ = Reason::None;
  uint32_t stateAt_ = 0, lastRx_ = 0, lastHb_ = 0, lastStatus_ = 0, k1Since_ = 0;
  bool ctrlFireHeld_ = false, faultSawKeyOff_ = false;
  uint8_t nonce_[8] = {0};
  uint8_t pads_ = 0;
  Mode mode_ = Mode::Single;
  uint16_t stepMs_ = 0;
  Step steps_[cfg::kPads]{};
  uint8_t nSteps_ = 0;
  uint16_t fired_[cfg::kPads] = {0};
  bool firedPending_ = false;
  uint32_t safeAt_ = 0;

  uint8_t txq_[4][kMaxPacket];
  size_t txlen_[4] = {0};
  uint8_t txHead_ = 0, txCount_ = 0;
};

}  // namespace relay6
