"""Convierte source-prepped.png en un retrato ASCII animado (SVG autocontenido, solo SMIL).

Cada fila se revela de izquierda a derecha, escalonada de arriba abajo.
STATIC=1 desactiva la animación. La foto original NO se incrusta: solo caracteres.
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "skaiiner-ascii.svg"

COLS = 100
CHAR_W, LINE_H, FONT = 6, 9, 10
RAMP = " .`:-=+*cs#%@"  # de menos a más "tinta"
INK = "#c9d1d9"
BG = "#0d1117"
STATIC = os.environ.get("STATIC") == "1"

img = cv2.imread(str(SRC), cv2.IMREAD_GRAYSCALE)
if img is None:
    raise SystemExit("Falta source-prepped.png: ejecuta antes scripts/prep_photo.py")

h, w = img.shape
rows = max(1, round(COLS * (h / w) * (CHAR_W / LINE_H)))
small = cv2.resize(img, (COLS, rows), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
ink = 1.0 - small                       # oscuro = más tinta; fondo blanco = vacío
ink = np.clip((ink - 0.04) / 0.80, 0, 1) ** 0.8
idx = (ink * (len(RAMP) - 1)).round().astype(int)

W, H = COLS * CHAR_W, rows * LINE_H + 16
parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="ASCII portrait">',
    "<title>ASCII portrait of Skaiiner</title>",
    f'<style>text{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:{FONT}px;fill:{INK};white-space:pre}}</style>',
    f'<rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="#30363d"/>',
    "<defs>",
]
for r in range(rows):
    anim = (
        ""
        if STATIC
        else f'<animate attributeName="width" from="0" to="{W}" begin="{r * 0.045:.3f}s" dur="0.7s" fill="freeze"/>'
    )
    width0 = W if STATIC else 0
    parts.append(f'<clipPath id="r{r}"><rect x="0" y="{8 + r * LINE_H}" width="{width0}" height="{LINE_H}">{anim}</rect></clipPath>')
parts.append("</defs>")
for r in range(rows):
    line = "".join(RAMP[i] for i in idx[r]).rstrip()
    if not line:
        continue
    parts.append(
        f'<text x="0" y="{8 + (r + 1) * LINE_H - 2}" textLength="{len(line) * CHAR_W}" lengthAdjust="spacing" '
        f'clip-path="url(#r{r})" xml:space="preserve">{escape(line)}</text>'
    )
parts.append("</svg>")
OUT.write_text("\n".join(parts), encoding="utf-8")
print(f"{OUT.name}: {COLS}x{rows} caracteres, {len('\n'.join(parts)) // 1024} KB")
