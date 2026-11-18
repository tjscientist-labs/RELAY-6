#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Cut sheets P-1 … P-9 (11×17, 1:1 templates) + hole schedules + DXF files, all from parts.py.

    python3 -I src/gen_shop.py          # from the repo root

Writes figs/P*.svg (for the guide, scaled), shop/cut_sheets.html (tabloid, print at 100 %), shop/dxf/*.dxf.
Panel origin for the schedules and DXFs: lower-left corner of the panel, x right, y towards the hinge.
"""
import html, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import parts
from dxf import Dxf

SHEET_W, SHEET_H = 431.8, 279.4      # tabloid landscape, mm
BRIDGE = 8.0                         # HALO ring-slot bridges
REV, DATE = "A", "2026-11-18"


def esc(s):
    return html.escape(str(s))


def annulus_slots(r_in, r_out, n, bridge):
    """Arc slots between n bridges; returns list of (a0, a1) in degrees and the radii."""
    rm = (r_in + r_out) / 2
    gap = math.degrees(bridge / rm)
    step = 360 / n
    return [(i * step + gap / 2 + 45, (i + 1) * step - gap / 2 + 45) for i in range(n)]


def feature_svg(f, X, Y, s=1.0):
    """SVG for one feature; X(x), Y(y) map panel mm (centre origin) to sheet mm."""
    out = []
    col = "#C92A2A" if f.get("check") else "#111"
    k = f["kind"]
    x, y = X(f["x"]), Y(f["y"])
    if k == "hole":
        r = f["d"] / 2
        out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}" fill="none" stroke="{col}" stroke-width="0.3"/>')
        out.append(f'<path d="M{x-r-2:.2f},{y:.2f}H{x+r+2:.2f}M{x:.2f},{y-r-2:.2f}V{y+r+2:.2f}" stroke="#888" stroke-width="0.15"/>')
    elif k in ("rect", "engrave_rect", "slot"):
        w, h = f["w"], f["h"]
        rr = min(w, h) / 2 if k == "slot" else f.get("r", 0)
        dash = ' stroke-dasharray="1.5 1"' if k == "engrave_rect" else ""
        out.append(f'<rect x="{x-w/2:.2f}" y="{y-h/2:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rr:.2f}" fill="none" stroke="{col}" stroke-width="0.3"{dash}/>')
    elif k == "annulus":
        for a0, a1 in annulus_slots(f["r_in"], f["r_out"], f.get("tabs", 4), BRIDGE):
            p = arc_slot_path(x, y, f["r_in"], f["r_out"], a0, a1)
            out.append(f'<path d="{p}" fill="none" stroke="#111" stroke-width="0.3"/>')
        out.append(f'<path d="M{x-4:.2f},{y:.2f}H{x+4:.2f}M{x:.2f},{y-4:.2f}V{y+4:.2f}" stroke="#888" stroke-width="0.15"/>')
    elif k == "note":
        pass
    lab = f["ref"] if not f["ref"].startswith(("M", "SPK")) else ""
    if f["kind"] == "note":
        out.append(f'<text x="{x:.2f}" y="{y:.2f}" font-family="DejaVu Sans" font-size="3" fill="#444" text-anchor="middle">{esc(f["what"])}</text>')
        lab = ""
    if lab and k == "slot":
        out.append(f'<text x="{x:.2f}" y="{y - f["h"]/2 - (2 if f["ref"][0] == "L" else 6):.2f}" font-family="DejaVu Sans" font-size="2.6" fill="{col}" text-anchor="middle">{esc(lab)}</text>')
        lab = ""
    if lab and k != "annulus" and -150 < f["x"] < -60 and f["ref"].startswith("PB"):
        dx = (f.get("d", f.get("w", 8)) / 2) + 1.5
        out.append(f'<text x="{x-dx:.2f}" y="{y-dx*0.6:.2f}" font-family="DejaVu Sans" font-size="3" fill="{col}" text-anchor="end">{esc(lab)}{" CHECK" if f.get("check") else ""}</text>')
        lab = ""
    if lab and k != "annulus":
        dx = (f.get("d", f.get("w", 8)) / 2) + 1.5
        out.append(f'<text x="{x+dx:.2f}" y="{y-dx*0.6:.2f}" font-family="DejaVu Sans" font-size="3" fill="{col}">{esc(lab)}{" CHECK" if f.get("check") else ""}</text>')
    return "".join(out)


def arc_slot_path(cx, cy, r_in, r_out, a0, a1):
    """Closed arc slot with square (radial) ends; sheet coords, y down."""
    def pt(r, a):
        return cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a))
    p0, p1 = pt(r_out, a0), pt(r_out, a1)
    p2, p3 = pt(r_in, a1), pt(r_in, a0)
    big = 1 if (a1 - a0) > 180 else 0
    return (f"M{p0[0]:.2f},{p0[1]:.2f} A{r_out},{r_out} 0 {big} 0 {p1[0]:.2f},{p1[1]:.2f} L{p2[0]:.2f},{p2[1]:.2f} "
            f"A{r_in},{r_in} 0 {big} 1 {p3[0]:.2f},{p3[1]:.2f} Z")


COLX = 384.0     # right-hand column for title, notes and the scale bar


def title_block(code, title, material, scale="1:1"):
    x, w = COLX, SHEET_W - COLX - 4
    t = (f'<rect x="2" y="2" width="{SHEET_W-4}" height="{SHEET_H-4}" fill="none" stroke="#111" stroke-width="0.4"/>'
         f'<line x1="{x-2}" y1="2" x2="{x-2}" y2="{SHEET_H-2}" stroke="#111" stroke-width="0.3"/>'
         f'<text x="{x+2}" y="{SHEET_H-40}" font-family="DejaVu Sans Mono" font-size="9" font-weight="bold">{code}</text>'
         f'<text x="{x+2}" y="{SHEET_H-32}" font-family="DejaVu Sans" font-size="2.6" fill="#444">{scale} · tabloid · mm</text>'
         f'<text x="{x+2}" y="{SHEET_H-26}" font-family="DejaVu Sans" font-size="2.4" fill="#666">Rev {REV} · {DATE}</text>'
         f'<text x="{x+2}" y="{SHEET_H-20}" font-family="DejaVu Sans" font-size="2.4" fill="#666">RELAY-6 wireless launcher</text>')
    words, line, y = title.split(), "", 14
    for wd in words:
        if len(line + " " + wd) > 16:
            t += f'<text x="{x+2}" y="{y}" font-family="DejaVu Sans" font-size="4.2" font-weight="bold">{esc(line.strip())}</text>'; y += 5.5; line = ""
        line += " " + wd
    t += f'<text x="{x+2}" y="{y}" font-family="DejaVu Sans" font-size="4.2" font-weight="bold">{esc(line.strip())}</text>'
    y += 7
    for chunk in wrap(material, 26):
        t += f'<text x="{x+2}" y="{y}" font-family="DejaVu Sans" font-size="2.7" fill="#444">{esc(chunk)}</text>'; y += 3.6
    return t


def wrap(txt, n):
    out, line = [], ""
    for wd in str(txt).split():
        if len(line) + len(wd) + 1 > n:
            out.append(line); line = ""
        line = (line + " " + wd).strip()
    if line: out.append(line)
    return out


def scale_bar():
    x = COLX + 30
    g = f'<rect x="{x}" y="120" width="4" height="100" fill="none" stroke="#111" stroke-width="0.3"/>'
    g += "".join(f'<rect x="{x}" y="{120+i*10}" width="4" height="10" fill="{"#111" if i % 2 == 0 else "#fff"}"/>' for i in range(10))
    for i, chunk in enumerate(wrap("Print check: this bar must measure 100 mm. Print at 100 % (actual size).", 13)):
        g += f'<text x="{COLX+2}" y="{124+i*3.6}" font-family="DejaVu Sans" font-size="2.5">{esc(chunk)}</text>'
    return g


def notes_col(notes):
    g, y = "", 60
    for para, col in ((notes, "#333"), ("Red = CHECK: measure the part before cutting (Stage 0).", "#C92A2A")):
        for chunk in wrap(para, 22):
            g += f'<text x="{COLX+2}" y="{y}" font-family="DejaVu Sans" font-size="2.6" fill="{col}">{esc(chunk)}</text>'; y += 3.4
        y += 3
    return g


def panel_sheet(p, code, title, material, notes=""):
    W, D, R = p["W"], p["D"], p["R"]
    ox, oy = max(4.0, (COLX - 2 - W) / 2), (SHEET_H - D) / 2 + 2
    X = lambda x: ox + W / 2 + x
    Y = lambda y: oy + D / 2 - y
    g = [f'<rect x="{ox:.2f}" y="{oy:.2f}" width="{W:.2f}" height="{D:.2f}" rx="{R:.2f}" fill="#FAFAFA" stroke="#111" stroke-width="0.45"/>']
    for f in p["features"]:
        g.append(feature_svg(f, X, Y))
    g.append(f'<text x="{ox+W/2:.1f}" y="{oy-2:.1f}" font-family="DejaVu Sans" font-size="3" text-anchor="middle" fill="#444">{p.get("top", "HINGE SIDE")} · {W:.1f} × {D:.1f}, corner R{R:.0f}</text>') if oy > 5 else g.append(f'<text x="{ox+W/2:.1f}" y="{oy+4:.1f}" font-family="DejaVu Sans" font-size="3" text-anchor="middle" fill="#444">{p.get("top", "HINGE SIDE")} · {W:.1f} × {D:.1f}, corner R{R:.0f}</text>')
    g.append(f'<text x="{ox+W/2:.1f}" y="{oy+D+4.5:.1f}" font-family="DejaVu Sans" font-size="3" text-anchor="middle" fill="#444">{p.get("bottom", "USER SIDE (front, latches)")}</text>') if oy + D + 5 < SHEET_H - 2 else g.append(f'<text x="{ox+W/2:.1f}" y="{oy+D-2:.1f}" font-family="DejaVu Sans" font-size="3" text-anchor="middle" fill="#444">{p.get("bottom", "USER SIDE (front, latches)")}</text>')
    body = "".join(g) + notes_col(notes or "") + scale_bar() + title_block(code, title, material)
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET_W}mm" height="{SHEET_H}mm" viewBox="0 0 {SHEET_W} {SHEET_H}">' \
           f'<rect width="{SHEET_W}" height="{SHEET_H}" fill="#fff"/>{body}</svg>'


def halo_parts_sheet(h):
    rg = h["ring"]
    cx, cy = 130, 125
    g = []
    g.append(f'<circle cx="{cx}" cy="{cy}" r="{rg["r_out"]}" fill="#EEF8FF" stroke="#111" stroke-width="0.45"/>')
    g.append(f'<circle cx="{cx}" cy="{cy}" r="{rg["r_in"]}" fill="#fff" stroke="#111" stroke-width="0.45"/>')
    g.append(f'<text x="{cx}" y="{cy}" font-family="DejaVu Sans" font-size="3.4" text-anchor="middle">HALO RING</text>')
    g.append(f'<text x="{cx}" y="{cy+5}" font-family="DejaVu Sans" font-size="2.8" text-anchor="middle" fill="#444">6 mm (¼ in) clear cast acrylic · Ø{2*rg["r_out"]:.1f} / Ø{2*rg["r_in"]:.1f}</text>')
    g.append(f'<text x="{cx}" y="{cy+9}" font-family="DejaVu Sans" font-size="2.8" text-anchor="middle" fill="#444">sand the bottom face (diffuser); polish the outer edge</text>')
    # flip cover
    x0, y0 = 260, 60
    g.append(f'<rect x="{x0}" y="{y0}" width="80" height="80" rx="6" fill="#EEF8FF" stroke="#111" stroke-width="0.45"/>')
    g.append(f'<text x="{x0+40}" y="{y0+40}" font-family="DejaVu Sans" font-size="3.4" text-anchor="middle">FLIP COVER</text>')
    g.append(f'<text x="{x0+40}" y="{y0+45}" font-family="DejaVu Sans" font-size="2.8" text-anchor="middle" fill="#444">3 mm clear acrylic, bend 90° along the dashed line</text>')
    g.append(f'<line x1="{x0}" y1="{y0+66}" x2="{x0+80}" y2="{y0+66}" stroke="#1864AB" stroke-width="0.3" stroke-dasharray="2 1"/>')
    for hx in (x0 + 10, x0 + 70):
        g.append(f'<circle cx="{hx}" cy="{y0+74}" r="1.6" fill="none" stroke="#111" stroke-width="0.3"/>')
    # hinge blocks
    for i in range(2):
        bx = 260 + i * 30
        g.append(f'<rect x="{bx}" y="160" width="20" height="12" fill="#F4F4F4" stroke="#111" stroke-width="0.45"/>')
        g.append(f'<circle cx="{bx+10}" cy="166" r="1.6" fill="none" stroke="#111" stroke-width="0.3"/>')
    g.append('<text x="260" y="180" font-family="DejaVu Sans" font-size="2.8" fill="#444">HINGE BLOCKS ×2, 6 mm black acrylic; M3 × 20 pins</text>')
    g.append('<text x="260" y="196" font-family="DejaVu Sans" font-size="2.8" fill="#333">The cover microswitch (COVER input) must close only when the cover</text>')
    g.append('<text x="260" y="200" font-family="DejaVu Sans" font-size="2.8" fill="#333">is fully open: set it by bending the switch lever, not the cover.</text>')
    body = "".join(g) + scale_bar() + title_block("P-3", "HALO ring, flip cover, hinge blocks", "6 mm clear + 3 mm clear + 6 mm black acrylic")
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{SHEET_W}mm" height="{SHEET_H}mm" viewBox="0 0 {SHEET_W} {SHEET_H}"><rect width="{SHEET_W}" height="{SHEET_H}" fill="#fff"/>{body}</svg>'


def schedule_html(p, code, title):
    """One row per feature; repeated patterns (speaker grille, fixing holes) collapse to one row."""
    W, D = p["W"], p["D"]
    groups, order = {}, []
    for f in p["features"]:
        if f["kind"] == "note":
            continue
        if f["kind"] == "hole":
            size = f'Ø{f["d"]:.1f}'
        elif f["kind"] == "annulus":
            size = f'arc slots R{f["r_in"]:.1f}–R{f["r_out"]:.1f}, {f.get("tabs",4)} bridges {BRIDGE:.0f}'
        else:
            size = f'{f["w"]:.1f} × {f["h"]:.1f}'
        key = (f["ref"], f["what"], size) if f["ref"] in ("SPK", "M", "CVR") else (id(f),)
        if key not in groups:
            groups[key] = dict(f=f, size=size, pts=[]); order.append(key)
        groups[key]["pts"].append((f["x"] + W / 2, f["y"] + D / 2))
    rows = []
    for k in order:
        g = groups[k]; f = g["f"]; pts = g["pts"]
        if len(pts) == 1:
            xs, ys = f"{pts[0][0]:.1f}", f"{pts[0][1]:.1f}"
        elif len(pts) <= 4:
            xs = " / ".join(f"{x:.1f}" for x, _ in pts); ys = " / ".join(f"{y:.1f}" for _, y in pts)
        else:
            x0, x1 = min(x for x, _ in pts), max(x for x, _ in pts); y0, y1 = min(y for _, y in pts), max(y for _, y in pts)
            xs, ys = f"{x0:.1f}–{x1:.1f}", f"{y0:.1f}–{y1:.1f}"
        n = f" ×{len(pts)}" if len(pts) > 1 else ""
        rows.append(f'<tr><td class="m">{esc(f["ref"])}{n}</td><td>{esc(f["what"])}</td><td class="m">{xs}</td><td class="m">{ys}</td>'
                    f'<td class="m">{g["size"]}</td><td>{"CHECK" if f.get("check") else ""}</td><td>{"engrave" if f["kind"]=="engrave_rect" else "cut"}</td></tr>')
    return (f'<h3>{code} · {esc(title)} — {W:.1f} × {D:.1f} mm</h3><table><thead><tr><th>Ref</th><th>What</th><th>X</th><th>Y</th>'
            f'<th>Size</th><th></th><th>Op</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')


def panel_dxf(p, path, extra=None):
    d = Dxf()
    W, D, R = p["W"], p["D"], p["R"]
    d.rrect(W / 2, D / 2, W, D, R)
    for f in p["features"]:
        x, y = f["x"] + W / 2, f["y"] + D / 2
        k = f["kind"]
        if k == "hole":
            d.circle(x, y, f["d"] / 2)
        elif k in ("rect", "slot", "engrave_rect"):
            rr = min(f["w"], f["h"]) / 2 if k == "slot" else f.get("r", 0)
            d.rrect(x, y, f["w"], f["h"], rr, layer="ENGRAVE" if k == "engrave_rect" else "CUT")
        elif k == "annulus":
            rc = (f["r_out"] - f["r_in"]) / 2
            rm = (f["r_out"] + f["r_in"]) / 2
            for a0, a1 in annulus_slots(f["r_in"], f["r_out"], f.get("tabs", 4), BRIDGE):
                d.arc(x, y, f["r_out"], a0, a1); d.arc(x, y, f["r_in"], a0, a1)
                for a in (a0, a1):
                    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
                    d.line(x + f["r_in"] * ca, y + f["r_in"] * sa, x + f["r_out"] * ca, y + f["r_out"] * sa)
    d.text(2, -6, 3, f"{p['kind']} Rev {REV} {DATE} mm  CHECK holes: see schedule")
    d.save(path)


def main():
    os.makedirs(os.path.join(ROOT, "shop", "dxf"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "figs"), exist_ok=True)
    h, hl = parts.halo(), parts.lid("halo")
    fd, fdl = parts.flightdeck(), parts.lid("flightdeck")
    mo, mol = parts.monolith(), parts.lid("monolith")
    pf, pl = parts.padbox_front(), parts.padbox_lid()
    sheets = [
        ("P-1", h, "HALO panel", "3 mm black cast acrylic, laser cut", "Ring slots: the clear ring sits on the four bridges, LED strip below shines up through the slots."),
        ("P-2", hl, "HALO lid insert", "3 mm black cast acrylic, laser cut", "OLED window from the front; the module sits behind on M2.5 standoffs."),
        ("P-3", None, None, None, None),
        ("P-4", fd, "FLIGHTDECK panel", "3 mm 5052 aluminium, powder coat, engrave legends (or 3 mm acrylic)", f"ARM to FIRE centres: {fd['two_hand_sep']:.0f} mm."),
        ("P-5", fdl, "FLIGHTDECK lid insert", "3 mm black acrylic", "Checklist window: frosted 3 mm clear behind, edge-lit."),
        ("P-6", mo, "MONOLITH panel", "6 mm black acrylic or acetal (CNC)", "Lever slots: confirm the slide-pot lever width before cutting."),
        ("P-7", mol, "MONOLITH lid insert", "3 mm black acrylic", "Twin OLEDs share SPI; columns are 12 × 70 windows with WS2812 strips behind."),
        ("P-8", pf, "Pad box front face (drill template)", "Template: tape to the can, centre-punch, step drill", "Powerpole: 16.2 square per PP15/30 panel clip, CHECK the clip."),
        ("P-9", pl, "Pad box lid (drill template)", "Template: tape to the can lid", "Mast socket, antenna bulkhead, anemometer gland."),
    ]
    pages, sched = [], []
    for code, p, title, mat, note in sheets:
        if p is None:
            svg = halo_parts_sheet(h)
            dx = Dxf()
            rg = h["ring"]
            dx.circle(rg["r_out"] + 2, rg["r_out"] + 2, rg["r_out"]); dx.circle(rg["r_out"] + 2, rg["r_out"] + 2, rg["r_in"])
            dx.save(os.path.join(ROOT, "shop", "dxf", "P-3_halo_ring.dxf"))
            dc = Dxf(); dc.rrect(40, 40, 80, 80, 6); dc.line(0, 14, 80, 14, "ENGRAVE"); dc.circle(10, 6, 1.6); dc.circle(70, 6, 1.6)
            dc.save(os.path.join(ROOT, "shop", "dxf", "P-3_halo_cover.dxf"))
            db = Dxf()
            for i in range(2):
                db.rrect(10 + i * 30, 6, 20, 12, 0); db.circle(10 + i * 30, 6, 1.6)
            db.save(os.path.join(ROOT, "shop", "dxf", "P-3_halo_hinge_blocks.dxf"))
        else:
            svg = panel_sheet(p, code, title, mat, note)
            panel_dxf(p, os.path.join(ROOT, "shop", "dxf", f"{code}_{p['kind']}.dxf"))
            sched.append(schedule_html(p, code, title))
        open(os.path.join(ROOT, "figs", f"{code.replace('-', '')}_sheet.svg"), "w").write(svg)
        pages.append(f'<section class="sheet">{svg}</section>')
    css = ("@page{size:17in 11in;margin:0}body{margin:0;font-family:'DejaVu Sans',Arial,sans-serif}"
           ".sheet{width:17in;height:11in;page-break-after:always;display:flex;align-items:center;justify-content:center}"
           ".sheet svg{width:431.8mm;height:279.4mm}.sched{padding:14mm 18mm;column-count:2;column-gap:12mm}"
           "h3{font-size:11pt;margin:4mm 0 2mm;break-after:avoid}table{border-collapse:collapse;width:100%;font-size:8pt;break-inside:auto}"
           "th,td{text-align:left;border-bottom:.2mm solid #bbb;padding:.8mm 1.5mm}th{border-bottom:.4mm solid #111}td.m{font-family:'DejaVu Sans Mono',monospace}"
           "tr{break-inside:avoid}h2{font-size:15pt;margin:0 0 3mm;column-span:all}")
    sched_page = (f'<section class="sched"><h2>Hole schedules · origin at the panel\'s lower-left corner (user side, left), '
                  f'x right, y towards the hinge, mm</h2>{"".join(sched)}</section>')
    open(os.path.join(ROOT, "shop", "cut_sheets.html"), "w").write(
        f'<!doctype html><html><head><meta charset="utf-8"><title>RELAY-6 cut sheets Rev {REV}</title><style>{css}</style></head><body>'
        + "".join(pages) + sched_page + "</body></html>")
    open(os.path.join(ROOT, "shop", "dxf", "README.txt"), "w").write(
        "RELAY-6 wireless launcher, Rev A cut files (DXF R12, millimetres).\n"
        "Layers: CUT = cut through; ENGRAVE = mark only (NFC target, hazard border, bend line); NOTE = text, do not cut.\n"
        "Origin: lower-left corner of each panel. Holes marked CHECK on the sheets must be confirmed on the real part first.\n"
        "Made by src/gen_shop.py from src/parts.py; edit parts.py, never the DXF.\n")
    print("sheets", len(pages), "schedules", len(sched))


if __name__ == "__main__":
    main()
