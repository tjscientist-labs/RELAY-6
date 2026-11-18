# SPDX-License-Identifier: GPL-2.0-or-later
"""Small SVG drafting kit for the wireless-launcher drawings (schematics, views, shop sheets).

Print style: white paper, black linework, one accent. Units are SVG px unless a function says mm.
Every generator in this folder imports from here so the drawings share one look.
"""
import html, math

INK = "#111"
MUTED = "#555"
LIGHT = "#999"
ACC = "#D9480F"        # launcher orange (print-safe)
ACC2 = "#1864AB"       # signal blue
OK = "#2B8A3E"
WARN = "#C92A2A"
PAPER = "#fff"
FONT = "DejaVu Sans, Arial, sans-serif"
MONO = "DejaVu Sans Mono, monospace"


def esc(s):
    return html.escape(str(s), quote=True)


class Svg:
    """Accumulates elements; .render() returns a standalone <svg>."""

    def __init__(self, w, h, title, desc=""):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.el = []
        self.defs = []

    def add(self, s):
        self.el.append(s)
        return self

    # ---- primitives ----
    def line(self, x1, y1, x2, y2, c=INK, w=1.4, dash=None, extra=""):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        return self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{c}" stroke-width="{w}"{d} stroke-linecap="round" {extra}/>')

    def path(self, d, c=INK, w=1.4, fill="none", extra="", dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        return self.add(f'<path d="{d}" stroke="{c}" stroke-width="{w}" fill="{fill}" stroke-linejoin="round" stroke-linecap="round"{da} {extra}/>')

    def poly(self, pts, c=INK, w=1.4, fill="none", close=False, extra=""):
        tag = "polygon" if close else "polyline"
        p = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        return self.add(f'<{tag} points="{p}" stroke="{c}" stroke-width="{w}" fill="{fill}" stroke-linejoin="round" {extra}/>')

    def wire(self, *pts, c=INK, w=1.4):
        return self.poly(pts, c=c, w=w)

    def rect(self, x, y, w, h, c=INK, sw=1.4, fill="none", rx=0, dash=None, extra=""):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        return self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" stroke="{c}" stroke-width="{sw}" fill="{fill}"{d} {extra}/>')

    def circle(self, cx, cy, r, c=INK, sw=1.4, fill="none", extra=""):
        return self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" stroke="{c}" stroke-width="{sw}" fill="{fill}" {extra}/>')

    def text(self, x, y, s, size=11, c=INK, anchor="start", weight="normal", font=FONT, italic=False, extra=""):
        st = ' font-style="italic"' if italic else ""
        lines = str(s).split("\n")
        if len(lines) == 1:
            return self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" fill="{c}" text-anchor="{anchor}" font-weight="{weight}"{st} {extra}>{esc(s)}</text>')
        out = f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" fill="{c}" text-anchor="{anchor}" font-weight="{weight}"{st} {extra}>'
        for i, ln in enumerate(lines):
            out += f'<tspan x="{x:.1f}" dy="{0 if i == 0 else size * 1.25:.1f}">{esc(ln)}</tspan>'
        return self.add(out + "</text>")

    def dot(self, x, y, c=INK):
        return self.circle(x, y, 2.6, c=c, sw=0, fill=c)

    def arrow(self, x1, y1, x2, y2, c=INK, w=1.4, head=8, both=False, dash=None):
        self.line(x1, y1, x2, y2, c=c, w=w, dash=dash)
        def hd(xa, ya, xb, yb):
            a = math.atan2(yb - ya, xb - xa)
            p1 = (xb - head * math.cos(a - 0.4), yb - head * math.sin(a - 0.4))
            p2 = (xb - head * math.cos(a + 0.4), yb - head * math.sin(a + 0.4))
            self.poly([p1, (xb, yb), p2], c=c, w=w, fill=c, close=True)
        hd(x1, y1, x2, y2)
        if both:
            hd(x2, y2, x1, y1)
        return self

    # ---- schematic symbols (pins on a 10 px grid; horizontal unless noted) ----
    def resistor(self, x, y, length=60, vertical=False, label="", value="", c=INK):
        """Zig-zag resistor from (x,y) along +x (or +y)."""
        n, amp = 6, 6
        body = length * 0.6
        lead = (length - body) / 2
        pts = [(0, 0), (lead, 0)]
        for i in range(n):
            pts.append((lead + body * (i + 0.5) / n, amp if i % 2 == 0 else -amp))
        pts += [(lead + body, 0), (length, 0)]
        if vertical:
            pts = [(x + b, y + a) for a, b in pts]
            self.poly(pts, c=c)
            if label: self.text(x + 12, y + length / 2 - 2, label, 10)
            if value: self.text(x + 12, y + length / 2 + 11, value, 10, MUTED)
        else:
            pts = [(x + a, y + b) for a, b in pts]
            self.poly(pts, c=c)
            if label: self.text(x + length / 2, y - 11, label, 10, anchor="middle")
            if value: self.text(x + length / 2, y + 20, value, 10, MUTED, anchor="middle")
        return self

    def diode(self, x, y, length=50, vertical=False, label="", value="", kind="std", c=INK, flip=False):
        """Anode at (x,y), cathode at the far end (flip swaps)."""
        mid = length / 2
        s = 8
        if not vertical:
            d = -1 if flip else 1
            ax, cx = (x, x + length) if not flip else (x + length, x)
            self.line(x, y, x + length, y, c=c)
            tx = x + mid
            self.poly([(tx - s * d, y - s), (tx - s * d, y + s), (tx + s * d * 0.9, y)], c=c, fill=c, close=True)
            self.line(tx + s * d * 0.9, y - s, tx + s * d * 0.9, y + s, c=c, w=1.8)
            if kind == "schottky":
                self.path(f"M{tx + s*d*0.9 - 3*d},{y - s} L{tx + s*d*0.9 - 3*d},{y - s - 3}" , c=c)
                self.path(f"M{tx + s*d*0.9 + 3*d},{y + s} L{tx + s*d*0.9 + 3*d},{y + s + 3}", c=c)
            if kind == "tvs":
                self.path(f"M{tx + s*d*0.9},{y - s} l{-4*d},{-4}", c=c)
                self.path(f"M{tx + s*d*0.9},{y + s} l{4*d},{4}", c=c)
            if label: self.text(tx, y - 13, label, 10, anchor="middle")
            if value: self.text(tx, y + 22, value, 10, MUTED, anchor="middle")
        else:
            d = -1 if flip else 1
            self.line(x, y, x, y + length, c=c)
            ty = y + mid
            self.poly([(x - s, ty - s * d), (x + s, ty - s * d), (x, ty + s * d * 0.9)], c=c, fill=c, close=True)
            self.line(x - s, ty + s * d * 0.9, x + s, ty + s * d * 0.9, c=c, w=1.8)
            if kind == "tvs":
                self.path(f"M{x - s},{ty + s*d*0.9} l{-4},{4*d}", c=c)
                self.path(f"M{x + s},{ty + s*d*0.9} l{4},{-4*d}", c=c)
            if kind == "schottky":
                self.path(f"M{x - s},{ty + s*d*0.9} l0,{-3*d}", c=c)
                self.path(f"M{x + s},{ty + s*d*0.9} l0,{3*d}", c=c)
            if label: self.text(x + 13, ty - 1, label, 10)
            if value: self.text(x + 13, ty + 12, value, 10, MUTED)
        return self

    def ground(self, x, y, c=INK):
        self.line(x, y, x, y + 8, c=c)
        for i, hw in enumerate((10, 6.5, 3)):
            self.line(x - hw, y + 8 + i * 4, x + hw, y + 8 + i * 4, c=c)
        return self

    def rail(self, x, y, label, c=INK, up=True):
        """Supply arrow/bar label pointing up (pin at x,y)."""
        dy = -1 if up else 1
        self.line(x, y, x, y + 10 * dy, c=c)
        self.line(x - 9, y + 10 * dy, x + 9, y + 10 * dy, c=c, w=1.8)
        self.text(x, y + (10 * dy) + (-5 if up else 15), label, 10, c, anchor="middle", weight="bold")
        return self

    def fuse(self, x, y, length=50, vertical=False, label="", value="", c=INK):
        if not vertical:
            self.line(x, y, x + length, y, c=c)
            self.rect(x + length * 0.2, y - 6, length * 0.6, 12, c=c, fill=PAPER)
            self.line(x + length * 0.2, y, x + length * 0.8, y, c=c, w=1)
            if label: self.text(x + length / 2, y - 11, label, 10, anchor="middle")
            if value: self.text(x + length / 2, y + 20, value, 10, MUTED, anchor="middle")
        else:
            self.line(x, y, x, y + length, c=c)
            self.rect(x - 6, y + length * 0.2, 12, length * 0.6, c=c, fill=PAPER)
            self.line(x, y + length * 0.2, x, y + length * 0.8, c=c, w=1)
            if label: self.text(x + 12, y + length / 2 - 2, label, 10)
            if value: self.text(x + 12, y + length / 2 + 11, value, 10, MUTED)
        return self

    def battery(self, x, y, label="", value="", c=INK):
        """Vertical battery, + at top pin (x,y), - at (x,y+60)."""
        self.line(x, y, x, y + 22, c=c)
        self.line(x - 16, y + 22, x + 16, y + 22, c=c, w=2)
        self.line(x - 9, y + 28, x + 9, y + 28, c=c, w=3)
        self.line(x - 16, y + 34, x + 16, y + 34, c=c, w=2)
        self.line(x - 9, y + 40, x + 9, y + 40, c=c, w=3)
        self.line(x, y + 40, x, y + 60, c=c)
        self.text(x - 22, y + 20, "+", 12, anchor="middle", weight="bold")
        if label: self.text(x + 22, y + 28, label, 10)
        if value: self.text(x + 22, y + 41, value, 10, MUTED)
        return self

    def switch(self, x, y, length=50, vertical=False, label="", value="", key=False, nc=False, c=INK):
        """SPST, pin a at (x,y), pin b at the far end."""
        if not vertical:
            a, b = (x + 12, y), (x + length - 12, y)
            self.line(x, y, a[0], y, c=c); self.line(b[0], y, x + length, y, c=c)
            self.dot(*a, c=c); self.circle(b[0], y, 2.6, c=c, fill=PAPER)
            if nc:
                self.line(a[0], y, b[0] + 2, y + 4, c=c)
            else:
                self.line(a[0], y, b[0] - 2, y - 14, c=c)
            if key:
                kx, ky = (a[0] + b[0]) / 2, y - 22
                self.circle(kx, ky, 4, c=c); self.line(kx + 4, ky, kx + 14, ky, c=c); self.line(kx + 10, ky, kx + 10, ky + 4, c=c)
                self.line(kx, ky + 4, kx, y - 8, c=c, dash="2 2")
            if label: self.text(x + length / 2, y + 20, label, 10, anchor="middle")
            if value: self.text(x + length / 2, y + 32, value, 10, MUTED, anchor="middle")
        else:
            a, b = (x, y + 12), (x, y + length - 12)
            self.line(x, y, x, a[1], c=c); self.line(x, b[1], x, y + length, c=c)
            self.dot(*a, c=c); self.circle(x, b[1], 2.6, c=c, fill=PAPER)
            if nc:
                self.line(x, a[1], x + 4, b[1] + 2, c=c)
            else:
                self.line(x, a[1], x + 14, b[1] - 2, c=c)
            if key:
                kx, ky = x + 26, (a[1] + b[1]) / 2
                self.circle(kx, ky, 4, c=c); self.line(kx, ky + 4, kx, ky + 14, c=c); self.line(kx, ky + 10, kx + 4, ky + 10, c=c)
                self.line(kx - 4, ky, x + 9, ky, c=c, dash="2 2")
            if label: self.text(x - 12, y + length / 2, label, 10, anchor="end")
            if value: self.text(x - 12, y + length / 2 + 12, value, 10, MUTED, anchor="end")
        return self

    def nmos(self, x, y, label="", value="", c=INK):
        """N-channel MOSFET. Drain pin (x, y-30), source pin (x, y+30), gate pin (x-40, y)."""
        self.line(x, y - 30, x, y - 14, c=c); self.line(x, y + 30, x, y + 14, c=c)
        self.line(x - 12, y - 16, x - 12, y + 16, c=c, w=2)       # channel
        self.line(x - 18, y - 12, x - 18, y + 12, c=c, w=2)       # gate plate
        self.line(x - 40, y, x - 18, y, c=c)
        self.line(x - 12, y - 14, x, y - 14, c=c); self.line(x - 12, y + 14, x, y + 14, c=c); self.line(x - 12, y, x, y, c=c)
        self.line(x, y, x, y + 14, c=c)
        self.poly([(x - 10, y), (x - 4, y - 4), (x - 4, y + 4)], c=c, fill=c, close=True)
        # body diode
        self.line(x + 10, y - 14, x + 10, y + 14, c=c, w=1)
        self.line(x, y - 14, x + 10, y - 14, c=c, w=1); self.line(x, y + 14, x + 10, y + 14, c=c, w=1)
        self.poly([(x + 6, y + 4), (x + 14, y + 4), (x + 10, y - 3)], c=c, w=1, fill=c, close=True)
        self.line(x + 6, y - 3, x + 14, y - 3, c=c, w=1)
        if label: self.text(x + 20, y - 4, label, 10)
        if value: self.text(x + 20, y + 9, value, 10, MUTED)
        return self

    def relay_spdt(self, x, y, label="", value="", c=INK, armed=False):
        """Changeover contact drawn vertically. COM pin (x, y+70) at bottom; NO pin (x-30, y) top-left;
        NC pin (x+30, y) top-right. Coil drawn separately with coil()."""
        self.line(x, y + 70, x, y + 50, c=c)
        self.dot(x, y + 50, c=c)
        self.line(x - 30, y, x - 30, y + 20, c=c); self.circle(x - 30, y + 20, 2.6, c=c, fill=PAPER)
        self.line(x + 30, y, x + 30, y + 20, c=c); self.circle(x + 30, y + 20, 2.6, c=c, fill=PAPER)
        if armed:
            self.line(x, y + 50, x - 28, y + 24, c=c, w=1.8)
        else:
            self.line(x, y + 50, x + 28, y + 24, c=c, w=1.8)
        self.text(x - 34, y + 34, "NO", 9, MUTED, anchor="end")
        self.text(x + 34, y + 34, "NC", 9, MUTED)
        self.text(x + 8, y + 64, "COM", 9, MUTED)
        if label: self.text(x, y - 8, label, 10, anchor="middle", weight="bold")
        if value: self.text(x, y - 20, value, 9, MUTED, anchor="middle")
        return self

    def coil(self, x, y, label="", c=INK):
        """Relay coil, vertical box; top pin (x,y), bottom pin (x,y+50)."""
        self.line(x, y, x, y + 12, c=c); self.line(x, y + 38, x, y + 50, c=c)
        self.rect(x - 12, y + 12, 24, 26, c=c, fill=PAPER)
        self.line(x - 12, y + 38, x + 12, y + 12, c=c, w=1)
        if label: self.text(x + 18, y + 29, label, 10)
        return self

    def chip(self, x, y, w, h, name, left=(), right=(), top=(), bottom=(), sub="", fill="#F4F4F4", c=INK, pitch=20):
        """IC/module box. Pins are (name) tuples; returns dict pin->(x,y) of the outer pin end."""
        self.rect(x, y, w, h, c=c, fill=fill, rx=3)
        self.text(x + w / 2, y + 16, name, 11, anchor="middle", weight="bold")
        if sub: self.text(x + w / 2, y + 29, sub, 9, MUTED, anchor="middle")
        pins = {}
        y0 = y + (40 if sub else 32)
        for i, p in enumerate(left):
            if p is None: continue
            py = y0 + i * pitch
            self.line(x - 14, py, x, py, c=c); self.text(x + 5, py + 3.5, p, 9, font=MONO)
            pins[("L", p)] = (x - 14, py)
        for i, p in enumerate(right):
            if p is None: continue
            py = y0 + i * pitch
            self.line(x + w, py, x + w + 14, py, c=c); self.text(x + w - 5, py + 3.5, p, 9, anchor="end", font=MONO)
            pins[("R", p)] = (x + w + 14, py)
        for i, p in enumerate(top):
            px = x + 30 + i * 46
            self.line(px, y - 14, px, y, c=c); self.text(px, y + 44 if False else y - 18, p, 9, anchor="middle", font=MONO)
            pins[("T", p)] = (px, y - 14)
        for i, p in enumerate(bottom):
            px = x + 30 + i * 46
            self.line(px, y + h, px, y + h + 14, c=c); self.text(px, y + h + 26, p, 9, anchor="middle", font=MONO)
            pins[("B", p)] = (px, y + h + 14)
        return pins

    def conn(self, x, y, label, pins=2, c=INK):
        """Connector body (vertical stack of pin circles), pin i at (x, y+i*20)."""
        self.rect(x - 8, y - 10, 16, pins * 20, c=c, fill="#EEE", rx=2)
        for i in range(pins):
            self.circle(x, y + i * 20, 3, c=c, fill=PAPER)
        self.text(x, y - 16, label, 10, anchor="middle", weight="bold")
        return self

    def note(self, x, y, s, size=10, c=MUTED, w=None):
        return self.text(x, y, s, size, c)

    def frame(self, sheet, title, rev="A", date="2026-11-18", scale="NTS"):
        """Title block along the bottom right."""
        W, H = self.w, self.h
        self.rect(6, 6, W - 12, H - 12, c=INK, sw=1.2)
        bw, bh = 460, 54
        x, y = W - bw - 6, H - bh - 6
        self.rect(x, y, bw, bh, c=INK, sw=1.2, fill=PAPER)
        self.line(x, y + 27, x + bw, y + 27, c=INK, w=0.8)
        self.line(x + 320, y, x + 320, y + bh, c=INK, w=0.8)
        self.text(x + 8, y + 18, title, 12, weight="bold")
        self.text(x + 8, y + 45, "Six-pad wireless launcher (open design)", 9, MUTED)
        self.text(x + 328, y + 18, sheet, 12, weight="bold", font=MONO)
        self.text(x + 328, y + 45, f"Rev {rev} · {date} · {scale}", 9, MUTED)
        return self

    def render(self):
        defs = f"<defs>{''.join(self.defs)}</defs>" if self.defs else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" '
                f'role="img" aria-label="{esc(self.title)}"><title>{esc(self.title)}</title>'
                f'{"<desc>" + esc(self.desc) + "</desc>" if self.desc else ""}{defs}'
                f'<rect width="{self.w}" height="{self.h}" fill="{PAPER}"/>' + "".join(self.el) + "</svg>")
