#!/usr/bin/env python3
"""Erzeugt eine Schweizer Kantons-Karte, eingefärbt nach Wasserhärte
(weich = hell/cyan, hart = orange/rot = problematisch).
Aufruf:  python3 tools/build_hardness_map.py  ->  assets/wasserhaerte-karte.png
"""
import json
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Patch

HERE = os.path.dirname(__file__)
GEO = os.path.join(HERE, "ch-cantons.geojson")
OUT = os.path.join(HERE, "..", "assets", "wasserhaerte-karte.png")

# Wasserhärte (°fH) je Kanton – Richtwerte, identisch zum Online-Rechner.
HARDNESS = {
    "Ticino": 8, "Uri": 10, "Graubünden": 12, "Obwalden": 14, "Glarus": 15,
    "Valais": 16, "Nidwalden": 18, "Appenzell Innerrhoden": 18,
    "Appenzell Ausserrhoden": 19, "Schwyz": 20, "St. Gallen": 22,
    "Bern": 24, "Zürich": 24, "Genève": 26, "Zug": 28, "Basel-Stadt": 28,
    "Vaud": 30, "Thurgau": 30, "Luzern": 30, "Fribourg": 31, "Aargau": 34,
    "Solothurn": 35, "Basel-Landschaft": 36, "Neuchâtel": 36,
    "Schaffhausen": 38, "Jura": 40,
}

# Farbverlauf: weich (hell-cyan) -> mittel (gelb) -> hart (orange) -> sehr hart (rot)
cmap = LinearSegmentedColormap.from_list("haerte", [
    (0.00, "#cfeaf5"), (0.35, "#9fd6e6"), (0.55, "#f6cd6b"),
    (0.78, "#ec660b"), (1.00, "#c0271a"),
])
norm = Normalize(vmin=8, vmax=40)


def rings_to_path(rings):
    verts, codes = [], []
    for ring in rings:
        if len(ring) < 3:
            continue
        verts.append(ring[0]); codes.append(Path.MOVETO)
        for pt in ring[1:]:
            verts.append(pt); codes.append(Path.LINETO)
        verts.append(ring[0]); codes.append(Path.CLOSEPOLY)
    return Path(verts, codes)


def main():
    data = json.load(open(GEO, encoding="utf-8"))
    fig, ax = plt.subplots(figsize=(9.2, 6.2), dpi=200)

    all_lat = []
    for feat in data["features"]:
        name = feat["properties"]["name"]
        h = HARDNESS.get(name)
        color = cmap(norm(h)) if h is not None else "#dddddd"
        geom = feat["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            path = rings_to_path(poly)  # poly = [exterior, hole1, ...]
            ax.add_patch(PathPatch(path, facecolor=color, edgecolor="white", linewidth=0.8))
            for ring in poly:
                all_lat += [p[1] for p in ring]

    ax.autoscale_view()
    ax.relim()
    ax.autoscale()
    mean_lat = sum(all_lat) / len(all_lat)
    ax.set_aspect(1.0 / math.cos(math.radians(mean_lat)))
    ax.axis("off")

    # Legende (diskret)
    legend_items = [
        Patch(facecolor=cmap(norm(11)), edgecolor="white", label="weich (8–15 °fH)"),
        Patch(facecolor=cmap(norm(22)), edgecolor="white", label="mittel (16–28 °fH)"),
        Patch(facecolor=cmap(norm(33)), edgecolor="white", label="hart (30–36 °fH)"),
        Patch(facecolor=cmap(norm(40)), edgecolor="white", label="sehr hart (38–40 °fH)"),
    ]
    leg = ax.legend(handles=legend_items, loc="lower left", frameon=False,
                    fontsize=11, handlelength=1.1, handleheight=1.1,
                    labelspacing=0.5, borderaxespad=0.2)
    for t in leg.get_texts():
        t.set_color("#16222e")

    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    fig.savefig(os.path.abspath(OUT), dpi=200, transparent=True,
                bbox_inches="tight", pad_inches=0.05)
    print("written:", os.path.abspath(OUT))


if __name__ == "__main__":
    main()
