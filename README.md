# RELAY-6 wireless launcher

A six-pad, two-way wireless launch system: the **RELAY-6** pad box and three controllers that share one electronics core
(**HALO**, **FLIGHTDECK**, **MONOLITH**). LoRa (licence-free), every packet authenticated, rated for high-power clusters.
Source: https://github.com/tjscientist-labs/RELAY-6 · Write-up: https://model-rocketry.fubsypoly.com/launchers/vol-1/

**Status (2026-11-18): Rev A design, build pack and firmware done. Firmware passes 71 host tests and compiles for all four targets; nothing has been bought, built, flown or run on hardware.**

## Files

| Path | What |
|---|---|
| `DESIGN.md` | Decisions, link protocol, cost estimate, open questions |
| `concepts/` | The concept canvas (claude.ai Design artifact "Wireless Launcher Concepts", private), as files |
| `build_guide.html`, `shop/relay6_build_guide.pdf` | Build guide Rev A: overview, safety, theory, priced parts, 13 build stages with gates, commissioning, field use, troubleshooting, open items, reference tables |
| `shop/relay6_cut_sheets_11x17.pdf` | Cut sheets P-1 to P-9 at 1:1 (tabloid; print at 100 %) and the hole schedules |
| `shop/relay6-launcher-bom.pdf`, `shop/bom.json` | Printable priced BOM (made by `bom_pdf.py` from the fubsypoly website repo; `make_pack.sh` keeps the committed PDF if it is missing) |
| `shop/relay6_build_pack.pdf` | Guide + cut sheets + BOM in print order |
| `shop/dxf/` | DXF cut files (R12, mm; layers CUT / ENGRAVE / NOTE). `README.txt` explains them |
| `figs/` | E-1 … E-6 schematics, V-1 … V-6 renderings, P-1 … P-9 sheets (SVG) |
| `firmware/` | PlatformIO firmware for the pad box and the three controllers; see its README |
| `LICENSE` | GNU GPL v2 |
| `src/` | Generators. `parts.py` is the single geometry source; `bom_data.py` + `bom_padbox.py` the single price source |

## Regenerate

```
python3 -I src/bom_data.py      # prices → shop/bom.json
sh src/make_pack.sh             # schematics, views, cut sheets + DXF, guide, BOM PDF, build pack
```

Needs python3, google-chrome or chromium, pdfunite (poppler-utils). No pip packages.

## Before cutting anything

- Measure the real Apache 3800 and ammo can (inside, lid/base split, corner radius) and edit `src/parts.py`.
- Confirm every red CHECK hole on the cut sheets with the part in hand (60 mm buttons, USB-C extension, Powerpole clip, lever slots, core housing).
- Confirm the C&K key switch releases its key in the OFF position.
- The 0.9 mA igniter test current must be far below the no-fire current of the igniters you use.

## Warning

This is a launch controller for rocket motors and igniters. Rev A has not been built or run on hardware.
Build it, test it with the gates in the build guide and fly it under the NAR / Tripoli safety codes at your own risk.

## Licence

Copyright © 2026 tjscientist. Everything here (firmware, generators, drawings, DXF files, BOM and documents) is
licensed under the **GNU General Public License, version 2 or (at your option) any later version** (`GPL-2.0-or-later`); see `LICENSE`.
It is distributed WITHOUT ANY WARRANTY. Libraries the firmware downloads at build time (RadioLib, U8g2,
Adafruit ADS1X15 / MCP23017 / NeoPixel, robtillaart INA228) keep their own licences.
