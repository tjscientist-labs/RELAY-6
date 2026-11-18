#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build guide for the six-pad wireless launcher (US Letter, portrait, prints to PDF).

    python3 -I src/gen_guide.py            # from the repo root

Reads: figs/*.svg (schematics, views, panel sheets), shop/bom.json (prices), src/parts.py (sizes).
Writes: build_guide.html. src/make_pack.sh prints it.
"""
import html, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import parts

REV, DATE = "A", "2026-11-18"


def svg(name):
    p = os.path.join(ROOT, "figs", name)
    s = open(p).read()
    s = re.sub(r'^<\?xml[^>]*>', '', s)
    return s


def fig(name, cap, n):
    return f'<figure>{svg(name)}<figcaption><b>Figure {n}.</b> {cap}</figcaption></figure>'


def bom_tables():
    b = json.load(open(os.path.join(ROOT, "shop", "bom.json")))
    out = []
    for g in b["groups"]:
        rows = []
        for it in g["items"]:
            buy = it.get("buy") or []
            v = buy[0][0] if buy else ""
            rows.append(f'<tr><td>{html.escape(it.get("qty",""))}</td><td><b>{html.escape(it["item"])}</b><br>'
                        f'<span class="muted">{html.escape(it.get("spec",""))}</span></td>'
                        f'<td class="mono">{html.escape(it.get("mpn",""))}</td><td>{html.escape(v)}</td>'
                        f'<td class="num">{html.escape(it.get("price",""))}</td></tr>')
        out.append(f'<h4>{html.escape(g["name"])}</h4><table><thead><tr><th>Qty</th><th>Part</th><th>Part no.</th>'
                   f'<th>Source</th><th>Price</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')
    return "".join(out), b


def cost_table(b):
    t = b.get("totals", {})
    rows = "".join(f'<tr><td>{html.escape(k)}</td><td class="num">{html.escape(v)}</td></tr>' for k, v in t.items())
    return f'<table class="narrow"><thead><tr><th>Build</th><th>Parts cost (USD)</th></tr></thead><tbody>{rows}</tbody></table>'


CSS = open(os.path.join(HERE, "guide.css")).read()


def main():
    bomhtml, b = bom_tables()
    n = iter(range(1, 100))
    F = lambda name, cap: fig(name, cap, next(n))
    C = parts.CASES
    body = f"""
<main>
<h1>RELAY-6 Wireless Launcher</h1>
<p class="lead">Build guide for a six-pad, two-way wireless launch system: the RELAY-6 pad box and three controllers that share one
electronics core (HALO, FLIGHTDECK and MONOLITH). Licence-free LoRa, every packet authenticated, rated for high-power clusters.</p>
<table class="meta"><tr><td>Revision</td><td>{REV} · {DATE}</td></tr>
<tr><td>Status</td><td>Design complete on paper. Nothing has been built or flown yet; every gate below is still open.</td></tr>
<tr><td>Drawings</td><td>E-1 to E-6 (electrical), V-1 to V-6 (rendered views), P-1 to P-9 (1:1 cut sheets and drill templates, 11 × 17), DXF set</td></tr>
<tr><td>Parts</td><td>Priced bill of materials, {b.get("date","")}, in section 5 and as a printable PDF</td></tr></table>
<figure class="cover">{svg("V1_family.svg")}</figure>

<h3>Contents</h3>
<ol class="toc">
<li>How to use this guide</li><li>Overview</li><li>Safety</li><li>Theory of operation</li><li>Tools, materials and parts</li>
<li>The build, stage by stage</li><li>Commissioning</li><li>At the field</li><li>Maintenance and troubleshooting</li>
<li>Open items</li><li>Reference tables</li><li>Files and how to regenerate them</li></ol>

<h2>1. How to use this guide</h2>
<p>The build is split into stages. Each stage ends in a <b>gate</b>: a test that has to pass before the next stage starts. The order
puts every electrical risk on the bench first, with a current-limited supply and dummy loads, and only then puts the electronics in a case.
Live igniters come late, and a motor comes last.</p>
<p>Build the <b>pad box first</b>. It is the part that can fire a rocket and it is the same for every controller. Then build whichever
controller you like first; the other two are new panels on the same core and can follow at any time.</p>
<div class="note"><b>Conventions.</b> Dimensions are millimetres unless marked. "CHECK" means measure the part in your hand before
cutting its hole: hole sizes are taken from the makers' drawings where they publish one and are marked CHECK where they do not.
References like <span class="mono">K1</span>, <span class="mono">Q3</span> and <span class="mono">E-2</span> point at the
electrical drawings; <span class="mono">P-1</span> to <span class="mono">P-9</span> are the full-size cut sheets.</div>

<h2>2. Overview</h2>
<p>A wired launch controller is a battery, a key, a button and a long pair of wires. This design moves the battery and the switching out
to the pads and replaces the long wires with a radio link. That buys three things: no 30 m lead to unreel, full battery voltage at the
igniter instead of what is left after the wire, and a pad box that can measure each igniter and report back.</p>
{F("E1_system.svg", "The system. The controller only ever sends requests; the pad box decides, switches and reports.")}
<h3>The parts of the system</h3>
<table><thead><tr><th>Unit</th><th>What it does</th><th>Case</th></tr></thead><tbody>
<tr><td><b>RELAY-6 pad box</b></td><td>Six fire channels (40 A-class MOSFETs), changeover relay that grounds the igniter bus when safe,
local arm key, hardware watchdog, igniter resistance meter, ignition timer, beacon, siren, anemometer.</td><td>{html.escape(C["padbox"]["name"])}</td></tr>
<tr><td><b>HALO</b></td><td>Six lit pad keys in a ring around a covered FIRE button, inside an edge-lit acrylic halo that drains as the count runs.</td><td>{html.escape(C["halo"]["name"])}</td></tr>
<tr><td><b>FLIGHTDECK</b></td><td>Six toggle switches under red flip covers, a two-hand fire zone (ARM left, FIRE right) and a backlit checklist in the lid.</td><td>{html.escape(C["flightdeck"]["name"])}</td></tr>
<tr><td><b>MONOLITH</b></td><td>Six slide levers you push forward to commit a pad, a twist-collar fire core and a twin-OLED strip in the lid.</td><td>{html.escape(C["monolith"]["name"])}</td></tr>
</tbody></table>
{F("V2_padbox.svg", "V-2. The RELAY-6 pad box at the rack: beacon mast, anemometer, antenna, six Powerpole outputs, key and battery gauge.")}
<h3>Key numbers</h3>
<table class="narrow"><tbody>
<tr><td>Pads</td><td>6 per pad box; the protocol carries a bank number so a second box can join later</td></tr>
<tr><td>Fire modes</td><td>Single · Select (any set) · Salvo (all six) · Ripple (0.25–5 s steps) · Drag race</td></tr>
<tr><td>Pyro supply</td><td>12 V sealed lead-acid, 7.2 Ah (as TeleLaunch); 40 A main fuse; 15 A fuse per pad</td></tr>
<tr><td>Fire pulse</td><td>1.0 s per pad (firmware constant; see section 11)</td></tr>
<tr><td>Igniter test current</td><td>≈ 0.9 mA (3.30 kΩ from a 3.0 V rail), SAFE state only</td></tr>
<tr><td>Radio</td><td>LoRa on one 915 MHz channel, SF8, 500 kHz bandwidth, licence-free under FCC Part 15; 868 MHz build option for Europe</td></tr>
<tr><td>Link security</td><td>LoRa CRC + AES-128-CMAC tag + 32-bit counter + ARM nonce; 4 Hz heartbeat, 1 s fail-safe</td></tr>
<tr><td>Controller battery</td><td>2 × 18650 in parallel (1S2P), USB-C charging</td></tr>
</tbody></table>

<h2>3. Safety</h2>
<div class="warn"><b>This is a pyrotechnic firing system.</b> Treat the pad box as live whenever its battery is connected. Build and
test every stage with dummy loads (resistors or lamps), not igniters. Fit real igniters only in Stage 6, outdoors, with no motor.
Fit a motor only after commissioning (section 7).</div>
<h3>Rules the design follows</h3>
<p>The NAR Model Rocket Safety Code and the NAR and Tripoli high-power codes require an electrical launch system with a safety
interlock in series with the launch switch, and a launch switch that returns to off when released. They also require a countdown,
and a wait after a misfire before anyone approaches the pad. Check the current text of the code that applies to your launch: the
wording, the misfire wait and the minimum distances are set there, not here.</p>
<ul>
<li><b>Interlock in series:</b> the pad box key S2 is in series with the K1 relay coil. With the key out, no current can reach the igniter bus. The controller key is a second, firmware interlock.</li>
<li><b>Spring-return launch switch:</b> every FIRE control is momentary. Releasing it stops the count or the fire command.</li>
<li><b>Fail-safe radio:</b> the pad box drops to SAFE when it hears nothing valid for 1 s, in firmware and in hardware (watchdog U2).</li>
<li><b>Shorted when safe:</b> at rest, K1 ties the igniter bus to ground, so stray voltage cannot appear across an igniter.</li>
</ul>
<h3>Batteries</h3>
<ul>
<li>A lead-acid battery can deliver hundreds of amps into a short. Fit F0 (40 A) within 100 mm of the battery terminal and use 12 AWG or heavier from the battery to K1.</li>
<li>Charge the pad box with a 12 V lead-acid smart charger, with S1 off. Why not LiFePO₄: small 12 V LiFePO₄ packs carry a protection board that limits current (the 10 Ah ExpertPower: 10 A continuous, 15 A for 10 s). A six-pad salvo or an HPR cluster can trip it and switch the whole pad box off. Use LiFePO₄ only if its board is rated for 40 A pulses or more, with a LiFePO₄ charger (14.6 V).</li>
<li>The controller's 18650 cells: buy from a reputable cell seller, use a protected holder or a BMS, and never leave them charging unattended.</li>
</ul>
<h3>Radio</h3>
<p>The LoRa modules run in the 902–928 MHz band under FCC Part 15. Use the antenna type the module was sold with and do not add an amplifier.
Builders outside the US must buy the 868 MHz (or local) version of the modules and set the region in firmware.</p>

<h2>4. Theory of operation</h2>
<h3>4.1 What a launch system has to do</h3>
<p>An igniter is a small resistive bridge, typically around an ohm, that heats a pyrogen until it lights the motor. Model-rocket
igniters need a few amps for a fraction of a second; electric matches need less but must have it reliably. A launch system therefore has
three jobs: deliver a short pulse of high current to the chosen igniters and nowhere else; make certain that it cannot do so by accident;
and tell the operator, before the button is pressed, whether each igniter is connected.</p>
<h3>4.2 The pad box: power and arming</h3>
{F("E2_power_arming.svg", "E-2. Pad box power and arming. K1 at rest grounds the igniter bus; three independent conditions energise it.")}
<p>The battery feeds two paths through the 40 A main fuse F0. The <b>logic path</b> goes through the main switch S1 to a 5 V buck
converter for the ESP32 board, the beacon and the sensors. The <b>pyro path</b> goes straight to the normally-open contact (87) of K1,
a 40 A automotive changeover relay.</p>
<p>K1's common terminal (30) is the igniter bus, PAD+. At rest K1 connects PAD+ to its normally-closed contact (87a), which is wired to
ground. So in SAFE the bus is not merely switched off but tied to 0 V. When K1 pulls in, PAD+ moves to the battery. An automotive
changeover relay breaks the first contact before it makes the second, so the battery is never shorted during the swap.</p>
<p>K1's coil current flows through the arm key S2 and the MOSFET Q7. Q7 is driven by U4 (half a TC4427 gate driver) from the AND gate U3.
One input of U3 is the firmware's ARM_EN line. The other is the output of U2, a retriggerable monostable used as a hardware watchdog:
the firmware toggles the HEARTBEAT line every time it receives a valid packet, and if the toggles stop for about a second, U2 times
out and U3's output falls no matter what the firmware is doing. The pad box can therefore only be armed while all three are true:
the key is in ARM, the firmware asks for it, and valid packets are still arriving.</p>
<p>The six gate drivers that fire the pads are powered from PAD+. While K1 is at rest they have no supply and cannot turn a MOSFET on,
so a firmware fault in SAFE cannot fire a pad.</p>
<h3>4.3 One pad channel and the igniter meter</h3>
{F("E3_pad_channel.svg", "E-3. One pad channel; build six. Low-side switching with a fuse, a TVS clamp and the resistance meter.")}
<p>The igniter connects between PAD+ (red Powerpole) and its own return, PAD−n (black Powerpole). PAD−n runs through a 15 A fuse to the
drain of an IRLB3034-type MOSFET (the Infineon original is out of production; the UMW part is a current equivalent) whose source returns to the battery through RS1, the current shunt. To fire, the firmware raises FIRE_n; the
gate driver lifts the gate to the 12 V of PAD+ and the MOSFET conducts. A 10 Ω gate resistor and a 100 kΩ pull-down keep the gate
quiet; an SMBJ15A transient suppressor clamps spikes picked up by the leads.</p>
<p><b>Resistance.</b> In SAFE, PAD+ is grounded, so a small current fed into PAD−n flows through the igniter to ground. One Schottky
diode from 3.3 V makes a shared TEST rail of about 3.0 V; a 3.30 kΩ, 0.1 % resistor from TEST to each PAD−n sets about 0.9 mA. Two
ADS1115 16-bit converters read TEST and each PAD−n. The firmware computes the current from the drop across the 3.30 kΩ resistor and
divides it into the PAD−n voltage. At the ±0.256 V range one count is 7.8 µV, which at 0.9 mA is about 0.009 Ω. An open igniter
lets PAD−n rise to TEST; a short reads near zero. The reading includes the clip leads, so take it with your leads.</p>
<p><b>Ignition time.</b> An INA228 reads RS1. When a pad fires, the current steps up; when the bridge burns through, it steps down. The
interval is reported as "lit in 184 ms". A pad whose current never drops within the pulse is reported as NO FIRE at once, before
anyone walks out.</p>
<h3>4.4 The radio link</h3>
<p>LoRa radios already add a CRC to every packet and discard any that arrive damaged. A CRC proves only that a packet was not corrupted;
anyone can compute one. So every packet also carries an 8-byte AES-128-CMAC tag computed with a key shared only by the paired controller
and pad box, and a 32-bit counter that must increase. A packet with a bad tag or an old counter is dropped without a reply.</p>
{F("E5_sequence.svg", "E-5. Arming and firing, packet by packet. The pad box issues a nonce; the ARM and FIRE packets must carry it.")}
<p>Arming is a challenge and response: the pad box answers an ARM request with a fresh random nonce, valid for 30 s, and accepts ARM and
FIRE only if they carry that nonce under a valid tag. A recording of last week's FIRE packet is therefore useless. Pairing writes a new
random key into both units over USB (or by an NFC tap); there is no default key, and an unpaired unit will not arm.</p>
{F("E6_states.svg", "E-6. Pad box states. Every path backwards is automatic; every path forwards needs a fresh, authenticated request.")}
<h3>4.5 The controller</h3>
{F("E4_controller.svg", "E-4. Controller wiring: the core is the same in all three cases; only the panel inputs and lights differ.")}
<p>The controller is a Heltec WiFi LoRa 32 V3 (ESP32-S3 with an SX1262 radio) plus a 3.12-inch 256 × 64 OLED, a rotary encoder, a key
switch, an NFC reader for the range-safety officer's card, an I²S amplifier and speaker for the spoken countdown, a GPS for the log, and
one chain of WS2812 LEDs for all the panel lights. It runs from two 18650 cells in parallel through a USB-C charger and a 5 V boost
converter. The E-STOP is in series with the battery: pressing it kills the controller, the pad box hears no heartbeat, and it drops to
SAFE within a second.</p>
<h3>4.6 Firmware</h3>
<p>Both units run one firmware tree (PlatformIO, Arduino-ESP32 with RadioLib for the SX1262 and the ESP32-S3's AES hardware for CMAC),
built twice with a role flag. The pad box firmware is the authority: it owns the state machine in E-6, and the controller can only ask.
Timing constants are collected in section 11. <b>Firmware Rev A</b> (<span class="mono">firmware/</span>): the core logic
(AES-128-CMAC, packets, both state machines, the Ω meter and ignition timer) is plain C++ and passes 71 host tests, including a recorded-packet
replay attack, link loss, a pulled key and a welded K1; all four targets compile for the Heltec V3. It has not yet run on hardware, so stages 1–5
are where it meets real boards. The radio runs on one 915 MHz channel at SF8 and 500 kHz bandwidth: for a single-channel (non-hopping)
system in 902–928 MHz, FCC 15.247 requires at least 500 kHz of bandwidth. Check the rules that apply to you.</p>

<h2>5. Tools, materials and parts</h2>
<h3>Tools</h3>
<ul><li>Temperature-controlled soldering iron, 60/40 or SAC305 solder, flux; a heavier iron or a torch for 12 AWG lugs.</li>
<li>Multimeter; a bench supply with current limit (to 2 A); a 4-wire ohmmeter or a 0.1 % reference resistor for Stage 5.</li>
<li>Step drills to 32 mm, a 22 mm and a 30 mm punch or hole saw, a 60 mm hole saw, deburring tool, files.</li>
<li>Crimp tool for Anderson Powerpole; ratcheting crimper for ring lugs (12–10 AWG).</li>
<li>Laser cutter access or a cutting service for the acrylic panels (DXF set); a drill press for the ammo can.</li></ul>
<h3>What it costs</h3>
<p>Prices are what the listed suppliers showed on {b.get("date","")} for one unit (quantity breaks noted in the printable BOM), before tax
and shipping. The core is the same for all three controllers; the pad box is built once.</p>
{cost_table(b)}
<p><b>Where the money goes, and how to spend less.</b> The pad box is the largest item (≈ $630): the anemometer, siren, fuse block,
battery and charger are about $180 of it, and several lines are multi-packs (50 clips, 50 ft of wire, five relays, 25 Powerpole sets)
whose spares serve the other builds. Each controller carries about $87 of optional parts (GPS, NFC reader, cards): leave them off and
the flight log simply has no position and arming needs no card. The rugged 60 mm buttons, toggles and keylocks are where the feel is;
they are worth keeping. Laser-cut panels are allowances until the DXFs are quoted.</p>
<h3>Bill of materials</h3>
<p>The printable version (with tick boxes for ordered / in hand / fitted, alternates and order log) is
<span class="mono">shop/relay6-launcher-bom.pdf</span>.</p>
{bomhtml}

<h2>6. The build, stage by stage</h2>
{{STAGES}}

<h2>7. Commissioning</h2>
<p>Do this at a club launch or a private field you are permitted to fly at, with a range-safety officer, before the first flight.</p>
<ul class="check">
<li>Pair the controller and the pad box with a new key. Confirm an unpaired controller is ignored (OLED shows no link).</li>
<li>Range test with the antennas as they will be used: walk the controller out to twice your planned distance. RSSI and SNR on the LINK screen stay above the margin in section 11.</li>
<li>Six lamps (12 V, 21 W automotive) on the six outputs. Fire each mode: single, select, salvo, ripple at 0.5 s, drag race. The lamps flash in the expected order and the FIRED report matches.</li>
<li>Walk away until the link drops; the beacon turns green and K1 releases within 1 s.</li>
<li>Pull the pad key while ARMED: K1 releases at once and the controller shows the key fault.</li>
<li>Press the controller E-STOP while ARMED: the pad box returns to SAFE within about 1 s.</li>
<li>Fire one real igniter with no motor on each pad, then a cluster of three on one pad. Ignition times are reported.</li>
<li>Only then: first motor, single pad, low-power rocket, full countdown.</li>
</ul>

<h2>8. At the field</h2>
<h3>Setting up</h3>
<ol><li>Pad box to the rack, mast up, antenna on, S1 ON. Beacon green.</li>
<li>Clip leads on, one per pad. The controller's PAD screen shows each igniter's resistance; fix anything outside the window now.</li>
<li>Back at the line: controller on, link shown, wind under the limit.</li></ol>
<h3>Flying</h3>
<ol><li>RSO card on the NFC pad (if used). Key ON. Select pads and mode.</li>
<li>Walk out, turn the pad box key to ARM, walk back. (The pad key is the field's interlock: whoever holds it controls the rack.)</li>
<li>Call the range. Hold FIRE (both hands on FLIGHTDECK). The count runs on the speaker and the OLED; releasing FIRE stops it.</li>
<li>Read the FIRED report. Any NO FIRE: key the pad box to SAFE, wait the code's misfire time, then approach.</li></ol>
<h3>Packing up</h3>
<p>Pad key out first. S1 off. Leads coiled. The log is on the controller's microSD (or as a QR code on the OLED).</p>

<h2>9. Maintenance and troubleshooting</h2>
<table><thead><tr><th>Symptom</th><th>Likely cause</th><th>Check</th></tr></thead><tbody>
<tr><td>No link</td><td>Unpaired, wrong region, antenna not fitted</td><td>LINK screen; re-pair; SMA tight</td></tr>
<tr><td>Will not arm, "KEY"</td><td>Pad key in SAFE</td><td>S2 at the pad</td></tr>
<tr><td>Will not arm, "Ω"</td><td>Reading stale or outside window</td><td>Clips, igniter, PAD screen</td></tr>
<tr><td>Arms then drops</td><td>Heartbeat lost; weak link</td><td>RSSI/SNR; antenna height; U2 timing</td></tr>
<tr><td>Pad shows OPEN with igniter fitted</td><td>Clip on the wrong lead, broken bridge, blown Fn</td><td>Meter across Jn; Fn</td></tr>
<tr><td>NO FIRE after a valid FIRE</td><td>Igniter pyrogen failed, Fn blown, Qn open</td><td>Lamp on the pad; Fn; Qn gate voltage</td></tr>
<tr><td>FAULT: PAD+ live in SAFE</td><td>K1 welded or miswired</td><td>Replace K1 before further use</td></tr>
<tr><td>Battery warning</td><td>Under 11.8 V at rest</td><td>Charge the battery</td></tr>
</tbody></table>
<p>Before each season: re-run the Stage 5 calibration with the reference resistor, check every Powerpole contact for heat marks, cycle K1
50 times with a lamp load and check it releases every time.</p>

<h2>10. Open items</h2>
<ul>
<li><b>Firmware.</b> Rev A written and host-tested; not yet run on hardware. Still to do: voice clips (beeps only now), the GPS log, NFC RSO cards, the microSD log and QR code, and on-air range and timing checks.</li>
<li><b>Heltec V3 pin map.</b> The GPIO assignments in section 11 are proposals; check each against Heltec's pinout (pins used by the radio, the on-board OLED and flash are not free).</li>
<li><b>Igniter test current.</b> 0.9 mA was chosen so the meter can read ohms. Confirm it is far below the no-fire current of the igniters and e-matches you will use (maker's data sheet) before Stage 6.</li>
<li><b>Watchdog timing.</b> Set U2's R and C on the bench for 0.8–1.2 s and record the measured value.</li>
<li><b>Case sizes.</b> {html.escape(parts.CASE_NOTE)}</li>
<li><b>Range.</b> No range figure is claimed. Measure it (section 7) with the antennas you will use.</li>
<li><b>A PCB.</b> Revision A is built on proto boards. A carrier PCB for each unit would make it easier for others to copy; it is a later revision.</li>
</ul>

<h2>11. Reference tables</h2>
{{REFTABLES}}

<h2>12. Files and how to regenerate them</h2>
<pre>RELAY-6/
  DESIGN.md                 decisions and open questions
  src/parts.py              the single geometry source: cases, panels, holes
  src/gen_schematics.py     E-1 … E-6           →  figs/E*.svg
  src/gen_views.py          V-1 … V-6           →  figs/V*.svg
  src/gen_shop.py           P-1 … P-9 + DXFs    →  figs/P*_sheet.svg, shop/cut_sheets.html, shop/dxf/*.dxf
  src/bom_data.py, src/bom_padbox.py  the priced BOM  →  shop/bom.json
  firmware/                 pad box + controllers (PlatformIO); host tests: make -C firmware/test/host
  src/gen_guide.py          this guide          →  build_guide.html
  src/make_pack.sh          prints the guide, the cut sheets and the BOM, joins the build pack
  shop/bom.json             the priced BOM      →  shop/relay6-launcher-bom.pdf (MyWebssite bom_pdf.py)</pre>
<p>Run, from the repo root: <span class="mono">python3 -I src/bom_data.py</span> then <span class="mono">sh src/make_pack.sh</span>.
Edit <span class="mono">parts.py</span> for any size change and regenerate: never edit a DXF or an SVG by hand.</p>
</main>"""
    st = open(os.path.join(HERE, "guide_stages.html")).read()
    st = st.replace("{V3}", F("V3_padbox_inside.svg", "V-3. Inside the pad box: battery and heavy current along the back, logic at the front left."))
    st = st.replace("{V_HALO}", F("V4_halo.svg", "V-4. HALO assembled. Cut sheets P-1 (panel), P-2 (lid insert), P-3 (ring, cover, hinge blocks)."))
    st = st.replace("{V_FD}", F("V5_flightdeck.svg", "V-5. FLIGHTDECK assembled. Cut sheets P-4 (panel) and P-5 (lid insert)."))
    st = st.replace("{V_MONO}", F("V6_monolith.svg", "V-6. MONOLITH assembled. Cut sheets P-6 (panel) and P-7 (lid insert)."))
    st = st.replace("{P1}", F("P1_sheet.svg", "P-1 HALO panel, reduced. Print the full-size sheet from the cut-sheet PDF at 100 %."))
    st = st.replace("{P4}", F("P4_sheet.svg", "P-4 FLIGHTDECK panel, reduced."))
    st = st.replace("{P6}", F("P6_sheet.svg", "P-6 MONOLITH panel, reduced."))
    st = st.replace("{P8}", F("P8_sheet.svg", "P-8 pad box front face drill template, reduced."))
    body = body.replace("{STAGES}", st)
    body = body.replace("{REFTABLES}", open(os.path.join(HERE, "guide_reftables.html")).read())
    page = f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>RELAY-6 Wireless Launcher · Build guide Rev {REV}</title><style>{CSS}</style></head><body>{body}</body></html>'
    open(os.path.join(ROOT, "build_guide.html"), "w").write(page)
    print("build_guide.html", len(page))


if __name__ == "__main__":
    main()
