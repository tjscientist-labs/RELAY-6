#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Electrical drawings E-1 … E-6 for the six-pad wireless launcher.

    python3 -I src/gen_schematics.py figs

Writes E1_system.svg … E6_states.svg. Every value drawn here is listed in the build guide's
reference tables and in shop/bom.json; change them together.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sv import Svg, INK, MUTED, LIGHT, ACC, ACC2, OK, WARN, PAPER, MONO

W, H = 1100, 850


# ---------------------------------------------------------------- E-1 system
def e1():
    s = Svg(W, H, "E-1 System block diagram",
            "Controller and RELAY-6 pad box linked by LoRa; the pad box switches six igniters.")
    s.text(40, 52, "E-1 · System", 22, weight="bold")
    s.text(40, 76, "One controller (any of the three panels) pairs with one RELAY-6 pad box. Everything that can fire a rocket is in the pad box.", 12, MUTED)

    # controller
    s.rect(40, 110, 330, 560, c=INK, sw=1.6, fill="#FAFAFA", rx=10)
    s.text(205, 136, "CONTROLLER", 14, anchor="middle", weight="bold")
    s.text(205, 153, "HALO · FLIGHTDECK · MONOLITH (same core)", 10, MUTED, anchor="middle")
    blocks = [("ESP32-S3 + SX1262", "Heltec WiFi LoRa 32 V3"), ("OLED 3.12″ 256×64", "SSD1322, SPI"),
              ("Panel inputs", "6 pad selects · FIRE · mode · encoder"), ("Arm key + NFC", "PN532, NTAG215 RSO cards"),
              ("Panel lights", "WS2812 chain via 74AHCT125"), ("Voice", "MAX98357A I²S + 40 mm speaker"),
              ("GPS", "u-blox M10, UART"), ("Power", "1S2P 18650 · USB-C charge · 5 V boost · E-STOP")]
    for i, (a, b) in enumerate(blocks):
        y = 172 + i * 60
        s.rect(60, y, 290, 48, c=INK, sw=1, fill=PAPER, rx=6)
        s.text(74, y + 21, a, 12, weight="bold"); s.text(74, y + 38, b, 10, MUTED)
    # pad box
    s.rect(730, 110, 330, 560, c=INK, sw=1.6, fill="#FAFAFA", rx=10)
    s.text(895, 136, "RELAY-6 PAD BOX", 14, anchor="middle", weight="bold")
    s.text(895, 153, "at the rack, 12 V sealed lead-acid", 10, MUTED, anchor="middle")
    blocks = [("ESP32-S3 + SX1262", "Heltec WiFi LoRa 32 V3"), ("Local SAFE/ARM key", "in series with K1 coil"),
              ("Hardware watchdog", "CD74HC123 · ~1 s · AND ARM_EN"), ("K1 changeover relay 40 A", "SAFE: PAD+ → GND · ARMED: PAD+ → +12 V"),
              ("6 fire channels", "IRLB3034-type + TC4427, 15 A fuse each"), ("Ω meter", "≈0.9 mA test current, 2 × ADS1115"),
              ("Ignition timer", "INA228 + 50 A/75 mV shunt"), ("Beacon · siren · wind", "WS2812 mast · 12 V siren · anemometer")]
    for i, (a, b) in enumerate(blocks):
        y = 172 + i * 60
        s.rect(750, y, 290, 48, c=INK, sw=1, fill=PAPER, rx=6)
        s.text(764, y + 21, a, 12, weight="bold"); s.text(764, y + 38, b, 10, MUTED)
    # link
    s.arrow(380, 300, 720, 300, c=ACC2, w=2.2, head=11)
    s.text(550, 288, "ARM-REQ · SELECT · FIRE · HEARTBEAT 4 Hz", 11, ACC2, anchor="middle", weight="bold")
    s.arrow(720, 360, 380, 360, c=OK, w=2.2, head=11)
    s.text(550, 384, "CHALLENGE · Ω per pad · battery · wind · ACK · RSSI", 11, OK, anchor="middle", weight="bold")
    s.rect(420, 420, 260, 150, c=INK, sw=1, fill=PAPER, rx=8)
    s.text(550, 444, "LoRa 915 MHz (US) · licence-free", 11, anchor="middle", weight="bold")
    for i, t in enumerate(["LoRa hardware CRC on every packet", "AES-128-CMAC tag, paired key", "32-bit counter: no replays",
                           "Nonce challenge before ARM", "No heartbeat for 1 s → SAFE"]):
        s.text(436, 470 + i * 19, "• " + t, 10)
    # pads
    for i in range(6):
        x = 760 + (i % 3) * 100; y = 700 + (i // 3) * 46
        s.rect(x, y, 84, 34, c=INK, sw=1, fill=PAPER, rx=5)
        s.text(x + 42, y + 22, f"PAD {i+1}", 11, anchor="middle", weight="bold", font=MONO)
    s.line(895, 670, 895, 698, c=ACC, w=2.4)
    s.text(905, 690, "Powerpole + clip leads, ≤ 5 m", 10, ACC)
    s.text(60, 700, "The controller never carries pyro current. If the controller dies, is switched off,", 11)
    s.text(60, 716, "or goes out of range, the pad box sees no heartbeat and drops to SAFE within ~1 s.", 11)
    s.frame("E-1", "System block diagram")
    return s


# ---------------------------------------------------------------- E-2 power + arming
def e2():
    s = Svg(W, H, "E-2 Pad box power and arming",
            "Battery, fuses, main switch, K1 changeover relay, arm key, watchdog and AND gate.")
    s.text(40, 52, "E-2 · Pad box: power and arming", 22, weight="bold")
    s.text(40, 76, "K1 is shown SAFE (coil off): PAD+ is tied to ground. Three things must all be true to energise it: key in ARM, watchdog fed, firmware ARM_EN.", 12, MUTED)

    # battery and main fuse
    s.battery(90, 200, "BT1", "12 V SLA 7.2 Ah")
    s.wire((90, 200), (90, 140))
    s.fuse(90, 140, 70, label="F0", value="40 A ATC")
    s.wire((160, 140), (250, 140))
    s.dot(250, 140)
    s.text(258, 132, "+BATT", 10, weight="bold")
    # pyro feed to K1 NO
    s.wire((250, 140), (250, 100), (490, 100), (490, 120))
    s.relay_spdt(520, 120, "")
    s.text(262, 236, "K1 · 40/30 A automotive relay", 10, weight="bold")
    s.text(262, 250, "Nilight 50003R · 30 = COM · 87 = NO · 87a = NC", 9, MUTED)
    s.wire((550, 120), (550, 100), (640, 100), (640, 118))
    s.ground(640, 118)
    s.text(650, 112, "SAFE: PAD+ shorted to GND", 10, WARN)
    # PAD+ bus
    s.wire((520, 190), (520, 230))
    s.text(528, 212, "30", 9, MUTED)
    s.line(520, 230, 1040, 230, c=ACC, w=3)
    s.dot(520, 230, c=ACC)
    s.text(700, 222, "PAD+ bus → six red Powerpoles (E-3)", 11, ACC, weight="bold")
    s.text(700, 250, "also VDRV: the TC4427 gate drivers are powered from PAD+,", 10, MUTED)
    s.text(700, 264, "so no gate can turn on unless K1 is ARMED.", 10, MUTED)

    # logic supply
    s.wire((250, 140), (250, 300))
    s.switch(250, 300, 60, vertical=True)
    s.text(272, 326, "S1 MAIN", 10); s.text(272, 339, "30 A toggle", 10, MUTED)
    s.wire((250, 360), (250, 400))
    s.dot(250, 400)
    s.text(258, 396, "+12 SW", 10, weight="bold")
    # buck
    s.wire((250, 400), (140, 400), (140, 430))
    p = s.chip(90, 444, 110, 66, "U1 buck", sub="12 → 5 V 1 A")
    s.wire((140, 430), (140, 444))
    s.wire((145, 510), (145, 540)); s.text(152, 532, "+5 V → Heltec, beacon", 10)
    # key + coil + Q7
    s.wire((250, 400), (420, 400), (420, 420))
    s.switch(420, 420, 60, vertical=True, key=True, label="S2 ARM KEY", value="local SAFE/ARM")
    s.wire((420, 480), (420, 500))
    s.coil(420, 500, "")
    s.text(404, 523, "K1 coil", 10, anchor="end"); s.text(404, 536, "≈150 mA", 9, MUTED, anchor="end")
    s.diode(470, 550, 50, vertical=True, flip=True, label="D7", value="1N4007")
    s.wire((420, 500), (470, 500), (470, 550))
    s.wire((470, 600), (420, 600)); s.dot(420, 600); s.dot(420, 500)
    s.wire((420, 550), (420, 610))
    s.nmos(420, 640, "Q7", "IRLB3034-type")
    s.ground(420, 670)
    # driver U4
    p4 = s.chip(250, 610, 100, 64, "U4", sub="TC4427 ½", right=("OUTA",), left=("INA",))
    s.text(300, 690, "VDD = +12 SW", 9, MUTED, anchor="middle")
    ox, oy = p4[("R", "OUTA")]
    s.wire((ox, oy), (372, oy), (372, 640), (380, 640))
    ix, iy = p4[("L", "INA")]
    s.resistor(216, iy, 46, vertical=True)
    s.text(228, iy + 26, "R7", 9); s.text(228, iy + 37, "100 k", 9, MUTED)
    s.ground(216, iy + 46)
    s.dot(216, iy)
    # AND + watchdog
    pa = s.chip(70, 590, 110, 80, "U3 AND", sub="74HC08 (¼)", left=("A", "B"), right=("Y",))
    yx, yy = pa[("R", "Y")]
    s.wire((yx, yy), (200, yy), (200, iy), (ix, iy))
    ax_, ay_ = pa[("L", "A")]
    s.wire((ax_, ay_), (44, ay_)); s.text(40, ay_ - 6, "ARM_EN", 9, ACC2, anchor="end")
    s.text(40, ay_ + 6, "(GPIO)", 8, ACC2, anchor="end")
    pw = s.chip(70, 720, 150, 60, "U2 watchdog", sub="CD74HC123 (½) · ≈1.0 s", left=("B",), right=("Q",))
    qx, qy = pw[("R", "Q")]
    bx_, by_ = pa[("L", "B")]
    s.wire((qx, qy), (250, qy), (250, 812), (30, 812), (30, by_), (bx_, by_))
    hx, hy = pw[("L", "B")]
    s.wire((hx, hy), (42, hy)); s.text(38, hy + 4, "HB", 9, ACC2, anchor="end", weight="bold")
    s.text(270, 800, "HB = HEARTBEAT GPIO, toggled on each valid packet", 9, ACC2)
    # INA228 shunt in return
    s.wire((90, 260), (90, 300))
    s.resistor(90, 300, 0.1, vertical=True)
    s.rect(70, 300, 40, 18, c=INK, fill="#EEE"); s.text(118, 314, "RS1 50 A / 75 mV", 10)
    s.wire((90, 318), (90, 350)); s.ground(90, 350)
    s.text(118, 328, "INA228 across RS1 (Kelvin)", 9, MUTED)
    s.text(118, 340, "MOSFET sources return here", 9, MUTED)
    # aux box
    s.rect(560, 420, 500, 230, c=INK, sw=1, fill="#FAFAFA", rx=8)
    s.text(576, 444, "Auxiliaries on +12 SW / +5 V", 12, weight="bold")
    aux = ["Siren: Floyd Bell 12 V, low-side MOSFET Q8 from SIREN GPIO",
           "Beacon: WS2812 16-ring on +5 V, data via 74AHCT125 from BEACON GPIO",
           "Anemometer: Adafruit 1733, 12 V supply, 0.4–2.0 V out → ADS1115 #2 AIN3",
           "Battery voltage: INA228 VBUS; K1 sense: PAD+ → 100 k/22 k → GPIO",
           "Charge port: Powerpole pair to BT1 via F0 (charge with S1 OFF)",
           "TVS 1.5KE18A across +12 SW to GND at the board input",
           "All logic grounds meet at the BATT− side of RS1 (one point)"]
    for i, t in enumerate(aux):
        s.text(576, 470 + i * 24, "• " + t, 10.5)
    s.rect(560, 670, 500, 92, c=WARN, sw=1.2, fill="#FFF5F5", rx=8)
    s.text(576, 694, "Interlock summary", 12, WARN, weight="bold")
    s.text(576, 714, "Key OFF → no coil current (hardware).   Watchdog starves → U3 low → Q7 off.", 10.5)
    s.text(576, 732, "Firmware drops ARM_EN → Q7 off.   K1 at rest → PAD+ = 0 V and no gate drive.", 10.5)
    s.text(576, 750, "S1 OFF → everything off; PAD+ still tied to GND through K1 87a.", 10.5)
    s.frame("E-2", "Pad box: power and arming")
    return s


# ---------------------------------------------------------------- E-3 one channel
def e3():
    s = Svg(W, H, "E-3 One pad channel", "Fire switch, fuse, TVS, test current and Ω measurement for pad n.")
    s.text(40, 52, "E-3 · One pad channel (n = 1 … 6, build six)", 22, weight="bold")
    s.text(40, 76, "Low-side switching. The igniter sits between PAD+ (E-2) and PAD−n. Shown SAFE.", 12, MUTED)
    s.line(40, 120, 1060, 120, c=ACC, w=3); s.text(46, 112, "PAD+ bus (E-2)", 11, ACC, weight="bold")
    # connector + igniter
    s.wire((320, 120), (320, 180), (208, 180))
    s.conn(200, 180, "Jn Powerpole", 2)
    s.text(228, 174, "red +", 9, MUTED); s.text(228, 214, "black −", 9, MUTED)
    s.rect(60, 160, 100, 70, c=LIGHT, sw=1, dash="4 3", rx=6)
    s.text(110, 154, "at the rocket", 9, MUTED, anchor="middle")
    s.resistor(80, 210, 60, label="", value="")
    s.text(110, 246, "igniter / e-match", 10, anchor="middle")
    s.wire((80, 210), (75, 210), (75, 180), (192, 180))
    s.wire((140, 210), (192, 200))
    s.wire((208, 200), (280, 200), (280, 260), (420, 260))
    s.dot(420, 260)
    s.text(428, 252, "PAD−n", 11, weight="bold")
    # fuse + mosfet
    s.wire((420, 260), (420, 290))
    s.fuse(420, 290, 50, vertical=True, label="Fn", value="15 A ATC")
    s.wire((420, 340), (420, 370))
    s.nmos(420, 400, "Qn", "UMWIRLB3034")
    s.wire((420, 430), (420, 470))
    s.line(300, 470, 700, 470, c=INK, w=2.4)
    s.text(306, 490, "PYRO RETURN → RS1 → BATT− (E-2)", 10, weight="bold")
    # gate drive
    s.resistor(320, 400, 40, label="Rg", value="10 Ω")
    s.wire((360, 400), (380, 400))
    s.wire((370, 400), (370, 440))
    s.resistor(370, 440, 30, vertical=True)
    s.text(384, 452, "Rgs", 9); s.text(384, 463, "100 k", 9, MUTED)
    s.wire((370, 470), (370, 470))
    pg = s.chip(150, 370, 130, 70, "U5 TC4427 ½", sub="VDD = PAD+ (VDRV)", left=("IN",), right=("OUT",))
    s.wire(pg[("R", "OUT")], (320, pg[("R", "OUT")][1]), (320, 400))
    s.resistor(100, 410, 50, vertical=True, value="100 k")
    s.wire(pg[("L", "IN")], (100, pg[("L", "IN")][1]), (100, 410)); s.dot(100, pg[("L", "IN")][1])
    s.ground(100, 460)
    s.text(24, 404, "FIRE_n", 10, ACC2, weight="bold")
    s.wire((60, 410), (100, 410))
    # TVS
    s.wire((420, 260), (520, 260), (520, 300))
    s.diode(520, 300, 60, vertical=True, kind="tvs", flip=True, label="TVSn", value="SMBJ15A")
    s.wire((520, 360), (520, 470))
    # test current
    s.text(640, 150, "TEST rail (shared by all six)", 10, weight="bold")
    s.wire((620, 160), (620, 175))
    s.rail(620, 160, "3V3")
    s.diode(620, 175, 40, vertical=True, kind="schottky", label="D0", value="1N5817 (one)")
    s.wire((620, 215), (620, 240)); s.dot(620, 240)
    s.text(628, 236, "TEST → ADS #1 AIN0", 10, ACC2)
    s.wire((620, 240), (720, 240))
    s.resistor(720, 240, 80, label="Rtn")
    s.text(782, 226, "3.30 k, 0.1 %", 9, MUTED)
    s.wire((800, 240), (820, 240), (820, 260)); s.dot(820, 260)
    s.wire((520, 260), (820, 260))
    # ADC input
    s.wire((820, 260), (880, 260))
    s.resistor(880, 260, 60, label="Rin", value="10 k")
    s.wire((940, 260), (980, 260)); s.dot(960, 260)
    s.wire((960, 260), (960, 290))
    s.text(976, 296, "Cf 100 nF", 9, MUTED)
    s.line(950, 290, 970, 290, c=INK, w=2); s.line(950, 296, 970, 296, c=INK, w=2)
    s.wire((960, 296), (960, 320)); s.ground(960, 320)
    s.wire((980, 260), (1000, 260))
    s.text(1004, 256, "ADS1115", 10, ACC2, weight="bold"); s.text(1004, 270, "AINx", 10, ACC2)
    s.text(870, 360, "Clamp: BAT54S at AINx to 3V3/GND", 9, MUTED)
    s.text(870, 374, "(PAD−n is +12 V when ARMED)", 9, MUTED)
    # notes
    s.rect(560, 520, 500, 250, c=INK, sw=1, fill="#FAFAFA", rx=8)
    s.text(576, 544, "How the Ω reading works (SAFE only)", 12, weight="bold")
    notes = ["K1 at rest grounds PAD+. TEST ≈ 3.0 V drives",
             "I = (V_TEST − V_PAD−n) / 3.30 k ≈ 0.9 mA through Rtn and the igniter.",
             "R = V_PAD−n / I. Both voltages come from the ADS1115 (±0.256 V range",
             "for PAD−n: 7.8 µV per count ≈ 0.009 Ω at 0.9 mA).",
             "Open igniter: PAD−n rises to TEST → 'OPEN'. Short: R < 0.2 Ω.",
             "The reading includes the clip leads. Arming needs a fresh reading",
             "(< 10 s old) within the window set for that pad (default 0.3–5 Ω).",
             "TeleLaunch uses 100 µA for continuity. 0.9 mA is used here to read Ω;",
             "check it against the no-fire current of the igniters you fly (Stage 6)."]
    for i, t in enumerate(notes):
        s.text(576, 568 + i * 21, t, 10.5)
    s.rect(40, 540, 480, 160, c=INK, sw=1, fill="#FAFAFA", rx=8)
    s.text(56, 564, "Firing", 12, weight="bold")
    for i, t in enumerate(["ARMED: PAD+ = +12 V, VDRV live. FIRE_n high for 1.0 s",
                           "(ripple/salvo timing from firmware) → Qn on → igniter current",
                           "flows PAD+ → igniter → Fn → Qn → RS1 → BATT−.",
                           "INA228 sees the step up and, when the bridge burns open,",
                           "the step down: that interval is the ignition time.",
                           "No step down after 1.0 s → 'NO FIRE' on the controller."]):
        s.text(56, 588 + i * 19, t, 10.5)
    s.frame("E-3", "One pad channel (×6)")
    return s


# ---------------------------------------------------------------- E-4 controller
def e4():
    s = Svg(W, H, "E-4 Controller wiring", "Modules of the controller core and the panel-specific inputs.")
    s.text(40, 52, "E-4 · Controller wiring (all three panels)", 22, weight="bold")
    s.text(40, 76, "Module-level wiring. GPIO numbers are proposals: check each against Heltec's V3 pinout before soldering (Stage 2 gate).", 12, MUTED)
    mcu = s.chip(430, 150, 240, 520, "U1 Heltec WiFi LoRa 32 V3", sub="ESP32-S3 + SX1262 · LoRa on IPEX",
                 left=("3V3", "GND", "SPI SCK", "SPI MOSI", "OLED CS", "OLED DC", "OLED RST", None, "I2C SDA", "I2C SCL", None,
                       "I2S BCLK", "I2S LRC", "I2S DOUT", None, "GPS RX", "GPS TX"),
                 right=("VBAT/5V", "ENC A", "ENC B", "ENC SW", "KEY", "FIRE", "MODE", "COVER", "PAD SEL ×6 *", None,
                        "LED DATA", None, "VBAT ADC", None, "IPEX → SMA"), pitch=26)
    def mod(x, y, w, h, name, sub, pins_from, labels):
        s.rect(x, y, w, h, c=INK, sw=1.2, fill="#F7F7F7", rx=6)
        s.text(x + 10, y + 20, name, 11, weight="bold"); s.text(x + 10, y + 35, sub, 9, MUTED)
    # left modules
    mod(60, 150, 260, 150, "OLED 3.12″ 256×64", "ER-OLEDM032-1 · SSD1322 · 4-wire SPI", None, None)
    for i, n in enumerate(("SCK", "MOSI", "CS", "DC", "RST")):
        y = mcu[("L", ["SPI SCK", "SPI MOSI", "OLED CS", "OLED DC", "OLED RST"][i])][1]
        jx = 400 - i * 10
        s.wire((320, 190 + i * 20), (jx, 190 + i * 20), (jx, y), mcu[("L", ["SPI SCK", "SPI MOSI", "OLED CS", "OLED DC", "OLED RST"][i])])
        s.text(314, 194 + i * 20, n, 9, anchor="end", font=MONO)
    s.text(70, 296, "MONOLITH: second OLED shares SPI, own CS", 9, ACC)
    mod(60, 360, 260, 70, "PN532 NFC (I²C)", "Elechouse V3 · NTAG215 RSO cards", None, None)
    mod(60, 440, 260, 70, "MAX98357A I²S amp", "→ 40 mm 4 Ω speaker", None, None)
    mod(60, 560, 260, 70, "GPS u-blox M10", "UART 9600 · 1 PPS unused", None, None)
    for k, (yy, pin) in enumerate(((385, "I2C SDA"), (405, "I2C SCL"))):
        jx = 370 - k * 10
        s.wire((320, yy), (jx, yy), (jx, mcu[("L", pin)][1]), mcu[("L", pin)])
    for k, (yy, pin) in enumerate(((460, "I2S BCLK"), (475, "I2S LRC"), (490, "I2S DOUT"))):
        jx = 370 - k * 10
        s.wire((320, yy), (jx, yy), (jx, mcu[("L", pin)][1]), mcu[("L", pin)])
    for k, (yy, pin) in enumerate(((585, "GPS RX"), (605, "GPS TX"))):
        jx = 360 - k * 10
        s.wire((320, yy), (jx, yy), (jx, mcu[("L", pin)][1]), mcu[("L", pin)])
    # power chain
    s.rect(60, 690, 600, 110, c=INK, sw=1.2, fill="#F7F7F7", rx=6)
    s.text(72, 712, "Power", 11, weight="bold")
    xs = [80, 190, 300, 420, 540]
    labels = [("USB-C panel", "charge + program"), ("1S charger", "≥1 A, load-share"), ("1S2P 18650", "2 × Molicel P28A"),
              ("E-STOP (NC)", "latching, twist release"), ("5 V boost", "≥2 A → U1 5V, LEDs")]
    for i, (a, b) in enumerate(labels):
        s.rect(xs[i], 726, 100, 54, c=INK if i != 3 else WARN, sw=1, fill=PAPER, rx=4)
        s.text(xs[i] + 50, 748, a, 10, anchor="middle", weight="bold", c=INK if i != 3 else WARN)
        s.text(xs[i] + 50, 764, b, 8.5, MUTED, anchor="middle")
        if i: s.arrow(xs[i] - 10, 753, xs[i], 753, head=6)
    s.wire((640, 753), (690, 753), (690, mcu[("R", "VBAT/5V")][1]), mcu[("R", "VBAT/5V")])
    # right side inputs
    s.rect(760, 150, 300, 330, c=INK, sw=1.2, fill="#F7F7F7", rx=6)
    s.text(772, 172, "Panel inputs (to GND, INPUT_PULLUP)", 11, weight="bold")
    rows = ["Encoder A/B/SW · Bourns PEC11R", "KEY: key switch, removable in OFF", "FIRE: big button (both hands on FLIGHTDECK:",
            "   ARM + FIRE in series → one input)", "MODE: encoder push or toggle", "COVER: microswitch, FIRE cover lifted (HALO)",
            "   / twist collar at 90° (MONOLITH)", "* PAD SEL ×6: through MCP23017 I²C", "   expander (HALO buttons, FLIGHTDECK", "   toggles) or ADS1115 (MONOLITH slide pots)",
            "Debounce in firmware, 20 ms"]
    for i, t in enumerate(rows):
        s.text(772, 196 + i * 24, t, 10)
    s.rect(760, 500, 300, 120, c=INK, sw=1.2, fill="#F7F7F7", rx=6)
    s.text(772, 522, "Lights: one WS2812 chain", 11, weight="bold")
    for i, t in enumerate(["LED DATA → 74AHCT125 (5 V) → 330 Ω →", "  HALO: 6 button pixels + 46-pixel ring",
                           "  FLIGHTDECK: 6 × Stick-8 bars + 6 fire/arm", "  MONOLITH: 6 slot strips + core + columns", "1000 µF across 5 V at the chain start"]):
        s.text(772, 546 + i * 16, t, 9.5)
    for k, (pin, yy) in enumerate((("ENC A", 210), ("KEY", 250), ("FIRE", 270), ("COVER", 330), ("PAD SEL ×6 *", 360))):
        jx = 700 + k * 9
        s.wire(mcu[("R", pin)], (jx, mcu[("R", pin)][1]), (jx, yy), (760, yy))
    s.wire(mcu[("R", "LED DATA")], (748, mcu[("R", "LED DATA")][1]), (748, 540), (760, 540))
    s.text(770, 650, "Antenna: IPEX pigtail to an SMA bulkhead", 9.5, MUTED)
    s.text(770, 664, "in the case wall; 915 MHz ¼-wave whip.", 9.5, MUTED)
    s.frame("E-4", "Controller wiring")
    return s


# ---------------------------------------------------------------- E-5 sequence
def e5():
    s = Svg(W, H, "E-5 Arm and fire sequence", "Message sequence between controller and pad box.")
    s.text(40, 52, "E-5 · Arm and fire, message by message", 22, weight="bold")
    s.text(40, 76, "Every arrow is one LoRa packet: CRC-checked by the radio, CMAC-tagged and counter-numbered by the firmware.", 12, MUTED)
    xa, xb = 200, 680
    for x, n in ((xa, "CONTROLLER"), (xb, "RELAY-6")):
        s.rect(x - 90, 100, 180, 40, c=INK, sw=1.4, fill="#F4F4F4", rx=6)
        s.text(x, 126, n, 13, anchor="middle", weight="bold")
        s.line(x, 140, x, 790, c=LIGHT, w=1.4, dash="6 5")
    msgs = [
        (0, "HEARTBEAT 4 Hz (both ways, all the time)", ACC2, "pad box: watchdog fed"),
        (1, "STATUS: Ω per pad, V batt, wind, RSSI", OK, ""),
        (0, "SELECT pads + mode (SINGLE/SELECT/SALVO/RIPPLE/DRAG)", ACC2, "operator: key ON, pads chosen"),
        (0, "ARM-REQ", ACC2, ""),
        (1, "CHALLENGE nonce N (valid 30 s)", OK, "checks: local key ARM, wind OK, Ω fresh + in window"),
        (0, "ARM { pads, mode, N } + CMAC", ACC2, ""),
        (1, "ARMED ACK { pads, N }", OK, "ARM_EN high → K1 energises, PAD+ live, beacon amber"),
        (0, "COUNT T-5 … T-1 (voice + OLED)", ACC2, "FIRE held: releasing it at any time aborts"),
        (0, "FIRE { pads, mode, N } + CMAC", ACC2, "only while FIRE is held"),
        (1, "FIRED { per pad: lit in t ms / NO FIRE }", OK, "pad box drops ARM_EN 2 s after the last pad"),
        (1, "SAFE", OK, "K1 at rest, beacon green, log written"),
    ]
    y = 180
    for d, t, c, note in msgs:
        if d == 0:
            s.arrow(xa, y, xb, y, c=c, w=1.8, head=9)
        else:
            s.arrow(xb, y, xa, y, c=c, w=1.8, head=9)
        s.text((xa + xb) / 2, y - 8, t, 11, c, anchor="middle", weight="bold")
        if note:
            s.text(xb + 18, y + 4, note, 10, MUTED)
        y += 54
    s.rect(40, 770, 620, 60, c=WARN, sw=1.2, fill="#FFF5F5", rx=6)
    s.text(54, 792, "Abort paths: release FIRE · key OFF (either end) · E-STOP · no heartbeat 1 s ·", 10.5, WARN)
    s.text(54, 810, "nonce expired · bad CMAC or old counter (packet ignored) · wind over limit.", 10.5, WARN)
    s.frame("E-5", "Arm and fire sequence")
    return s


# ---------------------------------------------------------------- E-6 states
def e6():
    s = Svg(W, H, "E-6 Pad box states", "SAFE, CHECKING, ARMED, FIRING and FAULT states with transitions.")
    s.text(40, 52, "E-6 · Pad box states", 22, weight="bold")
    s.text(40, 76, "The pad box is the authority. Any doubt sends it to SAFE; only a complete, fresh, authenticated sequence moves it forward.", 12, MUTED)
    st = {"SAFE": (170, 250, OK), "CHECKING": (520, 250, ACC2), "ARMED": (870, 250, ACC),
          "FIRING": (870, 560, WARN), "FAULT": (170, 560, MUTED)}
    for n, (x, y, c) in st.items():
        s.rect(x - 110, y - 50, 220, 100, c=c, sw=2.2, fill=PAPER, rx=14)
        s.text(x, y - 8, n, 18, c, anchor="middle", weight="bold")
    subs = {"SAFE": "K1 at rest · Ω readings live", "CHECKING": "nonce issued · 30 s", "ARMED": "K1 on · PAD+ live · siren",
            "FIRING": "gates on for 1.0 s per pad", "FAULT": "K1 at rest · latched until reset"}
    for n, t in subs.items():
        x, y, _ = st[n]; s.text(x, y + 18, t, 10, MUTED, anchor="middle")
    s.arrow(280, 235, 410, 235, c=INK, w=1.6); s.text(345, 224, "valid ARM-REQ", 10, anchor="middle")
    s.arrow(410, 270, 280, 270, c=INK, w=1.6); s.text(345, 290, "timeout / check fails", 10, anchor="middle")
    s.arrow(630, 235, 760, 235, c=INK, w=1.6); s.text(695, 224, "ARM + nonce OK", 10, anchor="middle")
    s.arrow(870, 300, 870, 510, c=INK, w=1.6); s.text(880, 410, "valid FIRE", 10)
    s.arrow(760, 530, 282, 300, c=INK, w=1.6, head=10)
    s.text(600, 420, "all pads done + 2 s", 10.5, weight="bold")
    s.path("M870,200 C720,160 320,160 170,200", c=WARN, w=1.6, dash="6 4")
    s.arrow(178, 194, 170, 200, c=WARN, w=1.6, head=9)
    s.text(520, 124, "ANY TIME from ARMED or FIRING: no heartbeat 1 s · key OFF · FIRE released ·", 10.5, WARN, anchor="middle", weight="bold")
    s.text(520, 140, "SAFE command · wind over limit → SAFE", 10.5, WARN, anchor="middle", weight="bold")
    s.arrow(170, 300, 170, 510, c=MUTED, w=1.4, dash="4 3"); s.text(180, 410, "battery < 11.8 V · Ω short ·", 10, MUTED)
    s.text(180, 424, "K1 stuck (PAD+ live while SAFE)", 10, MUTED)
    s.arrow(130, 510, 130, 300, c=MUTED, w=1.4, dash="4 3"); s.text(120, 410, "key cycled", 10, MUTED, anchor="end")
    s.text(120, 424, "OFF → ON", 10, MUTED, anchor="end")
    s.text(40, 760, "Independent of firmware: the watchdog (U2) and the key (S2) drop K1 in hardware, so a crashed or hung ESP32 cannot hold the pad box armed.", 11)
    s.frame("E-6", "Pad box states")
    return s


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "figs"
    os.makedirs(out, exist_ok=True)
    for name, fn in (("E1_system", e1), ("E2_power_arming", e2), ("E3_pad_channel", e3), ("E4_controller", e4),
                     ("E5_sequence", e5), ("E6_states", e6)):
        with open(os.path.join(out, name + ".svg"), "w") as f:
            f.write(fn().render())
        print("wrote", name)


if __name__ == "__main__":
    main()
