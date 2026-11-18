# SPDX-License-Identifier: GPL-2.0-only
"""Single geometry source for the RELAY-6 launcher: cases, panels, holes. Units: mm.

Panel coordinates: origin at the panel centre, x to the right, y towards the hinge (away from the user).
Every hole marked check=True must be measured on the real part before cutting (build guide Stage 0).
gen_views.py (renderings), gen_shop.py (cut sheets + DXF) and gen_guide.py (text) all read this file.
"""

# ---------------------------------------------------------------- cases
# Interior sizes: see CASE_NOTE. w = left-right, d = front-back, base/lid = inside depth.
CASES = {
    "halo": {"name": "Harbor Freight Apache 3800, black (Pelican 1450-size)", "w": 377.8, "d": 269.9, "base": 111, "lid": 44, "r": 14,
             "shell": "#3B4249", "latch": "#E8661A"},
    "flightdeck": {"name": "Harbor Freight Apache 3800, orange", "w": 377.8, "d": 269.9, "base": 111, "lid": 44, "r": 14,
                   "shell": "#E2611A", "latch": "#20262B"},
    "monolith": {"name": "Harbor Freight Apache 3800, black", "w": 377.8, "d": 269.9, "base": 111, "lid": 44, "r": 14,
                 "shell": "#15181B", "latch": "#2A3036"},
    "padbox": {"name": ".50 cal steel ammo can", "w": 260, "d": 140, "base": 175, "lid": 0, "r": 6,
               "shell": "#4B5320", "latch": "#3A3F2A"},
}
CASE_NOTE = ("Apache 3800 interior 14-7/8 × 10-5/8 × 6-1/8 in (377.8 × 269.9 × 155.6 mm) is Harbor Freight's published figure; "
             "it does not give the lid/base split, so 44 / 111 mm is taken from the Pelican 1450 it copies (lid 1.75 in, base 4.37 in). "
             "The corner radius (14 mm) and the ammo-can sizes are estimates. Measure the real cases in Stage 0 and edit parts.py.")

CLEAR = 1.0          # panel-to-case clearance each side
PANEL_T = {"halo": 3.0, "flightdeck": 3.175, "monolith": 6.0}   # MONOLITH: 2 × 3 mm black acrylic laminated

# ---------------------------------------------------------------- hole sizes
# (diameter, check?) — from makers' drawings where published; CHECK where not.
HOLE = {
    "btn30": (30.0, False),      # Adafruit 3491: 30 mm hole
    "btn60": (24.0, True),       # Adafruit 1190/1193 60 mm: hole size only on the maker's drawing — CHECK
    "key": (19.3, False),        # C&K Y101132C203NQ: 19.30 cutout (Digi-Key)
    "estop": (22.5, False),      # 22 mm industrial operator, standard 22.3 +0.4
    "enc": (7.5, False),         # Bourns PEC11R 7 mm bushing
    "toggle": (12.2, False),     # CW GTS447A101HR + GT-4R cover: 12.2 hole (Digi-Key)
    "led": (5.0, False),
    "usbc": (16.0, True),        # Adafruit 6069 round USB-C extension: fits 12–18 holes
    "sma": (6.5, False),         # SMA bulkhead
    "core30": (30.0, False),     # 30 mm stainless IP67 pushbutton: 30 hole
    "bearing": (66.0, True),     # 6810 bearing housing (65 OD + 1)
    "pp_bracket": (0, True),     # Powerpole panel bracket: rectangular, see padbox
}
OLED = {"window": (79.0, 21.5), "outline": (100.5, 33.5), "check": False}  # ER-OLEDM032-1: visual area 78.78 × 21.18, outline 100.50 × 33.50 (BuyDisplay)


def panel_size(kind):
    c = CASES[kind]
    return c["w"] - 2 * CLEAR, c["d"] - 2 * CLEAR, max(c["r"] - CLEAR, 1)


def _ring_positions(n, r, start_deg=90, cx=0, cy=0):
    import math
    return [(cx + r * math.cos(math.radians(start_deg - 360 / n * i)), cy + r * math.sin(math.radians(start_deg - 360 / n * i))) for i in range(n)]


def halo():
    W, D, R = panel_size("halo")
    cx, cy = -20, 0
    rk = min(D / 2 - 32, 104)            # pad-key circle
    ring = (rk - 36, rk - 22)            # inner, outer radius of the halo ring
    f = []
    for i, (x, y) in enumerate(_ring_positions(6, rk, cx=cx, cy=cy)):
        f.append(dict(ref=f"PB{i+1}", what=f"Pad {i+1} key, 30 mm arcade (NeoPixel inside)", kind="hole", d=HOLE["btn30"][0],
                      check=HOLE["btn30"][1], x=x, y=y, r3d="btn30"))
    f.append(dict(ref="PB7", what="FIRE, 60 mm dome", kind="hole", d=HOLE["btn60"][0], check=True, x=cx, y=cy, r3d="btn60"))
    f.append(dict(ref="RING", what="Halo ring opening (ring sits in it)", kind="annulus", r_in=ring[0] - 1, r_out=ring[1] + 1,
                  x=cx, y=cy, r3d="ring", tabs=4))
    f.append(dict(ref="CVR", what="Flip-cover hinge screws, M3", kind="hole", d=3.2, x=cx - 30, y=cy + 44, r3d=None))
    f.append(dict(ref="CVR", what="Flip-cover hinge screws, M3", kind="hole", d=3.2, x=cx + 30, y=cy + 44, r3d=None))
    f.append(dict(ref="SW1", what="Cover microswitch lever slot", kind="slot", w=6, h=14, x=cx + 38, y=cy + 18, r3d=None))
    lx = -W / 2 + 34
    f.append(dict(ref="S1", what="Arm key switch", kind="hole", d=HOLE["key"][0], check=HOLE["key"][1], x=lx, y=D / 2 - 40, r3d="key"))
    f.append(dict(ref="NFC", what="NFC target (engrave only)", kind="engrave_rect", w=50, h=34, x=lx + 4, y=0, r3d="nfc"))
    f.append(dict(ref="J1", what="USB-C panel extension", kind="hole", d=HOLE["usbc"][0], check=True, x=lx, y=-D / 2 + 34, r3d="usbc"))
    rx = W / 2 - 36
    f.append(dict(ref="ENC", what="Mode encoder", kind="hole", d=HOLE["enc"][0], x=rx, y=D / 2 - 42, r3d="enc"))
    f.append(dict(ref="S2", what="E-STOP, 22 mm", kind="hole", d=HOLE["estop"][0], x=rx, y=-D / 2 + 44, r3d="estop"))
    for k in range(4):
        f.append(dict(ref="M", what="Panel fixing, M4 to case cleats", kind="hole", d=4.3, x=(-1) ** k * (W / 2 - 8) * (1 if k < 2 else 1),
                      y=(D / 2 - 8) * (1 if k in (0, 3) else -1), r3d=None))
    return dict(kind="halo", W=W, D=D, R=R, t=PANEL_T["halo"], features=f, ring=dict(r_in=ring[0], r_out=ring[1], x=cx, y=cy, t=6))


def flightdeck():
    W, D, R = panel_size("flightdeck")
    f = []
    n = 6
    span = W - 70
    xs = [-span / 2 + span * (i + 0.5) / n for i in range(n)]
    yt = D / 2 - 92
    for i, x in enumerate(xs):
        f.append(dict(ref=f"T{i+1}", what=f"Pad {i+1} toggle with flip cover", kind="hole", d=HOLE["toggle"][0], check=HOLE["toggle"][1],
                      x=x, y=yt, r3d="toggle"))
        f.append(dict(ref=f"B{i+1}", what=f"Pad {i+1} status window (NeoPixel Stick-8 behind)", kind="rect", w=46, h=8, r=2,
                      x=x, y=D / 2 - 30, r3d="bar"))
        f.append(dict(ref=f"T{i+1}a", what="Toggle anti-rotation", kind="hole", d=3.0, x=x, y=yt + 13, r3d=None))
    zy = -D / 2 + 62
    f.append(dict(ref="PB1", what="ARM, 60 mm dome (green)", kind="hole", d=HOLE["btn60"][0], check=True, x=-W / 2 + 62, y=zy, r3d="btn60g"))
    f.append(dict(ref="PB2", what="FIRE, 60 mm dome (red)", kind="hole", d=HOLE["btn60"][0], check=True, x=W / 2 - 62, y=zy, r3d="btn60"))
    f.append(dict(ref="S1", what="Master key switch", kind="hole", d=HOLE["key"][0], check=HOLE["key"][1], x=-70, y=zy, r3d="key"))
    f.append(dict(ref="ENC", what="Mode encoder", kind="hole", d=HOLE["enc"][0], x=0, y=zy + 6, r3d="enc"))
    f.append(dict(ref="S2", what="E-STOP, 22 mm", kind="hole", d=HOLE["estop"][0], x=70, y=zy, r3d="estop"))
    f.append(dict(ref="HZ", what="Hazard-stripe border (vinyl), engrave guide", kind="engrave_rect", w=W - 40, h=104, x=0, y=zy, r3d="hazard"))
    f.append(dict(ref="J1", what="USB-C panel extension", kind="hole", d=HOLE["usbc"][0], check=True, x=0, y=D / 2 - 140, r3d="usbc"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            f.append(dict(ref="M", what="Panel fixing, M4 to case cleats", kind="hole", d=4.3, x=sx * (W / 2 - 8), y=sy * (D / 2 - 8), r3d=None))
    return dict(kind="flightdeck", W=W, D=D, R=R, t=PANEL_T["flightdeck"], features=f, two_hand_sep=W - 124)


def monolith():
    W, D, R = panel_size("monolith")
    f = []
    xs = [-W / 2 + 46 + i * 36 for i in range(6)]
    for i, x in enumerate(xs):
        f.append(dict(ref=f"RV{i+1}", what=f"Pad {i+1} lever slot (60 mm slide pot below)", kind="slot", w=5, h=70, x=x, y=4, r3d="lever",
                      check=True))
        f.append(dict(ref=f"L{i+1}", what=f"Pad {i+1} light slot (WS2812 below, diffuser)", kind="slot", w=3, h=70, x=x + 10, y=4, r3d="lightslot"))
    cx, cy = W / 2 - 95, 22
    f.append(dict(ref="CORE", what="Fire core: 6810 bearing housing, 30 mm button in its bore", kind="hole", d=HOLE["bearing"][0], check=True,
                  x=cx, y=cy, r3d="core"))
    f.append(dict(ref="S1", what="Key switch", kind="hole", d=HOLE["key"][0], check=HOLE["key"][1], x=cx - 40, y=-D / 2 + 46, r3d="key"))
    f.append(dict(ref="S2", what="E-STOP, 22 mm", kind="hole", d=HOLE["estop"][0], x=cx + 40, y=-D / 2 + 46, r3d="estop"))
    f.append(dict(ref="ENC", what="Mode encoder", kind="hole", d=HOLE["enc"][0], x=cx + 62, y=cy + 70, r3d="enc"))
    f.append(dict(ref="J1", what="USB-C panel extension", kind="hole", d=HOLE["usbc"][0], check=True, x=-W / 2 + 40, y=-D / 2 + 30, r3d="usbc"))
    f.append(dict(ref="NFC", what="NFC target (engrave only)", kind="engrave_rect", w=50, h=34, x=-W / 2 + 140, y=-D / 2 + 40, r3d="nfc"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            f.append(dict(ref="M", what="Panel fixing, M4 to case cleats", kind="hole", d=4.3, x=sx * (W / 2 - 8), y=sy * (D / 2 - 8), r3d=None))
    return dict(kind="monolith", W=W, D=D, R=R, t=PANEL_T["monolith"], features=f)


def lid(kind):
    """Lid insert panel (3 mm), coordinates as the base panel with the lid folded down onto it (x same, y mirrored)."""
    W, D, R = panel_size(kind)
    f = []
    ow, oh = OLED["window"]
    if kind == "monolith":
        for x in (-48, 48):
            f.append(dict(ref="OLED", what="OLED window 3.12″ (twin)", kind="rect", w=ow, h=oh, r=1, x=x, y=D / 2 - 50, r3d="oled", check=True))
        for i in range(6):
            f.append(dict(ref=f"C{i+1}", what="Firing-order light column", kind="rect", w=12, h=70, r=2, x=-75 + i * 30, y=-10, r3d="column"))
    else:
        f.append(dict(ref="OLED", what="OLED window 3.12″", kind="rect", w=ow, h=oh, r=1, x=-40 if kind == "flightdeck" else 0, y=D / 2 - 55,
                      r3d="oled", check=True))
    sx = 0 if kind != "flightdeck" else -40
    for i in range(-3, 4):
        for j in range(-1, 2):
            f.append(dict(ref="SPK", what="Speaker grille, 40 mm", kind="hole", d=3.0, x=sx + i * 6, y=-D / 2 + 50 + j * 6, r3d=None))
    if kind == "flightdeck":
        f.append(dict(ref="CHK", what="Checklist card window", kind="rect", w=120, h=160, r=4, x=W / 2 - 90, y=0, r3d="checklist"))
    for sx2 in (-1, 1):
        for sy in (-1, 1):
            f.append(dict(ref="M", what="Lid insert fixing, M3", kind="hole", d=3.4, x=sx2 * (W / 2 - 8), y=sy * (D / 2 - 8), r3d=None))
    return dict(kind=kind + "_lid", W=W, D=D, R=R, t=3.0, features=f)


def padbox_front():
    """Front face of the ammo can (the long side facing the flight line), outside view; origin at the face centre."""
    c = CASES["padbox"]
    W, H = c["w"], c["base"]
    f = []
    for i in range(6):
        x = -W / 2 + 34 + i * 34
        f.append(dict(ref=f"J{i+1}", what=f"Pad {i+1} Powerpole pair (panel clip)", kind="rect", w=16.2, h=16.2, r=0.5, x=x, y=16,
                      check=True, r3d="pp"))
        f.append(dict(ref=f"J{i+1}s", what="Clip screws, 4-40", kind="hole", d=3.0, x=x, y=34, r3d=None))
        f.append(dict(ref=f"D{i+1}", what=f"Pad {i+1} status LED", kind="hole", d=HOLE["led"][0], x=x, y=-10, r3d="led"))
    f.append(dict(ref="S2", what="SAFE / ARM key", kind="hole", d=HOLE["key"][0], check=HOLE["key"][1], x=W / 2 - 30, y=-45, r3d="key"))
    f.append(dict(ref="S1", what="S1 main switch + charge port: right end panel", kind="note", x=-30, y=-60, r3d=None))
    return dict(kind="padbox_front", W=W, D=H, R=4, t=1.2, features=f, top="TOP (lid)", bottom="BOTTOM")


def padbox_lid():
    c = CASES["padbox"]
    W, D = c["w"], c["d"]
    f = [dict(ref="MAST", what="Beacon mast socket, 1/2″ bulkhead", kind="hole", d=22.5, x=-W / 2 + 40, y=0, r3d="mast", check=True),
         dict(ref="ANT", what="Antenna SMA bulkhead", kind="hole", d=HOLE["sma"][0], x=W / 2 - 40, y=0, r3d="ant"),
         dict(ref="WIND", what="Anemometer post, PG9 gland", kind="hole", d=15.5, x=0, y=0, r3d="wind", check=True)]
    return dict(kind="padbox_lid", W=W, D=D, R=4, t=1.2, features=f, top="BACK", bottom="FRONT (outputs side)")


def all_panels():
    return [halo(), lid("halo"), flightdeck(), lid("flightdeck"), monolith(), lid("monolith"), padbox_front(), padbox_lid()]
