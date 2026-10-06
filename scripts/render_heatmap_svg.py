"""Renderiza data/contributions.json como un SVG animado autocontenido (sin JS, sin recursos externos).

STATIC=1 desactiva las animaciones (útil para capturas/vista previa).
"""
import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG, FG, MUTED = "#0d1117", "#c9d1d9", "#8b949e"
CELL, GAP = 12, 3
STEP = CELL + GAP
LEFT, TOP = 36, 40
W = 860
STATIC = os.environ.get("STATIC") == "1"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def color_index(day):
    if day["count"] == 0 or day["level"] == 0:
        return 0
    return 5 if (day["level"] == 4 and day["count"] >= 10) else day["level"]


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    days = data["days"]
    first = date.fromisoformat(days[0]["date"])
    first_col = (first.weekday() + 1) % 7  # columnas empiezan en domingo

    cells, month_labels, last_month = [], [], None
    weeks = 0
    for i, d in enumerate(days):
        dt = date.fromisoformat(d["date"])
        pos = i + first_col
        week, dow = divmod(pos, 7)
        weeks = max(weeks, week + 1)
        x, y = LEFT + week * STEP, TOP + dow * STEP
        delay = (week + dow) * 14  # barrido diagonal
        cls = "" if STATIC else f' class="c" style="animation-delay:{delay}ms"'
        label = f"{d['count']} contributions on {d['date']}"
        cells.append(
            f'<rect{cls} x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
            f'fill="{PALETTE[color_index(d)]}"><title>{label}</title></rect>'
        )
        if dow == 0 and dt.month != last_month and (week > 0 or dt.day <= 7):
            month_labels.append(f'<text x="{x}" y="{TOP - 10}" class="m">{MONTHS[dt.month - 1]}</text>')
            last_month = dt.month

    grid_bottom = TOP + 7 * STEP
    H = grid_bottom + 46
    day_labels = "".join(
        f'<text x="{LEFT - 8}" y="{TOP + r * STEP + 10}" class="m" text-anchor="end">{n}</text>'
        for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )
    legend_x = W - 20 - 5 * (CELL + 4) - 60
    legend = "".join(
        f'<rect x="{legend_x + 30 + k * (CELL + 4)}" y="{grid_bottom + 18}" width="{CELL}" height="{CELL}" rx="2" fill="{PALETTE[k]}"/>'
        for k in range(5)
    )
    anim_css = (
        ""
        if STATIC
        else ".c{opacity:0;transform-box:fill-box;animation:pop .45s ease-out forwards}"
        "@keyframes pop{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:none}}"
        "@media (prefers-reduced-motion:reduce){.c{animation:none;opacity:1}}"
    )
    stats = (
        f"{data['total']} contributions in the last year  ·  "
        f"current streak {data['current_streak']}d  ·  longest streak {data['longest_streak']}d"
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">GitHub contribution graph for {data['user']}: {data['total']} contributions in the last year</title>
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.m{{font-size:10px;fill:{MUTED}}}
.s{{font-size:12px;fill:{FG}}}
{anim_css}
</style>
<rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="#30363d"/>
{''.join(month_labels)}
{day_labels}
{''.join(cells)}
<text x="{LEFT}" y="{grid_bottom + 28}" class="s">{stats}</text>
<text x="{legend_x}" y="{grid_bottom + 28}" class="m">Less</text>
{legend}
<text x="{legend_x + 30 + 5 * (CELL + 4) + 2}" y="{grid_bottom + 28}" class="m">More</text>
</svg>
"""
    OUT.write_text(svg, encoding="utf-8")
    print(f"escrito {OUT.name}: {len(days)} días, {weeks} semanas, {len(svg)//1024} KB")


if __name__ == "__main__":
    main()
