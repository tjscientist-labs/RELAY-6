// SPDX-License-Identifier: GPL-2.0-or-later
// Host tests for relay6_core: crypto vectors, packet sealing, and end-to-end runs of a controller and a pad box
// joined by an in-memory link (with an attacker in the middle for the replay tests).
//   make -C test/host        (plain g++, no PlatformIO needed)
#include <cmath>
#include <cstdio>
#include <cstring>
#include <functional>
#include <string>
#include <vector>

#include "aes128.h"
#include "cmac.h"
#include "controller.h"
#include "measure.h"
#include "padbox.h"
#include "protocol.h"

using namespace relay6;

static int g_fail = 0, g_pass = 0;
#define CHECK(c)                                                                          \
  do {                                                                                    \
    if (c) ++g_pass;                                                                      \
    else { ++g_fail; std::printf("  FAIL %s:%d  %s\n", __FILE__, __LINE__, #c); }        \
  } while (0)

static std::vector<uint8_t> hex(const char* s) {
  std::vector<uint8_t> v;
  for (size_t i = 0; s[i] && s[i + 1]; i += 2) {
    unsigned b;
    std::sscanf(s + i, "%2x", &b);
    v.push_back(static_cast<uint8_t>(b));
  }
  return v;
}

static void test_aes() {
  auto k = hex("000102030405060708090a0b0c0d0e0f"), pt = hex("00112233445566778899aabbccddeeff");
  auto want = hex("69c4e0d86a7b0430d8cdb78070b4c55a");  // FIPS-197 appendix C.1
  uint8_t out[16];
  Aes128(k.data()).encryptBlock(pt.data(), out);
  CHECK(std::memcmp(out, want.data(), 16) == 0);
}

static void test_cmac() {
  auto k = hex("2b7e151628aed2a6abf7158809cf4f3c");  // RFC 4493 section 4
  auto m = hex("6bc1bee22e409f96e93d7e117393172aae2d8a571e03ac9c9eb76fac45af8e5130c81c46a35ce411e5fbc1191a0a52eff69f2445df4f9b17ad2b417be66c3710");
  struct V { size_t len; const char* mac; } vs[] = {{0, "bb1d6929e95937287fa37d129b756746"}, {16, "070a16b46b4d4144f79bdd9dd04a287c"},
                                                    {40, "dfa66747de9ae63030ca32611497c827"}, {64, "51f0bebf7e3b9d92fc49741779363cfe"}};
  Cmac c(k.data());
  for (auto& v : vs) {
    uint8_t mac[16];
    c.compute(m.data(), v.len, mac);
    CHECK(std::memcmp(mac, hex(v.mac).data(), 16) == 0);
  }
}

static LinkKeys keys(uint8_t seed = 7) {
  LinkKeys k;
  for (int i = 0; i < 16; ++i) k.key[i] = static_cast<uint8_t>(seed * 31 + i * 17 + 1);
  k.system = 0xC0FFEE01;
  k.bank = 1;
  return k;
}

static void test_seal_open() {
  LinkKeys k = keys();
  Sealer s(k, false, 100);
  Opener o(k, false, 0);
  uint8_t pkt[kMaxPacket];
  const uint8_t pay[3] = {1, 2, 3};
  size_t n = s.seal(Msg::Select, pay, 3, pkt);
  CHECK(n == kHeader + 3 + kTag);
  Header h; const uint8_t* p; size_t pn;
  CHECK(o.open(pkt, n, h, p, pn) == OpenResult::Ok);
  CHECK(pn == 3 && p[2] == 3 && h.counter == 100);
  CHECK(o.open(pkt, n, h, p, pn) == OpenResult::Replay);           // same packet again
  uint8_t bad[kMaxPacket];
  n = s.seal(Msg::Select, pay, 3, pkt);
  std::memcpy(bad, pkt, n); bad[kHeader + 1] ^= 1;                  // one payload bit
  CHECK(o.open(bad, n, h, p, pn) == OpenResult::BadTag);
  std::memcpy(bad, pkt, n); bad[6] ^= 0x80;                          // forge a huge counter
  CHECK(o.open(bad, n, h, p, pn) == OpenResult::BadTag);
  Opener wrongKey(keys(8), false, 0);
  LinkKeys k8 = keys(8); k8.system = k.system;
  Opener ok8(k8, false, 0);
  CHECK(ok8.open(pkt, n, h, p, pn) == OpenResult::BadTag);
  Opener fromPad(k, true, 0);                                        // expects pad-box packets: reflection refused
  CHECK(fromPad.open(pkt, n, h, p, pn) == OpenResult::WrongDirection);
  LinkKeys other = k; other.system = 0x12345678;
  Opener sys(other, false, 0);
  CHECK(sys.open(pkt, n, h, p, pn) == OpenResult::WrongSystem);
  CHECK(o.open(pkt, n, h, p, pn) == OpenResult::Ok);                 // the genuine one still opens
  CHECK(o.open(pkt, 5, h, p, pn) == OpenResult::TooShort);
  uint8_t big[30];
  CHECK(s.seal(Msg::Select, big, 30, pkt) == 0);
}

static void test_counter_block() {
  uint32_t first, stored;
  CounterBlock::onBoot(0, first, stored);
  CHECK(first == 1 && stored == 1024);
  uint32_t ns;
  CHECK(!CounterBlock::needAdvance(500, stored, ns));
  CHECK(CounterBlock::needAdvance(1023, stored, ns) && ns == 2048);
  CounterBlock::onBoot(2048, first, stored);   // after a power cycle the counter jumps past everything used
  CHECK(first == 2049);
}

static void test_ohms() {
  // 1.00 Ω igniter: V_PAD = 3.0 * 1 / 3301
  OhmReading r = igniterOhms(3.0f, 3.0f * 1.0f / 3301.0f, 3300.0f, 0);
  CHECK(r.cls == OhmClass::Ok && std::abs(static_cast<int>(r.milli) - 1000) <= 2);
  r = igniterOhms(3.0f, 3.0f * 1.2f / 3301.2f, 3300.0f, 200);       // 0.2 Ω of leads calibrated out
  CHECK(r.cls == OhmClass::Ok && std::abs(static_cast<int>(r.milli) - 1000) <= 2);
  CHECK(igniterOhms(3.0f, 2.99f, 3300.0f, 0).cls == OhmClass::Open);
  CHECK(igniterOhms(3.0f, 0.00001f, 3300.0f, 0).cls == OhmClass::Short);
  CHECK(igniterOhms(3.0f, 3.0f * 9.0f / 3309.0f, 3300.0f, 0).cls == OhmClass::OutOfWindow);
  CHECK(igniterOhms(0.0f, 0.0f, 3300.0f, 0).cls == OhmClass::Empty);
}

static void test_ignition() {
  IgnitionTimer t;
  t.start(1000);
  for (uint32_t ms = 1000; ms < 1400; ms += 10) t.sample(ms, ms < 1180 ? 2.5f : 0.02f);
  CHECK(t.lit() && t.litMs() >= 180 && t.litMs() <= 190);
  IgnitionTimer dud;
  dud.start(0);
  for (uint32_t ms = 0; ms < 1000; ms += 10) dud.sample(ms, 2.5f);   // never burns through
  CHECK(!dud.lit() && dud.litMs() == 0xFFFF);
}

// ---------------------------------------------------------------- end-to-end harness
static uint32_t g_seed = 1;
static uint32_t rng() { g_seed = g_seed * 1664525u + 1013904223u; return g_seed; }

struct Rig {
  LinkKeys k = keys();
  PadBox pad{k, 1, 0, rng};
  Controller ctl{k, 1, 0};
  PadInputs pin;
  CtlInputs cin;
  uint32_t now = 1000;
  bool linkCut = false;
  int burnMs = 180;                         // simulated igniter burn-through time
  uint8_t everGated = 0;
  std::vector<std::pair<uint32_t, uint8_t>> gateLog;
  std::vector<std::vector<uint8_t>> heardFromCtl;   // attacker's recording
  uint32_t gateOn[6] = {0};

  Rig() {
    pin.keyArm = true; pin.battMv = 12700; pin.windDms = 20;
    for (auto& o : pin.ohm) { o.milli = 1000; o.cls = OhmClass::Ok; }
    cin.keyOn = true; cin.coverOk = true; cin.pads = 0x01; cin.mode = Mode::Single;
  }
  void step(int ms = 10) {
    for (int t = 0; t < ms; t += 10) {
      now += 10;
      pin.now = now; cin.now = now;
      pin.ohmAt = pad.state() == PadState::Safe ? now : pin.ohmAt;   // fresh readings in SAFE
      // relay follows ARM_EN only if the key is in ARM (hardware)
      pin.padLive = pad.out().armEn && pin.keyArm;
      // simulated current: each gated pad draws 2.5 A until it burns through
      float amps = 0;
      for (int i = 0; i < 6; ++i) {
        if ((pad.out().gates >> i) & 1) {
          if (!gateOn[i]) gateOn[i] = now;
          if (now - gateOn[i] < static_cast<uint32_t>(burnMs)) amps += 2.5f;
          else pin.ohm[i].cls = OhmClass::Open;           // bridge gone
        }
      }
      pin.amps = amps;
      pad.tick(pin);
      ctl.tick(cin);
      if (pad.out().gates) { everGated |= pad.out().gates; gateLog.push_back({now, pad.out().gates}); }
      uint8_t buf[kMaxPacket]; size_t n;
      while (ctl.nextTx(buf, n)) { heardFromCtl.emplace_back(buf, buf + n); if (!linkCut) pad.onPacket(buf, n); }
      while (pad.nextTx(buf, n)) if (!linkCut) ctl.onPacket(buf, n);
    }
  }
};

static void test_single_fire() {
  Rig r;
  r.step(500);
  CHECK(r.ctl.state() == CtlState::Ready);
  r.cin.fireHeld = true;
  r.step(300);
  CHECK(r.pad.state() == PadState::Armed && r.pad.out().armEn);
  CHECK(r.ctl.state() == CtlState::Counting);
  CHECK(r.everGated == 0);                       // nothing fires during the count
  r.step(5200);
  CHECK(r.everGated == 0x01);
  r.step(4000);
  CHECK(r.pad.state() == PadState::Safe && !r.pad.out().armEn);
  CHECK(r.ctl.state() == CtlState::Done);
  CHECK(r.ctl.pad().firedValid && r.ctl.pad().fired[0] >= 170 && r.ctl.pad().fired[0] <= 200);
  r.cin.fireHeld = false;
  r.step(300);
  CHECK(r.ctl.state() == CtlState::Ready);
}

static void test_release_during_count() {
  Rig r;
  r.step(500);
  r.cin.fireHeld = true;
  r.step(2000);
  CHECK(r.ctl.state() == CtlState::Counting);
  r.cin.fireHeld = false;
  r.step(100);
  CHECK(r.pad.state() == PadState::Safe && !r.pad.out().armEn);
  r.step(6000);
  CHECK(r.everGated == 0);
}

static void test_link_loss_armed() {
  Rig r;
  r.step(500);
  r.cin.fireHeld = true;
  r.step(1000);
  CHECK(r.pad.state() == PadState::Armed);
  r.linkCut = true;
  r.step(1100);
  CHECK(r.pad.state() == PadState::Safe && r.pad.lastReason() == Reason::LinkLost && !r.pad.out().armEn);
  r.step(6000);
  CHECK(r.everGated == 0);
}

static void test_refusals() {
  {  // pad key in SAFE
    Rig r; r.pin.keyArm = false; r.step(500); r.cin.fireHeld = true; r.step(1000);
    CHECK(r.pad.state() == PadState::Safe && r.ctl.state() == CtlState::Aborted && r.ctl.reason() == Reason::KeyOff);
  }
  {  // igniter out of window
    Rig r; r.pin.ohm[0].cls = OhmClass::Open; r.step(500); r.cin.fireHeld = true; r.step(1000);
    CHECK(r.pad.state() == PadState::Safe && r.ctl.reason() == Reason::OhmWindow);
  }
  {  // wind
    Rig r; r.pin.windDms = 120; r.step(500); r.cin.fireHeld = true; r.step(1000);
    CHECK(r.ctl.reason() == Reason::Wind && r.everGated == 0);
  }
  {  // single mode with two pads selected
    Rig r; r.cin.pads = 0x03; r.step(500); r.cin.fireHeld = true; r.step(1000);
    CHECK(r.ctl.reason() == Reason::BadRequest && r.pad.state() == PadState::Safe);
  }
  {  // cover closed (HALO): FIRE held is not enough
    Rig r; r.cin.coverOk = false; r.step(500); r.cin.fireHeld = true; r.step(1000);
    CHECK(r.pad.state() == PadState::Safe && r.ctl.state() == CtlState::Ready);
  }
}

static void test_ripple_and_salvo() {
  {
    Rig r; r.cin.pads = 0x15; r.cin.mode = Mode::Ripple; r.cin.rippleMs = 500;   // pads 1, 3, 5
    r.step(500); r.cin.fireHeld = true; r.step(7500);
    CHECK(r.everGated == 0x15);
    bool overlap = false;
    for (auto& g : r.gateLog) { int b = 0; for (int i = 0; i < 6; ++i) b += (g.second >> i) & 1; if (b > 1) overlap = true; }
    CHECK(!overlap);                                    // one pad on at a time
    // order: pad 1 first, then 3, then 5
    std::vector<uint8_t> order;
    for (auto& g : r.gateLog) if (order.empty() || order.back() != g.second) order.push_back(g.second);
    CHECK(order.size() == 3 && order[0] == 0x01 && order[1] == 0x04 && order[2] == 0x10);
    r.step(4000);
    CHECK(r.ctl.state() == CtlState::Done);
  }
  {
    Rig r; r.cin.pads = 0x3F; r.cin.mode = Mode::Salvo;
    r.step(500); r.cin.fireHeld = true; r.step(5600);
    bool all = false;
    for (auto& g : r.gateLog) if (g.second == 0x3F) all = true;
    CHECK(all);
    r.step(4000);
    CHECK(r.ctl.pad().firedValid);
    for (int i = 0; i < 6; ++i) CHECK(r.ctl.pad().fired[i] != 0xFFFF);
  }
}

static void test_no_fire_reported() {
  Rig r; r.burnMs = 100000;                         // igniter never burns through
  r.step(500); r.cin.fireHeld = true; r.step(9000);
  CHECK(r.everGated == 0x01);
  CHECK(r.ctl.pad().firedValid && r.ctl.pad().fired[0] == 0xFFFF);
}

static void test_replay_attack() {
  // Record a whole successful firing, then replay every controller packet to a fresh pad box
  // (same keys, counters carried over as after a reboot with CounterBlock). Nothing may fire.
  Rig r;
  r.step(500); r.cin.fireHeld = true; r.step(9000);
  CHECK(r.everGated == 0x01);
  auto tape = r.heardFromCtl;
  uint32_t first, stored;
  CounterBlock::onBoot(1024, first, stored);
  PadBox fresh(r.k, first, 0, rng);   // rx floor 0: the worst case (receiver forgot everything)
  PadInputs pin = r.pin;
  pin.keyArm = true;
  for (auto& o : pin.ohm) o.cls = OhmClass::Ok;
  uint8_t gated = 0;
  uint32_t now = 100000;
  for (auto& pkt : tape) {
    now += 10;
    pin.now = now; pin.ohmAt = now; pin.padLive = fresh.out().armEn;
    fresh.tick(pin);
    fresh.onPacket(pkt.data(), pkt.size());
    gated |= fresh.out().gates;
    uint8_t buf[kMaxPacket]; size_t n; while (fresh.nextTx(buf, n)) {}
  }
  for (int i = 0; i < 200; ++i) { now += 10; pin.now = now; pin.padLive = fresh.out().armEn; fresh.tick(pin); gated |= fresh.out().gates; }
  CHECK(gated == 0);   // the old ARM/FIRE carry an old nonce: refused
}

static void test_k1_stuck() {
  Rig r;
  r.step(500);
  PadInputs in = r.pin;
  in.padLive = true;   // bus live with ARM_EN low
  for (int i = 0; i < 30; ++i) { in.now = (r.now += 10); r.pad.tick(in); }
  CHECK(r.pad.state() == PadState::Fault);
  in.padLive = false; in.keyArm = true;
  for (int i = 0; i < 10; ++i) { in.now = (r.now += 10); r.pad.tick(in); }
  CHECK(r.pad.state() == PadState::Fault);         // needs a key cycle
  in.keyArm = false; in.now = (r.now += 10); r.pad.tick(in);
  in.keyArm = true; in.now = (r.now += 10); r.pad.tick(in);
  CHECK(r.pad.state() == PadState::Safe);
}

static void test_pad_key_pulled_while_armed() {
  Rig r;
  r.step(500); r.cin.fireHeld = true; r.step(1500);
  CHECK(r.pad.state() == PadState::Armed);
  r.pin.keyArm = false;
  r.step(20);
  CHECK(r.pad.state() == PadState::Safe && r.pad.lastReason() == Reason::KeyOff);
  r.step(6000);
  CHECK(r.everGated == 0);
}

int main() {
  struct T { const char* name; void (*fn)(); } tests[] = {
      {"AES-128 FIPS-197", test_aes}, {"CMAC RFC 4493", test_cmac}, {"seal/open, tamper, replay, reflection", test_seal_open},
      {"counter blocks", test_counter_block}, {"igniter ohms", test_ohms}, {"ignition timer", test_ignition},
      {"single pad fires after the count", test_single_fire}, {"release during count aborts", test_release_during_count},
      {"link loss while armed", test_link_loss_armed}, {"refusals", test_refusals}, {"ripple and salvo", test_ripple_and_salvo},
      {"no-fire reported", test_no_fire_reported}, {"replay attack", test_replay_attack}, {"K1 stuck -> FAULT", test_k1_stuck},
      {"pad key pulled while armed", test_pad_key_pulled_while_armed}};
  for (auto& t : tests) {
    const int before = g_fail;
    t.fn();
    std::printf("%s  %s\n", g_fail == before ? "ok  " : "FAIL", t.name);
  }
  std::printf("\n%d checks passed, %d failed\n", g_pass, g_fail);
  return g_fail ? 1 : 0;
}
