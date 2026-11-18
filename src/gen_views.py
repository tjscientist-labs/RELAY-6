#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Rendered views V-1 … V-6 from parts.py (dimetric, painter's algorithm).

    python3 -I src/gen_views.py figs
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parts
from iso import Scene, P, shade, fit
from sv import Svg, INK, MUTED, ACC

WALL = 9.0
LIT = {"green": "#3BE07A", "amber": "#FF8A1F", "red": "#FF3B3B", "off": "#3A424A", "cyan": "#46E0FF", "blue": "#7FA2FF", "white": "#EEF3FF"}
PAD_STATE = ["green", "green", "amber", "amber", "red", "off"]


def case_base(sc, W, D, H, shell, latch, zp, panel_col, rim=True):
    """Open base tub. Interior x 0..W, y 0..D. Panel top at zp."""
    w = WALL
    # back inner wall face (plane y=D, facing viewer) and left inner wall face (plane x=0)
    sc.face([(0, D, zp), (W, D, zp), (W, D, H), (0, D, H)], shade(shell, 0.55), depth=1e5)
    sc.face([(0, 0, zp), (0, D, zp), (0, D, H), (0, 0, H)], shade(shell, 0.62), depth=1e5 - 1)
    # panel
    sc.face([(0, 0, zp), (W, 0, zp), (W, D, zp), (0, D, zp)], panel_col, "#111", 0.8, depth=9e4)
    # rim strips (top of walls)
    top = shade(shell, 1.08)
    sc.face([(-w, D, H), (W + w, D, H), (W + w, D + w, H), (-w, D + w, H)], top, depth=-1e4)
    sc.face([(-w, -w, H), (0, -w, H), (0, D + w, H), (-w, D + w, H)], top, depth=-1e4 - 1)
    sc.face([(W, -w, H), (W + w, -w, H), (W + w, D + w, H), (W, D + w, H)], top, depth=-1e4 - 2)
    # inner face of the right wall is hidden; inner face of the front wall is hidden; outer front + right faces
    sc.face([(-w, -w, 0), (W + w, -w, 0), (W + w, -w, H), (-w, -w, H)], shade(shell, 0.85), depth=-2e4)
    sc.face([(W + w, -w, 0), (W + w, D + w, 0), (W + w, D + w, H), (W + w, -w, H)], shade(shell, 0.68), depth=-2e4 + 1)
    sc.face([(-w, -w, H), (W + w, -w, H), (W + w, 0, H), (-w, 0, H)], top, depth=-2.1e4)
    # ribs and latches on the front face
    for fx in (0.22, 0.5, 0.78):
        x = -w + (W + 2 * w) * fx
        sc.face([(x - 20, -w - 0.1, H - 26), (x + 20, -w - 0.1, H - 26), (x + 20, -w - 0.1, H + 4), (x - 20, -w - 0.1, H + 4)], latch, shade(latch, 0.6), 0.8, depth=-2.2e4)
    for fx in (0.1, 0.36, 0.64, 0.9):
        x = -w + (W + 2 * w) * fx
        sc.face([(x - 3, -w - 0.2, 8), (x + 3, -w - 0.2, 8), (x + 3, -w - 0.2, H - 40), (x - 3, -w - 0.2, H - 40)], shade(shell, 0.7), depth=-2.15e4)


def case_lid(sc, W, D, H, L, shell, insert_col, tilt=0):
    """Lid standing open above the back edge; its inside faces the viewer. Returns a function mapping
    lid-insert coords (x right, v up from the hinge) to world points."""
    w = WALL
    y0 = D + w
    yb = y0 + max(L, 30)
    zt = H + D + 2 * w
    # back shell box
    sc.face([(-w, y0, H), (W + w, y0, H), (W + w, y0, zt), (-w, y0, zt)], shade(shell, 0.9), depth=2e5)          # front (rim plane)
    sc.face([(W + w, y0, H), (W + w, yb, H), (W + w, yb, zt), (W + w, y0, zt)], shade(shell, 0.66), depth=2e5 - 1)
    sc.face([(-w, y0, zt), (W + w, y0, zt), (W + w, yb, zt), (-w, yb, zt)], shade(shell, 1.06), depth=2e5 - 2)
    # inner recess + insert
    sc.face([(0, y0 - 0.2, H + w), (W, y0 - 0.2, H + w), (W, y0 - 0.2, zt - w), (0, y0 - 0.2, zt - w)], insert_col, "#111", 0.8, depth=2e5 - 3)

    def at(x, v):
        return (x, y0 - 0.4, H + w + v)
    return at


def comp(sc, kind, x, y, z, state="green", k=1.0):
    """Panel component at world (x, y) on a panel whose top is z. All parts share one depth anchor
    (the component's y) and are ordered by height, so a cap is always painted over its bezel."""
    c = LIT.get(state, state)
    A = lambda zt: y - 0.001 * zt
    if kind == "btn30":
        sc.cyl(x, y, z, 17, 3, "#1A1D20", depth=A(z + 3))
        sc.cyl(x, y, z + 3, 13, 7, shade(c, 0.85), top=shade(c, 1.25), depth=A(z + 10))
    elif kind in ("btn60", "btn60g"):
        col = LIT["red"] if kind == "btn60" else LIT["green"]
        sc.cyl(x, y, z, 32, 5, "#16191C", depth=A(z + 5))
        sc.cyl(x, y, z + 5, 27, 10, shade(col, 0.8), top=shade(col, 1.2), depth=A(z + 15))
        sc.cyl(x - 6, y + 6, z + 15.2, 8, 0.3, shade(col, 1.45), top=shade(col, 1.45), stroke="none", depth=A(z + 16))
        if kind == "btn60" and state == "cover":
            pass
    elif kind == "key":
        sc.cyl(x, y, z, 12, 5, "#B9C1C8", top="#D9DFE4", depth=A(z + 5))
        sc.box(x - 2, y - 7, z + 5, 4, 14, 14, "#C9A227", depth=A(z + 19))
    elif kind == "estop":
        sc.cyl(x, y, z, 22, 4, "#E8C930", depth=A(z + 4))
        sc.cyl(x, y, z + 4, 19, 13, "#B3141A", top="#E0262C", depth=A(z + 17))
    elif kind == "enc":
        sc.cyl(x, y, z, 13, 15, "#A9B2BA", top="#D5DBE0", depth=A(z + 15))
    elif kind == "toggle":
        sc.box(x - 10, y - 12, z, 20, 24, 6, "#2A2F34", depth=A(z + 6))
        sc.box(x - 9, y - 16, z + 6, 18, 30, 10, "#C4161C", top="#E8343A", depth=A(z + 16))
    elif kind == "bar":
        sc.face([(x - 23, y - 4, z + 0.3), (x + 23, y - 4, z + 0.3), (x + 23, y + 4, z + 0.3), (x - 23, y + 4, z + 0.3)], c, "#111", 0.6, depth=8e4 - 2)
    elif kind == "nfc":
        sc.face([(x - 25, y - 17, z + 0.2), (x + 25, y - 17, z + 0.2), (x + 25, y + 17, z + 0.2), (x - 25, y + 17, z + 0.2)],
                "#2C333A", "#6B7884", 0.8, depth=8e4 - 2)
    elif kind == "usbc":
        sc.cyl(x, y, z, 7, 3, "#22272C", depth=A(z + 3))
    elif kind == "lever":
        sc.face([(x - 2.5, y - 35, z + 0.2), (x + 2.5, y - 35, z + 0.2), (x + 2.5, y + 35, z + 0.2), (x - 2.5, y + 35, z + 0.2)],
                "#050607", "#000", 0.5, depth=8e4 - 2)
        ly = y + (30 if state != "off" else -30)
        sc.box(x - 9, ly - 6, z, 18, 12, 12, "#C9D1D8", top="#EEF2F5", depth=ly - 0.001 * (z + 12))
    elif kind == "lightslot":
        col = LIT["blue"] if state != "off" else "#2A2F35"
        sc.face([(x - 1.5, y - 35, z + 0.3), (x + 1.5, y - 35, z + 0.3), (x + 1.5, y + 35, z + 0.3), (x - 1.5, y + 35, z + 0.3)],
                col, "none", 0, depth=8e4 - 2)
    elif kind == "core":
        sc.cyl(x, y, z, 34, 2, "#5A646E", depth=A(z + 2))
        sc.cyl(x, y, z + 2, 30, 12, "#9AA4AE", top="#C7CED5", depth=A(z + 14))
        sc.cyl(x, y, z + 14, 15, 6, "#6F8FFF", top="#DDE6FF", depth=A(z + 20))


def ring(sc, x, y, z, r_in, r_out, col):
    n = 64
    outer = [(x + r_out * math.cos(2 * math.pi * i / n), y + r_out * math.sin(2 * math.pi * i / n), z + 6) for i in range(n)]
    inner = [(x + r_in * math.cos(2 * math.pi * i / n), y + r_in * math.sin(2 * math.pi * i / n), z + 6.05) for i in range(n)]
    sc.face(outer, col, shade(col, 0.7), 1.0, depth=8e4)
    sc.face(inner, "#1B2026", "#0A0D10", 0.8, depth=8e4 - 0.5)
    # amber drain segment
    seg = [(x + (r_out + 0.5) * math.cos(math.radians(a)), y + (r_out + 0.5) * math.sin(math.radians(a)), z + 6.1) for a in range(30, 91, 3)]
    seg += [(x + (r_in - 0.5) * math.cos(math.radians(a)), y + (r_in - 0.5) * math.sin(math.radians(a)), z + 6.1) for a in range(90, 29, -3)]
    sc.face(seg, LIT["amber"], "none", 0, depth=8e4 - 0.6)


def hazard(sc, cx, cy, z, w, h):
    stripe = 12
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    # border band 10 mm, drawn as yellow then black diagonal ticks
    for (a, b, c_, d) in ((x0, y0, x1, y0 + 10), (x0, y1 - 10, x1, y1), (x0, y0, x0 + 10, y1), (x1 - 10, y0, x1, y1)):
        sc.face([(a, b, z + 0.2), (c_, b, z + 0.2), (c_, d, z + 0.2), (a, d, z + 0.2)], "#E8C930", "none", 0, depth=8e4 - 1)
    for i in range(int(w / stripe)):
        xa = x0 + i * stripe
        sc.face([(xa, y0, z + 0.25), (xa + 6, y0, z + 0.25), (xa + 6, y0 + 10, z + 0.25), (xa, y0 + 10, z + 0.25)], "#14181C", "none", 0, depth=8e4 - 1.5)
        sc.face([(xa, y1 - 10, z + 0.25), (xa + 6, y1 - 10, z + 0.25), (xa + 6, y1, z + 0.25), (xa, y1, z + 0.25)], "#14181C", "none", 0, depth=8e4 - 1.5)


def lid_items(sc, at, panel, W, D):
    for f in panel["features"]:
        r = f.get("r3d")
        x = f["x"] + W / 2
        v = f["y"] + D / 2           # lid insert: y in panel coords → height up the lid
        if r == "oled":
            w, h = f["w"], f["h"]
            sc.face([at(x - w / 2 - 6, v - h / 2 - 5), at(x + w / 2 + 6, v - h / 2 - 5), at(x + w / 2 + 6, v + h / 2 + 5), at(x - w / 2 - 6, v + h / 2 + 5)],
                    "#3A444D", "#111", 0.6, depth=1.9e5)
            sc.face([at(x - w / 2, v - h / 2), at(x + w / 2, v - h / 2), at(x + w / 2, v + h / 2), at(x - w / 2, v + h / 2)], "#020405", "#000", 0.5, depth=1.89e5)
            for i, frac in enumerate((0.75, 0.45, 0.18)):
                ll = w * (0.85 if i == 1 else 0.6)
                sc.face([at(x - w / 2 + 4, v - h / 2 + h * frac - 1.2), at(x - w / 2 + 4 + ll, v - h / 2 + h * frac - 1.2),
                         at(x - w / 2 + 4 + ll, v - h / 2 + h * frac + 1.2 + (2 if i == 1 else 0)), at(x - w / 2 + 4, v - h / 2 + h * frac + 1.2 + (2 if i == 1 else 0))],
                        "#46E0FF" if panel["kind"] != "flightdeck_lid" else "#C6FF3D", "none", 0, depth=1.88e5)
        elif r == "column":
            w, h = f["w"], f["h"]
            fill = h * (0.25 + 0.12 * (int(f["ref"][1]) % 4))
            sc.face([at(x - w / 2, v - h / 2), at(x + w / 2, v - h / 2), at(x + w / 2, v + h / 2), at(x - w / 2, v + h / 2)], "#0A0C0E", "#22282E", 0.6, depth=1.9e5)
            sc.face([at(x - w / 2 + 2, v - h / 2 + 2), at(x + w / 2 - 2, v - h / 2 + 2), at(x + w / 2 - 2, v - h / 2 + fill), at(x - w / 2 + 2, v - h / 2 + fill)],
                    LIT["blue"], "none", 0, depth=1.89e5)
        elif r == "checklist":
            w, h = f["w"], f["h"]
            sc.face([at(x - w / 2, v - h / 2), at(x + w / 2, v - h / 2), at(x + w / 2, v + h / 2), at(x - w / 2, v + h / 2)], "#EDE6D3", "#111", 0.6, depth=1.9e5)
            for i in range(8):
                yy = v + h / 2 - 20 - i * 17
                sc.face([at(x - w / 2 + 10, yy), at(x + w / 2 - 14, yy), at(x + w / 2 - 14, yy + 2.4), at(x - w / 2 + 10, yy + 2.4)], "#55606A", "none", 0, depth=1.89e5)
        elif f["ref"] == "SPK" and f["kind"] == "hole":
            sc.face([at(x - 1.4, v - 1.4), at(x + 1.4, v - 1.4), at(x + 1.4, v + 1.4), at(x - 1.4, v + 1.4)], "#05070A", "none", 0, depth=1.89e5)


def controller(kind, O, k, labels=True):
    c = parts.CASES[kind]
    panel = {"halo": parts.halo, "flightdeck": parts.flightdeck, "monolith": parts.monolith}[kind]()
    lidp = parts.lid(kind)
    W, D, H = c["w"], c["d"], c["base"] + 10
    zp = H - 9
    sc = Scene(O, k)
    panel_col = {"halo": "#1B2026", "flightdeck": "#1C2127", "monolith": "#202428"}[kind]
    case_base(sc, W, D, H, c["shell"], c["latch"], zp, panel_col)
    at = case_lid(sc, W, D, H, c["lid"], c["shell"], {"halo": "#20262C", "flightdeck": "#1E2328", "monolith": "#15181B"}[kind])
    lid_items(sc, at, lidp, W, D)
    # antenna on the back right of the lid
    ax, ay = W - 10, D + WALL + 10
    sc.box(ax - 3, ay, H + D + 2 * WALL, 6, 6, 150, "#3A444D", bias=-1)
    pad_i = 0
    if kind == "halo":
        rg = panel["ring"]
        ring(sc, rg["x"] + W / 2, rg["y"] + D / 2, zp, rg["r_in"], rg["r_out"], LIT["cyan"])
        # clear flip cover over FIRE, hinged at the back
        fx, fy, zc = rg["x"] + W / 2, rg["y"] + D / 2, zp + 24
        pts = [(fx - 38, fy - 38, zc), (fx + 38, fy - 38, zc), (fx + 38, fy + 38, zc), (fx - 38, fy + 38, zc)]
        sc.face(pts, "#BFE9FF", "#7FB8D6", 1.2, depth=fy - 60, extra='fill-opacity="0.28"')
        for (ax, ay) in ((fx - 38, fy - 38), (fx + 38, fy - 38)):
            sc.face([(ax, ay, zp), (ax, ay, zc), (ax + (1 if ax < fx else -1) * 0.1, ay, zc)], "none", "#7FB8D6", 1.0, depth=fy - 61)
        sc.face([(fx - 38, fy - 38, zp + 0.5), (fx + 38, fy - 38, zp + 0.5), (fx + 38, fy - 38, zc), (fx - 38, fy - 38, zc)],
                "#BFE9FF", "#7FB8D6", 1.0, depth=fy - 61, extra='fill-opacity="0.18"')
    for f in panel["features"]:
        r = f.get("r3d")
        if not r:
            continue
        x, y = f["x"] + W / 2, f["y"] + D / 2
        if r in ("btn30", "toggle", "bar", "lever", "lightslot"):
            idx = int("".join(ch for ch in f["ref"] if ch.isdigit()) or 1) - 1
            st = PAD_STATE[idx % 6]
            if kind == "monolith":
                st = "on" if idx in (0, 1, 2, 4) else "off"
            comp(sc, r, x, y, zp, st, k)
        elif r == "hazard":
            hazard(sc, x, y, zp, f["w"], f["h"])
        elif r != "ring":
            comp(sc, r, x, y, zp, k=k)
    out = sc.render()
    lab = []
    if labels:
        def L(ref, text, bx, by, anchor="start", z=10):
            for f in panel["features"]:
                if f["ref"] == ref:
                    a = P(f["x"] + W / 2, f["y"] + D / 2, zp + z, O=O, k=k)
                    b = (bx, by)
                    lab.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#fff" stroke-width="3" opacity="0.8"/>'
                               f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#111" stroke-width="1"/>'
                               f'<circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="2.4" fill="#333"/>'
                               f'<text x="{b[0] + (5 if anchor == "start" else -5):.1f}" y="{b[1] + 4:.1f}" font-family="DejaVu Sans, Arial, sans-serif" font-size="12" fill="#111" text-anchor="{anchor}">{text}</text>')
                    return
        return out, L, lab, (W, D, H, zp, sc)
    return out, None, lab, (W, D, H, zp, sc)


def controller_fit(kind, box):
    c = parts.CASES[kind]
    W, D, H = c["w"], c["d"], c["base"] + 10
    zt = H + D + 2 * WALL
    pts = [(-WALL, -WALL, 0), (W + WALL, -WALL, 0), (W + WALL, D + WALL + c["lid"], 0), (-WALL, -WALL, H),
           (-WALL, D + WALL, zt), (W + WALL, D + WALL + c["lid"], zt + 150)]
    return fit(pts, box)


def view_controller(kind, title, callouts, fname, desc):
    s = Svg(1100, 820, title, desc)
    O, k = controller_fit(kind, (250, 95, 860, 800))
    body, L, lab, (W, D, H, zp, sc) = controller(kind, O, k)
    s.add(body)
    for args in callouts:
        L(*args)
    s.add("".join(lab))
    # lid callouts
    s.text(40, 46, title, 20, weight="bold")
    s.text(40, 68, desc, 11, MUTED)
    return s


def padbox_scene(O, k, labels=None):
    c = parts.CASES["padbox"]
    W, D, H = c["w"], c["d"], c["base"]
    sc = Scene(O, k)
    col = c["shell"]
    sc.box(0, 0, 0, W, D, H, col, top=shade(col, 1.1))
    sc.box(-6, -4, H, W + 12, D + 8, 22, shade(col, 0.95), top=shade(col, 1.12), bias=-1)
    # handle
    sc.box(W / 2 - 50, D / 2 - 6, H + 22, 100, 12, 8, "#2A2E22", bias=-2)
    # front panel items (front face is plane y=0)
    front = parts.padbox_front()
    for f in front["features"]:
        x = f["x"] + W / 2
        zc = f["y"] + H / 2
        r = f.get("r3d")
        if r == "pp":
            sc.face([(x - 8, -0.3, zc - 8), (x, -0.3, zc - 8), (x, -0.3, zc + 8), (x - 8, -0.3, zc + 8)], "#C4161C", "#111", 0.6, depth=-10)
            sc.face([(x, -0.3, zc - 8), (x + 8, -0.3, zc - 8), (x + 8, -0.3, zc + 8), (x, -0.3, zc + 8)], "#1A1A1A", "#111", 0.6, depth=-10)
        elif r == "led":
            i = int(f["ref"][1]) - 1
            colr = LIT[PAD_STATE[i]]
            pts = [(x + 3 * math.cos(a / 8 * 2 * math.pi), -0.4, zc + 3 * math.sin(a / 8 * 2 * math.pi)) for a in range(8)]
            sc.face(pts, colr, "#111", 0.5, depth=-11)
        elif r == "key":
            pts = [(x + 12 * math.cos(a / 24 * 2 * math.pi), -0.4, zc + 12 * math.sin(a / 24 * 2 * math.pi)) for a in range(24)]
            sc.face(pts, "#C0C7CD", "#111", 0.6, depth=-11)
            sc.face([(x - 2, -0.5, zc - 7), (x + 2, -0.5, zc - 7), (x + 2, -0.5, zc + 7), (x - 2, -0.5, zc + 7)], "#C9A227", "#111", 0.5, depth=-12)
    # lid items
    lidp = parts.padbox_lid()
    zt = H + 22
    for f in lidp["features"]:
        x, y = f["x"] + W / 2, f["y"] + D / 2
        if f["r3d"] == "mast":
            sc.cyl(x, y, zt, 7, 250, "#8E99A4", top="#C9D1D8", bias=-3)
            sc.cyl(x, y, zt + 250, 18, 40, "#FF8A1F", top="#FFC48A", bias=-3.1)
            sc.cyl(x, y, zt + 290, 12, 6, "#2A2E33", bias=-3.2)
        elif f["r3d"] == "ant":
            sc.cyl(x, y, zt, 4, 160, "#2A2E33", top="#3A3F45", bias=-3)
        elif f["r3d"] == "wind":
            sc.cyl(x, y, zt, 5, 140, "#8E99A4", bias=-3)
            hub = zt + 140
            for a in (0, 120, 240):
                ex, ey = x + 55 * math.cos(math.radians(a)), y + 55 * math.sin(math.radians(a))
                sc.raw(-1e6 + 1, f'<line x1="{P(x, y, hub, O=O, k=k)[0]:.1f}" y1="{P(x, y, hub, O=O, k=k)[1]:.1f}" x2="{P(ex, ey, hub, O=O, k=k)[0]:.1f}" y2="{P(ex, ey, hub, O=O, k=k)[1]:.1f}" stroke="#6B7884" stroke-width="{2*k:.1f}"/>')
                sc.cyl(ex, ey, hub - 12, 13, 24, "#D5DBE0", top="#EEF2F5", bias=-1e6)
    # leads from the outputs
    out = sc.render()
    for i in range(6):
        x = -W / 2 + 34 + i * 34 + W / 2
        a = P(x, -1, H / 2 + 16, O=O, k=k)
        b = (a[0] - 40 - i * 18, a[1] + 120 + i * 6)
        out += f'<path d="M{a[0]:.1f},{a[1]:.1f} C{a[0]:.1f},{a[1]+50:.1f} {b[0]+30:.1f},{b[1]-20:.1f} {b[0]:.1f},{b[1]:.1f}" stroke="#7A2E1A" stroke-width="{2.2*k:.1f}" fill="none"/>'
    return out, (W, D, H)


def v_padbox():
    s = Svg(1100, 820, "V-2 RELAY-6 pad box", "The pad box at the rack.")
    c = parts.CASES["padbox"]
    W0, D0, H0 = c["w"], c["d"], c["base"]
    O, k = fit([(-6, -4, 0), (W0 + 6, D0 + 4, 0), (-6, -4, H0), (W0, D0, H0 + 22 + 420), (0, -4, -90)], (330, 100, 800, 790))
    body, (W, D, H) = padbox_scene(O, k)
    s.add(body)
    def L(x, y, z, t, dx, dy, anchor="start"):
        a = P(x, y, z, O=O, k=k); b = (a[0] + dx, a[1] + dy)
        s.add(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#333" stroke-width="0.9"/><circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="2.4" fill="#333"/>')
        s.text(b[0] + (5 if anchor == "start" else -5), b[1] + 4, t, 12, anchor=anchor)
    lid = {f["ref"]: f for f in parts.padbox_lid()["features"]}
    zt = H + 22
    def LA(x, y, z, t, bx, by, anchor="start"):
        a = P(x, y, z, O=O, k=k)
        s.add(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#fff" stroke-width="3" opacity="0.8"/>'
              f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#111" stroke-width="1"/><circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="2.4" fill="#111"/>')
        s.text(bx + (5 if anchor == "start" else -5), by + 4, t, 12, anchor=anchor)
    LA(lid["MAST"]["x"] + W / 2, D / 2, zt + 270, "Beacon: WS2812 ring in a frosted dome", 300, 160, "end")
    LA(lid["WIND"]["x"] + W / 2 + 40, D / 2, zt + 140, "Anemometer (Adafruit 1733)", 830, 170)
    LA(lid["ANT"]["x"] + W / 2, D / 2, zt + 150, "915 MHz antenna, SMA bulkhead", 830, 260)
    LA(W / 2 - 34 + W / 2, 0, H / 2 + 10, "SAFE / ARM key (S2)", 830, 560)
    LA(W, D / 2, H / 2, "Main switch S1 and charge port on this end", 830, 640)
    LA(-W / 2 + 34 + W / 2, 0, H / 2 + 16, "Six Powerpole outputs, red + / black −", 300, 420, "end")
    LA(-W / 2 + 34 + W / 2, 0, H / 2 - 10, "Status LED per pad", 300, 500, "end")
    s.text(40, 46, "V-2 · RELAY-6 pad box", 20, weight="bold")
    s.text(40, 68, "At the rack: mast up, leads out to the pads. Everything that can fire a rocket is inside this can.", 11, MUTED)
    return s


def v_padbox_inside():
    """Plan view of the inside of the can: battery, boards, relay, fuses."""
    c = parts.CASES["padbox"]
    W, D = c["w"], c["d"]
    s = Svg(1100, 700, "V-3 Pad box layout", "Plan view of the inside of the ammo can.")
    sx, ox, oy = 3.4, 110, 140
    def R(x, y, w, h, fill, label, sub="", tc="#111"):
        s.rect(ox + x * sx, oy + y * sx, w * sx, h * sx, c="#111", sw=1.2, fill=fill, rx=4)
        s.text(ox + (x + w / 2) * sx, oy + (y + h / 2) * sx - 2, label, 12, tc, anchor="middle", weight="bold")
        if sub: s.text(ox + (x + w / 2) * sx, oy + (y + h / 2) * sx + 13, sub, 10, MUTED if tc == "#111" else tc, anchor="middle")
    s.rect(ox - 6, oy - 6, W * sx + 12, D * sx + 12, c="#4B5320", sw=4, fill="#F1F2EC", rx=10)
    R(4, 4, 151, 65, "#E3E8F0", "BT1 12 V SLA 7.2 Ah", "151 × 65 × 94, strapped; terminals to the right")
    R(160, 4, 40, 30, "#FFF1E6", "F0 40 A", "≤100 mm")
    R(160, 38, 40, 31, "#FDE2E2", "K1", "40 A changeover")
    R(205, 4, 51, 65, "#EEE", "Power board", "Q1–Q6 on bar, F1–F6")
    R(4, 74, 120, 62, "#E7F5EA", "Logic board", "Heltec V3, U2–U7, ADS ×2, INA228")
    R(128, 74, 40, 62, "#EEE", "RS1", "shunt")
    R(172, 74, 84, 62, "#F4F4F4", "Front panel", "J1–J6 · LEDs · S2")
    s.text(ox + W * sx / 2, oy - 22, "back (hinge side)", 11, MUTED, anchor="middle")
    s.text(ox + W * sx / 2, oy + D * sx + 30, "front: six Powerpole outputs and the key face the flight line", 11, MUTED, anchor="middle")
    s.text(40, 46, "V-3 · Inside the pad box (plan, not to scale between parts)", 20, weight="bold")
    s.text(40, 68, "Heavy current runs along the top edge (battery → F0 → K1 → power board); logic stays at the bottom left, away from it.", 11, MUTED)
    s.text(ox, oy + D * sx + 60, "12 AWG: BT1 → F0 → K1 → PAD+ bus, and the return through RS1.  14 AWG: each pad.  Twisted pairs for the shunt sense leads and every pad lead.", 11)
    return s


def v_family():
    s = Svg(1500, 560, "V-1 The family", "HALO, FLIGHTDECK and MONOLITH controllers with the RELAY-6 pad box.")
    k = 0.62
    xs = [(40, "halo", "HALO"), (420, "flightdeck", "FLIGHTDECK"), (800, "monolith", "MONOLITH")]
    for x, kind, name in xs:
        O, k = controller_fit(kind, (x, 30, x + 340, 510))
        body, *_ = controller(kind, O, k, labels=False)
        s.add(body)
        s.text(x + 170, 540, name, 16, anchor="middle", weight="bold")
    c = parts.CASES["padbox"]
    Op, kp = fit([(-6, -4, 0), (c["w"] + 6, c["d"] + 4, 0), (c["w"], c["d"], c["base"] + 330), (0, -4, -90)], (1190, 60, 1460, 510))
    body, _ = padbox_scene(Op, kp)
    s.add(body)
    s.text(1310, 540, "RELAY-6", 16, anchor="middle", weight="bold")
    return s


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "figs"
    os.makedirs(out, exist_ok=True)
    Lx, Rx = 240, 870
    halo_c = [("S1", "Arm key (S1)", Lx, 470, "end"), ("NFC", "NFC target: RSO card", Lx, 540, "end"),
              ("PB1", "Pad keys, lit by state", Lx, 400, "end"), ("J1", "USB-C: charge, program", Lx, 690, "end"),
              ("RING", "Edge-lit halo ring", Rx, 430, "start"), ("PB7", "FIRE under a clear flip cover", Rx, 500, "start"),
              ("ENC", "Mode encoder", Rx, 570, "start"), ("S2", "E-STOP", Rx, 700, "start")]
    fd_c = [("T1", "Pad toggles under flip covers", Lx, 420, "end"), ("PB1", "ARM (left hand)", Lx, 640, "end"),
            ("S1", "Master key", Lx, 720, "end"), ("B6", "Status bar per pad", Rx, 400, "start"),
            ("ENC", "Mode encoder", Rx, 560, "start"), ("PB2", "FIRE (right hand)", Rx, 640, "start"), ("S2", "E-STOP", Rx, 720, "start")]
    mono_c = [("RV1", "Throttle levers: push to commit", Lx, 440, "end"), ("L1", "Light slot under each lever", Lx, 520, "end"),
              ("J1", "USB-C", Lx, 690, "end"), ("NFC", "NFC target", Lx, 610, "end"),
              ("CORE", "Twist-collar fire core", Rx, 470, "start"), ("ENC", "Mode encoder", Rx, 400, "start"),
              ("S1", "Key", Rx, 620, "start"), ("S2", "E-STOP", Rx, 700, "start")]
    jobs = {
        "V1_family.svg": v_family(),
        "V2_padbox.svg": v_padbox(),
        "V3_padbox_inside.svg": v_padbox_inside(),
        "V4_halo.svg": view_controller("halo", "V-4 · HALO", halo_c, "V4_halo.svg", "Open, lid up: OLED in the lid, the ring and its six keys in the base."),
        "V5_flightdeck.svg": view_controller("flightdeck", "V-5 · FLIGHTDECK", fd_c, "V5_flightdeck.svg", "Open: OLED and checklist in the lid; toggles, status bars and the two-hand fire zone in the base."),
        "V6_monolith.svg": view_controller("monolith", "V-6 · MONOLITH", mono_c, "V6_monolith.svg", "Open: twin OLED strip and firing-order columns in the lid; levers and the fire core in the base."),
    }
    for name, s in jobs.items():
        open(os.path.join(out, name), "w").write(s.render())
        print("wrote", name)


if __name__ == "__main__":
    main()
