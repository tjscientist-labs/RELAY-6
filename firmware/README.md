# RELAY-6 firmware (Rev A)

One source tree for the pad box and the three controllers. **Status (2026-11-18): the core logic is written and
passes 71 host tests. All four targets compile for the Heltec WiFi LoRa 32 V3. Nothing has run on hardware yet:
build-guide stages 1–5 are where it meets real boards.**

| Path | What |
|---|---|
| `lib/relay6_core/` | Plain C++17, no Arduino code: AES-128 and CMAC, packet sealing/opening, the pad-box state machine (drawing E-6), controller logic, igniter Ω and the ignition timer, timing constants (`config.h`) |
| `test/host/` | Host tests (`make -C test/host`): FIPS-197 and RFC 4493 vectors, tamper/replay/reflection, and end-to-end controller ↔ pad box runs including a replay attack, link loss, key pulled, K1 welded, ripple ordering, NO FIRE |
| `src/common/` | Heltec V3 pins (`board.h`), SX1262 radio, NVS pairing and counters, serial console |
| `src/padbox/` | Pad box: ADS1115 ×2, INA228, gates, ARM_EN, watchdog heartbeat, beacon, siren |
| `src/controller/` | Controller: SSD1322 OLED screens, panel input (`panel.cpp`, one per build flag), WS2812 lights, countdown beeps |
| `tools/pair.py` | Makes a pairing line for both units |

## Build

```
make -C test/host                       # the logic, on any PC (g++)
pio run                                 # all four targets
pio run -e padbox -t upload             # or halo / flightdeck / monolith
pio device monitor                      # 115200: show, status, pair …, offset <pad> <mΩ>
```

## Pair

`python3 tools/pair.py` prints one line, for example `pair 3f…c1 9a41d2e0 1`. Paste the same line into the
pad box's serial console and into the controller's. An unpaired unit will not arm, and there is no default key.

## How it behaves

- **Arming happens only while FIRE is held.** Hold FIRE (with the key on and the cover open), and the controller
  sends ARM_REQ. The pad box checks its own key, the Ω readings, wind and battery, then answers with a nonce. The
  controller sends ARM, the pad box arms, the 5-second count runs, and then the controller sends FIRE. Let go at any
  point and the controller sends SAFE.
- **Every packet carries an 8-byte AES-128-CMAC tag** (header + payload), a sender direction bit and a 32-bit
  counter. The LoRa radio also adds a CRC. ARM and FIRE must carry the current nonce, so recorded packets are
  useless. Counters are reserved in NVS in blocks of 1024, so they keep increasing across power cycles.
- **Radio:** 915 MHz, SF8, 500 kHz bandwidth on one channel; see `board.h`. The pad box transmits only straight
  after it hears the controller, so the two never talk over each other.
- **Hardware first:** the key S2 and the watchdog U2 drop K1 whatever the firmware does (drawing E-2).

## Open

- Voice clips (only beeps now), the GPS log, NFC RSO cards, the microSD flight log and QR code.
- The pin map is a proposal: check `board.h` and the pin lists in `src/*/main.cpp` against Heltec's pinout.
- Range and timing on real radios; the U2 watchdog value measured in Stage 3.
- An nRF52840 port (for example the RAK4631, which pairs an nRF52840 with an SX1262): `lib/relay6_core` is
  portable, so only `src/common/link.cpp` (radio, storage) and the pin map change.
