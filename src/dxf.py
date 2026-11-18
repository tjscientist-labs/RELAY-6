# SPDX-License-Identifier: GPL-2.0-only
"""Minimal DXF (R12, mm) writer: LINE, CIRCLE, ARC and closed LWPOLYLINE-free outlines.

R12 needs no handles or classes and opens in LightBurn, Inkscape, LibreCAD, Fusion and every
laser/router service's uploader. Layers: CUT (through cuts), ENGRAVE (marking only), NOTE (text).
"""
import math


class Dxf:
    def __init__(self):
        self.e = []

    def line(self, x1, y1, x2, y2, layer="CUT"):
        self.e += ["0", "LINE", "8", layer, "10", f"{x1:.3f}", "20", f"{y1:.3f}", "30", "0", "11", f"{x2:.3f}", "21", f"{y2:.3f}", "31", "0"]

    def circle(self, cx, cy, r, layer="CUT"):
        self.e += ["0", "CIRCLE", "8", layer, "10", f"{cx:.3f}", "20", f"{cy:.3f}", "30", "0", "40", f"{r:.3f}"]

    def arc(self, cx, cy, r, a0, a1, layer="CUT"):
        """Counter-clockwise from a0 to a1, degrees."""
        self.e += ["0", "ARC", "8", layer, "10", f"{cx:.3f}", "20", f"{cy:.3f}", "30", "0", "40", f"{r:.3f}", "50", f"{a0:.3f}", "51", f"{a1:.3f}"]

    def text(self, x, y, h, s, layer="NOTE"):
        self.e += ["0", "TEXT", "8", layer, "10", f"{x:.3f}", "20", f"{y:.3f}", "30", "0", "40", f"{h:.3f}", "1", s]

    def rrect(self, cx, cy, w, h, r, layer="CUT"):
        """Rounded rectangle centred on (cx, cy)."""
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        r = min(r, w / 2, h / 2)
        if r <= 0:
            for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
                self.line(*a, *b, layer=layer)
            return
        self.line(x0 + r, y0, x1 - r, y0, layer); self.line(x1, y0 + r, x1, y1 - r, layer)
        self.line(x1 - r, y1, x0 + r, y1, layer); self.line(x0, y1 - r, x0, y0 + r, layer)
        self.arc(x1 - r, y0 + r, r, 270, 360, layer); self.arc(x1 - r, y1 - r, r, 0, 90, layer)
        self.arc(x0 + r, y1 - r, r, 90, 180, layer); self.arc(x0 + r, y0 + r, r, 180, 270, layer)

    def save(self, path):
        hdr = ["0", "SECTION", "2", "HEADER", "9", "$INSUNITS", "70", "4", "9", "$MEASUREMENT", "70", "1", "0", "ENDSEC",
               "0", "SECTION", "2", "TABLES", "0", "TABLE", "2", "LAYER", "70", "3"]
        for name, col in (("CUT", 1), ("ENGRAVE", 5), ("NOTE", 7)):
            hdr += ["0", "LAYER", "2", name, "70", "0", "62", str(col), "6", "CONTINUOUS"]
        hdr += ["0", "ENDTAB", "0", "ENDSEC", "0", "SECTION", "2", "ENTITIES"]
        with open(path, "w") as f:
            f.write("\n".join(hdr + self.e + ["0", "ENDSEC", "0", "EOF"]) + "\n")
