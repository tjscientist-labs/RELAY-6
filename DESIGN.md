# Six-pad wireless launcher — design notes

Rev 0.1, 2026-11-18. Concepts only, not a build spec. The canvas sources are in `concepts/` (claude.ai Design canvas "Wireless Launcher Concepts").

## Brief
Wireless, two-way comms, a nice OLED, as many features from TeleLaunch and the Overkill controller as possible plus new ones; up to 6 rockets; fire all together or individually; futuristic sci-fi case, Pelican-style knock-off; unique.

## Shared architecture (all three concepts)
- **Controller:** ESP32-S3; 3.12″ 256×64 SSD1322 OLED; rotary encoder; key switch; 6 pad selects; guarded FIRE; e-stop; speaker; GPS; 2S Li-ion.
- **Link:** LoRa SX1262 at 915 MHz (licence-free) with AES-128 and a rolling counter. Alternative: 70 cm like TeleLaunch (needs a ham licence).
  - Down: arm, select, fire, heartbeat. Up: per-pad Ω, battery, wind, ACK, RSSI.
- **Pad box RELAY-6:** 6 MOSFET channels (30 A+ pulse); per-pad resistance sense at about 100 µA; the key switch drives a contactor on the pyro bus; 12 V sealed lead-acid; RGB beacon mast; anemometer; siren; PowerPole outputs; bank number in the protocol so a second box can join later.

## Safety (non-negotiable)
- A removable key in series with the fire circuit, at both ends.
- The fire control returns to OFF when released.
- No arm without an ACK from the pad box.
- The pad box disarms itself if the heartbeat is lost for more than 1 s.
- The e-stop removes pyro power in hardware.
- A wired backup.

## Fire modes
- Single
- Select (any set)
- Salvo (all six)
- Ripple (staggered, 0.25–5 s)
- Drag race (selected pads, fired together)

## New features (beyond the sources)
- Igniter ohmmeter.
- Ignition timer: burn-through time per pad, so a no-fire shows at once.
- Wind lockout over 20 mph.
- Talking countdown.
- NFC RSO-card arming.
- Flight log to microSD or a QR code.
- RGB pad beacon.

## Concepts
- **A · HALO:** six pad keys in a ring around a covered FIRE button inside an edge-lit acrylic halo, which drains as the countdown. Gunmetal shell, orange latches, hex-mesh lid.
- **B · FLIGHTDECK:** an orange case with six red missile-switch covers, a hazard-striped two-hand fire zone (ARM left, FIRE right), and a backlit checklist card in the lid.
- **C · MONOLITH:** matte black, with six throttle levers (Hall-sensed) and a twist-collar fire core that springs back to safe. A twin-OLED strip and firing-order light columns sit in the lid.

## Decisions (2026-11-18)
- **Build all three concepts.** They share one electronics core and one RELAY-6 pad box; only the panel and case differ. Any of the three controllers pairs with the pad box.
- **Radio: LoRa, licence-free** (915 MHz US; 868 MHz build option for Europe). LoRa needs no licence, so anyone can build and use it (a 70 cm ham version would not). Condition: it has to be safe, with every message CRC-checked or equivalent. Answer: the LoRa hardware CRC catches corrupted packets, and an AES-128-CMAC tag on every packet rejects packets the system did not send (see the link protocol below).
- **HPR: yes.** Clusters and high-current igniters. The pad box sits at the rack, so leads stay short.
- **Licence: GPL v2 or later** (decided 2026-11-18), for the firmware, generators, drawings and documents alike. Public repo: https://github.com/tjscientist-labs/RELAY-6
- **Budget:** "a bit expensive is fine, but it shouldn't cost too much." See the cost estimate.

## Link protocol (safety)
1. **LoRa PHY CRC is on:** the radio drops any packet with a bit error.
2. **Every packet is authenticated.** Each one carries a system ID, bank, message type, a 32-bit sequence counter, the payload, and an 8-byte **AES-128-CMAC** tag. The tag uses a key shared only by the paired controller and pad box. A packet with a bad tag is ignored.
3. **No replay:** the pad box rejects any counter it has already seen, so a recorded FIRE packet is useless.
4. **Arming is a challenge-response.** The pad box issues a fresh nonce, the controller answers with a MAC over it, and the FIRE packet must carry the same nonce. The nonce expires after 30 s.
5. **Heartbeat:** 4 Hz in both directions. If no valid heartbeat arrives for 1 s, the pad box drops the pyro contactor.
6. **Pairing:** a USB cable or an NFC tap writes a new random key into both units. There is no default key, and the unit will not arm until it has been paired.

This is the fix for the garage-door-opener launcher that "would sometimes go off on its own". Stray RF, a neighbour's remote or a corrupted packet cannot make a valid tag.

## HPR changes
- Each channel gets a 40 A-class logic-level MOSFET and a 15 A blade fuse.
- 12 V sealed lead-acid 7.2 Ah (Rev A, 2026-11-18): small 12 V LiFePO₄ packs have protection boards rated 10 A continuous / 15 A for 10 s, which a salvo or cluster can trip. LiFePO₄ only with a ≥ 40 A pulse BMS.
- The resistance sense allows several parallel igniters per pad for clusters, and shows the combined Ω.
- An optional 24 V boost rail for long leads or high-current e-matches. It's a later decision.

## Cost (rev A, priced 2026-11-18 — replaces the rough rev 0.2 estimate)
Priced line by line from supplier pages (`src/bom_data.py`, `src/bom_padbox.py` → `shop/bom.json`):

| Build | USD |
|---|---|
| RELAY-6 pad box | ≈ 632 |
| HALO controller (core + panel) | ≈ 430 |
| FLIGHTDECK controller | ≈ 527 |
| MONOLITH controller | ≈ 499 |
| Pad box + HALO | ≈ 1,062 |
| Pad box + all three | ≈ 2,087 |

- Optional GPS + NFC: ≈ $87 per controller.
- The rough estimate (≈ $670 one + box; ≈ $1,470 all) was low. The causes:
  - the GPS and NFC parts;
  - panel fabrication allowances;
  - multi-packs (50 clips, 50 ft of wire, 5 relays, 25 Powerpole sets).

**Design changes from pricing (2026-11-18):**
- **MOSFET:** Infineon IRLB3034PBF is obsolete. Use UMWIRLB3034; the alternate is IPP015N04NF2S.
- **K1:** the Bosch relay is only 20/30 A, so K1 is a Nilight 40/30 A.
- **Battery:** the 10 Ah LiFePO₄ BMS is 10 A continuous / 15 A for 10 s, so BT1 is a 12 V 7.2 Ah SLA.
- **Watchdog and AND gate:** 74LVC1G parts are SMD only, so they are CD74HC123E and 74HC08 (DIP).
- **Mast:** there is no hinge for a ½ in OD tube, so it is a two-piece plug-in mast.

## Open questions
- Which concept gets built first?
