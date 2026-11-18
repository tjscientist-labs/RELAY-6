# SPDX-License-Identifier: GPL-2.0-only
"""Tiny dimetric renderer for the launcher views (mm in, SVG px out).

World axes: x to the right (case width), y away from the viewer (case depth), z up.
Faces are collected with a depth key and painted back to front (painter's algorithm),
which is enough for the box-and-cylinder models used here.
"""
import math

# projection: x -> lower right, y -> upper right (receding), z -> up
AX = (math.cos(math.radians(-18)), -math.sin(math.radians(-18)))   # x axis on screen
AY = (math.cos(math.radians(40)) * 0.62, -math.sin(math.radians(40)) * 0.62)
S = 1.0


def P(x, y, z, O=(0, 0), k=1.0):
    return (O[0] + k * (AX[0] * x + AY[0] * y), O[1] + k * (AX[1] * x + AY[1] * y - z))


def shade(hexc, f):
    hexc = hexc.lstrip("#")
    r, g, b = (int(hexc[i:i + 2], 16) for i in (0, 2, 4))
    if f >= 1:
        r, g, b = (int(c + (255 - c) * (f - 1)) for c in (r, g, b))
    else:
        r, g, b = (int(c * f) for c in (r, g, b))
    return f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"


class Scene:
    def __init__(self, O, k=1.0):
        self.O, self.k = O, k
        self.items = []   # (depth, svg)

    def _pts(self, pts3):
        return " ".join(f"{a:.1f},{b:.1f}" for a, b in (P(*p, O=self.O, k=self.k) for p in pts3))

    def face(self, pts3, fill, stroke="#222", sw=0.7, depth=None, extra=""):
        if depth is None:
            depth = sum(p[1] for p in pts3) / len(pts3) - sum(p[2] for p in pts3) / len(pts3) * 0.01 - sum(p[0] for p in pts3) / len(pts3) * 0.001
        self.items.append((depth, f'<polygon points="{self._pts(pts3)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" {extra}/>'))

    def raw(self, depth, svg):
        self.items.append((depth, svg))

    def box(self, x0, y0, z0, w, d, h, col, stroke="#222", sw=0.7, top=None, bias=0.0, depth=None):
        x1, y1, z1 = x0 + w, y0 + d, z0 + h
        dep = y0 + bias if depth is None else depth + 0.3
        # visible faces for this projection: front (y=y0), right? (x=x1 faces +x: visible), top
        self.face([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], shade(col, 0.82), stroke, sw, depth=dep - 0.2)
        self.face([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], shade(col, 0.66), stroke, sw, depth=dep - 0.1)
        self.face([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], top or col, stroke, sw, depth=dep - 0.3 - h * 0.0001)

    def cyl(self, cx, cy, z0, r, h, col, top=None, stroke="#222", sw=0.7, bias=0.0, n=40, depth=None):
        """Vertical cylinder."""
        dep = cy - r + bias if depth is None else depth + 0.3
        ring0 = [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z0) for i in range(n)]
        ring1 = [(x, y, z0 + h) for x, y, _ in ring0]
        # silhouette: take the screen-lowest half of the bottom ring and the matching top half
        scr = [P(*p) for p in ring0]
        # find extreme points along the screen x axis
        i_min = min(range(n), key=lambda i: scr[i][0]); i_max = max(range(n), key=lambda i: scr[i][0])
        # walk from i_min to i_max along the side with larger screen y (front)
        def walk(a, b, step):
            out = [a]
            i = a
            while i != b:
                i = (i + step) % n
                out.append(i)
            return out
        w1, w2 = walk(i_min, i_max, 1), walk(i_min, i_max, -1)
        avg = lambda idx: sum(scr[i][1] for i in idx) / len(idx)
        front = w1 if avg(w1) > avg(w2) else w2
        side = [ring0[i] for i in front] + [ring1[i] for i in reversed(front)]
        self.face(side, shade(col, 0.78), stroke, sw, depth=dep - 0.2)
        self.face(ring1, top or col, stroke, sw, depth=dep - 0.3 - h * 0.0001)

    def label(self, x, y, z, text, dx=30, dy=-30, size=11, col="#111", anchor="start", depth=-1e9):
        a = P(x, y, z, O=self.O, k=self.k)
        b = (a[0] + dx, a[1] + dy)
        svg = (f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#444" stroke-width="0.8"/>'
               f'<circle cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="2" fill="#444"/>'
               f'<text x="{b[0] + (4 if anchor == "start" else -4):.1f}" y="{b[1] + 4:.1f}" font-family="DejaVu Sans, Arial, sans-serif" '
               f'font-size="{size}" fill="{col}" text-anchor="{anchor}">{text}</text>')
        self.items.append((depth, svg))

    def render(self):
        # paint far (large depth) first
        return "".join(s for _, s in sorted(self.items, key=lambda t: -t[0]))


def fit(points3d, box):
    """(O, k) so the projected points fill box = (x0, y0, x1, y1) on screen."""
    pr = [P(*p) for p in points3d]
    xs, ys = [a for a, _ in pr], [b for _, b in pr]
    bw, bh = max(xs) - min(xs), max(ys) - min(ys)
    k = min((box[2] - box[0]) / bw, (box[3] - box[1]) / bh)
    ox = box[0] + ((box[2] - box[0]) - bw * k) / 2 - min(xs) * k
    oy = box[1] + ((box[3] - box[1]) - bh * k) / 2 - min(ys) * k
    return (ox, oy), k
