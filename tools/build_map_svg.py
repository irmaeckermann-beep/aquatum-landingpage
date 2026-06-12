#!/usr/bin/env python3
"""Erzeugt eine interaktive SVG-Karte der Schweizer Kantone, eingefärbt nach
Wasserhärte. Jeder Kanton ist ein <path class="canton"> mit data-Attributen
(Name, °fH, Kategorie) für Hover/Klick auf der Website.
Aufruf:  python3 tools/build_map_svg.py  ->  assets/ch-map.svg
"""
import json
import math
import os
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_hex

HERE = os.path.dirname(__file__)
GEO = os.path.join(HERE, "ch-cantons.geojson")
OUT = os.path.join(HERE, "..", "assets", "ch-map.svg")

HARDNESS = {
    "Ticino": 8, "Uri": 10, "Graubünden": 12, "Obwalden": 14, "Glarus": 15,
    "Valais": 16, "Nidwalden": 18, "Appenzell Innerrhoden": 18,
    "Appenzell Ausserrhoden": 19, "Schwyz": 20, "St. Gallen": 22,
    "Bern": 24, "Zürich": 24, "Genève": 26, "Zug": 28, "Basel-Stadt": 28,
    "Vaud": 30, "Thurgau": 30, "Luzern": 30, "Fribourg": 31, "Aargau": 34,
    "Solothurn": 35, "Basel-Landschaft": 36, "Neuchâtel": 36,
    "Schaffhausen": 38, "Jura": 40,
}
ABBR = {
    "Zürich": "ZH", "Bern": "BE", "Luzern": "LU", "Uri": "UR", "Schwyz": "SZ",
    "Obwalden": "OW", "Nidwalden": "NW", "Glarus": "GL", "Zug": "ZG",
    "Fribourg": "FR", "Solothurn": "SO", "Basel-Stadt": "BS",
    "Basel-Landschaft": "BL", "Schaffhausen": "SH", "Appenzell Ausserrhoden": "AR",
    "Appenzell Innerrhoden": "AI", "St. Gallen": "SG", "Graubünden": "GR",
    "Aargau": "AG", "Thurgau": "TG", "Ticino": "TI", "Vaud": "VD", "Valais": "VS",
    "Neuchâtel": "NE", "Genève": "GE", "Jura": "JU",
}
cmap = LinearSegmentedColormap.from_list("haerte", [
    (0.00, "#cfeaf5"), (0.35, "#9fd6e6"), (0.55, "#f6cd6b"),
    (0.78, "#ec660b"), (1.00, "#c0271a"),
])
norm = Normalize(vmin=8, vmax=40)


def category(h):
    if h <= 15: return "weich"
    if h <= 28: return "mittel"
    if h <= 36: return "hart"
    return "sehr hart"


def main():
    data = json.load(open(GEO, encoding="utf-8"))
    # Grenzen bestimmen
    lons, lats = [], []
    for f in data["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            for ring in poly:
                for x, y in ring:
                    lons.append(x); lats.append(y)
    lon0, lon1 = min(lons), max(lons)
    lat0, lat1 = min(lats), max(lats)
    phi = math.radians((lat0 + lat1) / 2)
    W = 1000.0
    kx = W / (lon1 - lon0)
    ky = kx / math.cos(phi)
    H = (lat1 - lat0) * ky
    pad = 8

    def px(lon, lat):
        return (lon - lon0) * kx + pad, (lat1 - lat) * ky + pad

    paths, labels = [], []
    for f in data["features"]:
        name = f["properties"]["name"]
        h = HARDNESS.get(name, 0)
        fill = to_hex(cmap(norm(h)))
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        d = []
        for poly in polys:
            for ring in poly:
                if len(ring) < 3:
                    continue
                pts = []
                for i, (lon, lat) in enumerate(ring):
                    X, Y = px(lon, lat)
                    pts.append(("M" if i == 0 else "L") + f"{X:.1f} {Y:.1f}")
                d.append(" ".join(pts) + " Z")
        cat = category(h)
        paths.append(
            f'<path class="canton" data-name="{name}" data-haerte="{h}" data-cat="{cat}" '
            f'fill="{fill}" d="{" ".join(d)}"><title>{name}: {h} °fH ({cat})</title></path>'
        )
        # Label-Position
        ext = max(polys, key=lambda pl: len(pl[0]))[0]
        clon = sum(p[0] for p in ext) / len(ext)
        clat = sum(p[1] for p in ext) / len(ext)
        LX, LY = px(clon, clat)
        tcol = "#ffffff" if h >= 30 else "#16222e"
        labels.append(f'<text x="{LX:.1f}" y="{LY:.1f}" class="canton-label" '
                      f'fill="{tcol}">{ABBR.get(name, "")}</text>')

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W + 2 * pad:.0f} {H + 2 * pad:.0f}" '
        f'class="ch-map" role="img" aria-label="Schweizer Kantone nach Wasserhärte">\n'
        f'  <g class="cantons">\n    ' + "\n    ".join(paths) + "\n  </g>\n"
        f'  <g class="labels" pointer-events="none">\n    ' + "\n    ".join(labels) + "\n  </g>\n"
        f'</svg>\n'
    )
    with open(os.path.abspath(OUT), "w", encoding="utf-8") as fh:
        fh.write(svg)
    print("written:", os.path.abspath(OUT), f"({len(svg)} bytes)")


if __name__ == "__main__":
    main()
