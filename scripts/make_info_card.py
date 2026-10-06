"""Genera info-card.svg (panel estilo neofetch) a partir de data/profile.json.

SVG autocontenido: solo texto y animación CSS (fade + slide por línea), sin JS ni recursos externos.
STATIC=1 desactiva la animación.
"""
import json
import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
P = json.loads((ROOT / "data" / "profile.json").read_text(encoding="utf-8"))
OUT = ROOT / "info-card.svg"

W, H = 490, 330
BG, FG, MUTED, KEY, ACCENT = "#0d1117", "#c9d1d9", "#8b949e", "#39d353", "#58a6ff"
STATIC = os.environ.get("STATIC") == "1"
X_KEY, X_VAL = 24, 118
Y0, DY = 78, 21

rows = [
    ("user", f"{P['handle']} ({P['name']})"),
    ("since", P["since"]),
    ("role", P["role"]),
    ("stack", "  ·  ".join(P["stack"])),
    ("focus", "  ·  ".join(P["focus"])),
]
lines = []  # (key, value, color)
for k, v in rows:
    lines.append((k, v, FG))
lines.append(("projects", "", FG))
for pr in P["projects"]:
    lines.append(("", f"▸ {pr['name']}  {pr['text']}", ACCENT))

parts = []
delay = 0.35
for i, (k, v, color) in enumerate(lines):
    y = Y0 + i * DY
    d = f"{delay + i * 0.16:.2f}s"
    anim = "" if STATIC else f' class="l" style="animation-delay:{d}"'
    inner = ""
    if k:
        inner += f'<tspan x="{X_KEY}" fill="{KEY}" font-weight="bold">{escape(k)}</tspan>'
    if v:
        x = X_VAL if k else X_KEY + 12
        inner += f'<tspan x="{x}" fill="{color}">{escape(v)}</tspan>'
    parts.append(f'<text{anim} y="{y}">{inner}</text>')

sep_y = Y0 + len(lines) * DY + 4
palette = "".join(
    f'<rect x="{X_KEY + i * 22}" y="{sep_y + 6}" width="18" height="10" rx="2" fill="{c}"/>'
    for i, c in enumerate(["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"])
)
anim_css = (
    ""
    if STATIC
    else ".l{opacity:0;animation:in .5s ease-out forwards}"
    "@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}"
    "@keyframes blink{50%{opacity:0}}.cur{animation:blink 1s steps(1) infinite}"
    "@media (prefers-reduced-motion:reduce){.l{animation:none;opacity:1}.cur{animation:none}}"
)
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">Profile card for {escape(P['handle'])}</title>
<style>
text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;fill:{FG}}}
.m{{fill:{MUTED}}}
{anim_css}
</style>
<rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="#30363d"/>
<rect width="{W}" height="34" rx="10" fill="#161b22"/><rect y="24" width="{W}" height="10" fill="#161b22"/>
<circle cx="20" cy="17" r="5" fill="#ff5f56"/><circle cx="38" cy="17" r="5" fill="#ffbd2e"/><circle cx="56" cy="17" r="5" fill="#27c93f"/>
<text x="76" y="21" class="m">{escape(P['handle'].lower())}@github ~ $ neofetch</text>
{''.join(parts)}
{palette}
<text x="{X_KEY}" y="{H - 14}" class="m">$ <tspan class="cur">▮</tspan></text>
</svg>
"""
OUT.write_text(svg, encoding="utf-8")
print(f"{OUT.name}: {len(lines)} líneas, {len(svg)//1024} KB")
