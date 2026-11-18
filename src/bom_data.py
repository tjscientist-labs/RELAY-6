#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""The priced bill of materials. One source: this file -> shop/bom.json (+ totals for the guide).

    python3 -I src/bom_data.py

Prices: what each listed page showed on PRICED (USD, unit price at the quantity shown, before tax and shipping).
"est." = an allowance, not a quote. "(listing)" = taken from a search-results tile, product page not opened.
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRICED = "2026-11-18"

DK = lambda pn: ["Digi-Key", f"https://www.digikey.com/en/products/result?keywords={pn}"]
AF = lambda n: ["Adafruit", f"https://www.adafruit.com/product/{n}"]
AMZ = lambda a: ["Amazon", f"https://www.amazon.com/dp/{a}"]


def I(qty, item, spec, mpn, unit, buy, ref="", alts="", tag="Same", note="", optional=False, each=True):
    """unit = unit price (float) or None; qty = number used for the total."""
    return dict(qty=qty, item=item, spec=spec, mpn=mpn, unit=unit, buy=buy, ref=ref, alts=alts, tag=tag, note=note, optional=optional)


CORE = [
    I(1, "Heltec WiFi LoRa 32 V3, 915 MHz, no shell", "ESP32-S3 + SX1262; LoRa on IPEX; 1S Li-ion charger on board", "ZC-153-2-915", 17.90,
      [["Heltec", "https://heltec.org/project/wifi-lora-32-v3/"]], "U1", "LilyGO T3-S3 SX1262 915 MHz (H598) $17.12, lilygo.cc", "Choice"),
    I(1, "OLED 3.12″ 256×64, SSD1322, 4-wire SPI", "ER-OLEDM032-1, choose colour (blue/white/yellow/green) and the 4-wire SPI header option (+$0.59)",
      "ER-OLEDM032-1", 20.84, [["BuyDisplay", "https://www.buydisplay.com/blue-3-2-inch-arduino-raspberry-pi-oled-display-module-256x64-spi"]],
      "DS1", "Newhaven NHD-3.12-25664UCY2 $38.17, Digi-Key", "Choice", "Visual area 78.78 × 21.18; outline 100.50 × 33.50"),
    I(1, "GNSS breakout, u-blox MAX-M10S", "UART/I²C; needs an active GPS antenna on its SMA", "SparkFun GPS-18037", 45.95,
      [["SparkFun", "https://www.sparkfun.com/sparkfun-gnss-receiver-breakout-max-m10s-qwiic.html"]], "U6",
      "SEQURE M10-18 mini GPS with patch antenna, $22.99 (listing), Amazon B0D7Q2ZS8Q", "Choice", "Optional: GPS only feeds the flight log", optional=True),
    I(1, "Active GPS antenna, SMA", "for the MAX-M10S", "", 12.00, [["any"]], "", "", "Choice", "est. — not priced", optional=True),
    I(1, "NFC reader PN532", "I²C; RSO card arming", "Elechouse PN532 V4", 23.90, [["Elechouse", "https://www.elechouse.com/shop/"]], "U5",
      "HiLetgo PN532 V3 $8.99 (listing), Amazon B01I1J17LC", "Choice", "Optional: RSO card arming", optional=True),
    I(10, "NFC cards NTAG215", "CR80 PVC", "GoToTags JKYLMEQ2VG", 0.48, [["GoToTags", "https://store.gototags.com/nfc-pvc-card-ntag215/"]], "",
      "20-pack $7.99 (listing), Amazon B075CL5HGP", "Same", "Minimum order 10", optional=True),
    I(1, "I²S class-D amp MAX98357A", "3 W mono", "Adafruit 3006", 5.95, [AF(3006)], "U4"),
    I(1, "Speaker 40 mm 4 Ω 3 W", "2-pack (one spare)", "Gikfun B01LN8ONG4", 9.28, [AMZ("B01LN8ONG4")], "LS1", "Adafruit 3968 (out of stock)", "Same", each=False),
    I(1, "Rotary encoder with push switch", "24 PPR, detent, 6 mm D shaft, 20 mm", "Bourns PEC11R-4220F-S0024", 2.69, [DK("PEC11R-4220F-S0024")], "ENC",
      "PEC11R-4215F-S0024 (15 mm shaft) $2.95"),
    I(1, "Knob, knurled aluminium, black", "23.5 mm × 15.9, 6 mm bore", "Kilo OEJNI-90-4-7", 12.93, [DK("OEJNI-90-4-7")], "ENC",
      "Adafruit 5527 (20 mm) $2.95", "Choice"),
    I(1, "Key switch, 2-position", "19.30 mm cutout; key removable in one position (confirm it is OFF on the data sheet)", "C&K Y101132C203NQ", 25.16,
      [DK("Y101132C203NQ")], "S1", "Schneider XB5AG21 22 mm, $90.41", "Spec", "Spare key C&K 115140126, $4.32"),
    I(1, "E-stop, 22 mm mushroom, 1 NC", "push to latch, twist to release", "APIELE XB2-01ZS style", 9.99, [AMZ("B079FKJG26")], "S2",
      "IDEC XW1E-BV401MFR $49.17 (27-week lead)", "Choice"),
    I(2, "Li-ion cell 18650, Molicel P28A", "2800 mAh, 35 A", "Molicel P28A", 5.99, [["18650BatteryStore", "https://www.18650batterystore.com/products/molicel-p28a"]],
      "BT1", "IMR Batteries P28A $5.99"),
    I(2, "18650 holder, PCB", "one cell each; wire the two in parallel (1S2P)", "Keystone 1043P", 3.37, [DK("1043P")], "BT1"),
    I(1, "USB-C Li-ion charger, bq24074", "1.0 A charge as shipped; load sharing", "Adafruit 4755", 14.95, [AF(4755)], "U7"),
    I(1, "5 V step-up regulator", "1.3–5 V in, 5 V out", "Pololu U3V40F5 (#4012)", 9.95, [["Pololu", "https://www.pololu.com/product/4012"]], "U8",
      "Pololu S13V20F5 $17.95"),
    I(1, "Antenna 915 MHz tilt whip, SMA", "3 dBi, 903–928 MHz", "Abracon AEACAC195013-S915", 14.72, [DK("AEACAC195013-S915")], "ANT",
      "TE Linx ANT-916-CW-HW-SMA $11.20"),
    I(1, "u.FL to SMA bulkhead cable", "15 cm RG178", "Adafruit 851", 3.95, [AF(851)], "ANT", "", "Spec", "Check the SMA gender matches the antenna"),
    I(1, "USB-C round panel-mount extension", "fits 12–18 mm hole", "Adafruit 6069", 4.50, [AF(6069)], "J1", "Adafruit 4218 (21.5–27 mm hole) $9.95"),
    I(1, "Perma-Proto full-size board", "157 × 51 mm", "Adafruit 1606", 10.95, [AF(1606)], ""),
    I(1, "Level shifter 74AHCT125", "3.3 V → 5 V for the WS2812 data line", "Adafruit 1787", 1.50, [AF(1787)], "U9", "SN74AHCT125N, any distributor", "Same",
      "est. — price not confirmed"),
    I(1, "I/O expander MCP23017", "I²C: pad keys/toggles, MODE, encoder push", "MCP23017-E/SP", 1.60, [DK("MCP23017-E/SP")], "U10", "", "Same",
      "est. — price not confirmed"),
    I(1, "Wire, headers, standoffs, 1000 µF, resistors", "allowance", "", 15.00, [["any"]], "", "", "Choice", "est."),
]

HALO = [
    I(1, "Case, Apache 3800 (black)", "inside 14-7/8 × 10-5/8 × 6-1/8 in", "Harbor Freight 63927", 39.99,
      [["Harbor Freight", "https://www.harborfreight.com/3800-weatherproof-protective-case-large-orange-56766.html"]], "",
      "Pelican 1450 $169.95", "Choice", "Measure inside before cutting (Stage 0)"),
    I(6, "Arcade button 30 mm, translucent clear", "30 mm hole", "Adafruit 3491", 2.50, [AF(3491)], "PB1–PB6"),
    I(2, "NeoPixel mini button PCB, pack of 5", "one inside each pad key", "Adafruit 1612", 4.95, [AF(1612)], "PB1–PB6"),
    I(1, "Arcade button 60 mm, red, LED", "FIRE; hole size from the maker's drawing (CHECK)", "Adafruit 1190", 5.95, [AF(1190)], "PB7",
      "Adafruit 1185 (100 mm) $9.95", "Spec"),
    I(1, "Microswitch, lever", "cover-open sense", "Omron D2F-L", 2.55, [DK("D2F-L")], "SW1", "D2F-FL $2.15"),
    I(1, "Clear cast acrylic 1/4 in, 12 × 12 in, 2-pack", "halo ring (6 mm)", "Amazon B0H33BKNLR", 14.99, [AMZ("B0H33BKNLR")], "P-3", "", "Choice"),
    I(1, "WS2812B strip 60/m, 1 m", "≈46 LEDs for the ring", "BTF-LIGHTING B01CDTE9UC", 8.99, [AMZ("B01CDTE9UC")], "", "Adafruit 2508 (out of stock)"),
    I(1, "Laser-cut panels (P-1, P-2, P-3 cover and blocks)", "3 mm black + 3 mm clear cast acrylic", "SendCutSend", 45.00,
      [["SendCutSend", "https://sendcutsend.com/materials/"]], "P-1–P-3", "Any laser service or a local makerspace", "Choice", "est. — upload the DXFs for a quote"),
]

FLIGHTDECK = [
    I(1, "Case, Apache 3800 (orange)", "inside 14-7/8 × 10-5/8 × 6-1/8 in", "Harbor Freight 56766", 39.99,
      [["Harbor Freight", "https://www.harborfreight.com/3800-weatherproof-protective-case-large-orange-56766.html"]], "", "Pelican 1450 $169.95", "Choice"),
    I(6, "Toggle switch SPST, IP56", "12.2 mm hole, 15/32-32 bushing", "CW Industries GTS447A101HR", 6.87, [DK("GTS447A101HR")], "T1–T6",
      "SparkFun COM-11310 illuminated toggle + cover $4.75", "Choice", "$5.93 each at 10"),
    I(6, "Safety flip cover, red", "fits GTS series", "CW Industries GT-4R", 5.72, [DK("GT-4R")], "T1–T6", "", "Same", "$5.18 each at 10"),
    I(1, "WS2812B strip 60/m, 1 m", "cut six 8-LED status bars", "BTF-LIGHTING B01CDTE9UC", 8.99, [AMZ("B01CDTE9UC")], "B1–B6",
      "Adafruit NeoPixel Stick 1426 $5.95 each (out of stock)"),
    I(1, "Arcade button 60 mm, green, LED", "ARM", "Adafruit 1193", 5.95, [AF(1193)], "PB1", "", "Spec", "hole: CHECK"),
    I(1, "Arcade button 60 mm, red, LED", "FIRE", "Adafruit 1190", 5.95, [AF(1190)], "PB2", "", "Spec", "hole: CHECK"),
    I(1, "Aluminium panel, laser cut + powder coat", "3.18 mm 5052-H32 (P-4)", "SendCutSend", 70.00,
      [["SendCutSend", "https://sendcutsend.com/materials/"]], "P-4", "3 mm black acrylic (as HALO) about $25", "Choice", "est. — quote needed"),
    I(1, "Lid insert + checklist window", "3 mm black + 3 mm clear acrylic (P-5)", "SendCutSend", 25.00,
      [["SendCutSend", "https://sendcutsend.com/materials/"]], "P-5", "", "Choice", "est."),
    I(1, "Hazard-stripe vinyl tape, 2 in", "fire-zone border", "", 8.00, [["any"]], "", "", "Choice", "est."),
]

MONOLITH = [
    I(1, "Case, Apache 3800 (black)", "inside 14-7/8 × 10-5/8 × 6-1/8 in", "Harbor Freight 63927", 39.99,
      [["Harbor Freight", "https://www.harborfreight.com/3800-weatherproof-protective-case-large-orange-56766.html"]], "", "", "Choice"),
    I(6, "Slide potentiometer 60 mm, 10 kΩ linear", "body 75 × 9 × 6.5", "Bourns PTA6043-2015DPB103", 2.23, [DK("PTA6043-2015DPB103")], "RV1–RV6",
      "Same Sky PTNS2-6015M-B10 $2.02", "Same", "$1.86 each at 10"),
    I(1, "Fader caps, 10-pack", "plastic; machine aluminium caps later", "uxcell B07W78R9M3", 6.49, [AMZ("B07W78R9M3")], "RV1–RV6", "", "Spec",
      "(listing) — check the lever size first"),
    I(2, "ADS1115 16-bit ADC breakout", "reads the six levers (4 + 2)", "Adafruit 1085", 14.95, [AF(1085)], "U10", "", "Same"),
    I(1, "Pushbutton 30 mm stainless, blue LED, IP67", "fire core; LED is 12 V (dim at 5 V, or add a small boost)", "Amazon B095WRSWG8", 21.99,
      [AMZ("B095WRSWG8")], "PB1", "Amazon B095PFQG77 $23.99", "Spec"),
    I(1, "Bearing 6810-2RS, 50 × 65 × 7", "twist collar", "uxcell B082PXZLJT (2-pack)", 9.79, [AMZ("B082PXZLJT")], "", "VXB 6810-2RS $24.99", "Same",
      "(listing)"),
    I(1, "Second OLED (same as DS1)", "twin strip", "ER-OLEDM032-1", 20.84,
      [["BuyDisplay", "https://www.buydisplay.com/blue-3-2-inch-arduino-raspberry-pi-oled-display-module-256x64-spi"]], "DS2"),
    I(1, "WS2812B strip 60/m, 1 m", "lever slots + columns", "BTF-LIGHTING B01CDTE9UC", 8.99, [AMZ("B01CDTE9UC")], ""),
    I(1, "Panels: 2 × 3 mm black acrylic (laminated), lid insert", "P-6, P-7", "SendCutSend", 55.00,
      [["SendCutSend", "https://sendcutsend.com/materials/"]], "P-6, P-7", "6.9 mm Delrin, CNC routed (colour not confirmed)", "Choice", "est."),
    I(1, "Printed collar, cam and housing", "PETG, 3D printed", "", 5.00, [["any"]], "", "", "Choice", "est."),
]

PADBOX = []      # filled from the pad-box pricing (see PADBOX list below)


def build(padbox):
    groups = [("Controller core (one per controller)", CORE), ("HALO panel parts", HALO), ("FLIGHTDECK panel parts", FLIGHTDECK),
              ("MONOLITH panel parts", MONOLITH), ("RELAY-6 pad box", padbox)]
    out, sums = [], {}
    for name, items in groups:
        rows, total, opt = [], 0.0, 0.0
        for it in items:
            line = None if it["unit"] is None else it["unit"] * it["qty"]
            if line is not None:
                if it["optional"]:
                    opt += line
                total += line
            price = "price not confirmed" if it["unit"] is None else (f'${it["unit"]:.2f}' + (f' × {it["qty"]} = ${line:.2f}' if it["qty"] != 1 else ""))
            note = price + (" · " + it["note"] if it["note"] else "") + (" · optional" if it["optional"] else "")
            rows.append({"qty": str(it["qty"]), "ref": it["ref"], "item": it["item"], "spec": it["spec"], "mpn": it["mpn"],
                         "alts": it["alts"], "buy": it["buy"], "tag": it["tag"], "note": note, "price": price})
        out.append({"name": name, "items": rows, "note": f"Subtotal ≈ ${total:,.0f}" + (f" (of which optional ${opt:,.0f})" if opt else "")})
        sums[name] = (total, opt)
    core = sums["Controller core (one per controller)"][0]
    pb = sums["RELAY-6 pad box"][0]
    unit = {k: core + sums[g][0] for k, g in (("HALO", "HALO panel parts"), ("FLIGHTDECK", "FLIGHTDECK panel parts"), ("MONOLITH", "MONOLITH panel parts"))}
    totals = {
        "Pad box (RELAY-6)": f"${pb:,.0f}",
        "HALO controller (core + panel)": f"${unit['HALO']:,.0f}",
        "FLIGHTDECK controller": f"${unit['FLIGHTDECK']:,.0f}",
        "MONOLITH controller": f"${unit['MONOLITH']:,.0f}",
        "Pad box + HALO": f"${pb + unit['HALO']:,.0f}",
        "Pad box + all three controllers": f"${pb + sum(unit.values()):,.0f}",
        "Saving per controller without GPS and NFC (optional rows)": f"${sums['Controller core (one per controller)'][1]:,.0f}",
    }
    bom = {
        "title": "RELAY-6 six-pad wireless launcher",
        "subtitle": "Bill of materials: pad box, controller core, HALO / FLIGHTDECK / MONOLITH panels",
        "revision": "A", "date": PRICED,
        "source": "Build guide Rev A, sections 4–6; drawings E-1 to E-6, P-1 to P-9",
        "intro": ("Prices are what each supplier's page showed on " + PRICED + ", one unit, before tax and shipping. "
                  "'est.' is an allowance, not a quote; '(listing)' was read from a search result. The core group is bought once per controller."),
        "tags": {"EOL": "The original part is no longer made: buy the current equivalent listed.", "Same": "Standard part: any equivalent works.", "Choice": "A builder's choice: the listed part is the one drawn.",
                 "Spec": "The spec matters: match it or recheck the drawing and hole size."},
        "groups": out,
        "totals": totals,
    }
    json.dump(bom, open(os.path.join(ROOT, "shop", "bom.json"), "w"), indent=1, ensure_ascii=False)
    for k, v in totals.items():
        print(f"{k:58s} {v}")


if __name__ == "__main__":
    import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import bom_padbox
    bom_padbox_items = bom_padbox.PADBOX
    import bom_data as _bd
    _bd.build(bom_padbox_items)
