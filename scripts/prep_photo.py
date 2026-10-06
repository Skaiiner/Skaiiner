"""Prepara la foto para el retrato ASCII (todo local, no se sube nada).

Entrada: source-photo.jpg  ->  Salida: source-prepped.png
La foto ya tiene fondo liso y claro, así que no se usa rembg: se detecta el fondo por
distancia de color, se recorta al sujeto, se pone fondo blanco y se sube el contraste (CLAHE).
"""
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "source-photo.jpg"
out = ROOT / "source-prepped.png"

img = cv2.imread(str(src))
if img is None:
    sys.exit(f"No se pudo leer {src}")

# Color de fondo = mediana de los bordes superiores/laterales.
border = np.concatenate([img[:20].reshape(-1, 3), img[:200, :20].reshape(-1, 3), img[:200, -20:].reshape(-1, 3)])
bg = np.median(border, axis=0)
dist = np.linalg.norm(img.astype(np.float32) - bg, axis=2)
mask = (dist > 28).astype(np.uint8) * 255
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
mask = cv2.medianBlur(mask, 7)

import os

if os.environ.get("CROP"):  # CROP="x0,y0,x1,y1" para recorte manual (p. ej. excluir una mesa)
    x0, y0, x1, y1 = (int(v) for v in os.environ["CROP"].split(","))
else:
    ys, xs = np.where(mask > 0)
    pad = 18
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, img.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, img.shape[1])
crop, m = img[y0:y1, x0:x1], mask[y0:y1, x0:x1]

# Contraste local sobre la luminancia.
lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
lab[:, :, 0] = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(lab[:, :, 0])
crop = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

alpha = (cv2.GaussianBlur(m, (5, 5), 0).astype(np.float32) / 255.0)[..., None]
white = np.full_like(crop, 255)
res = (crop * alpha + white * (1 - alpha)).astype(np.uint8)
cv2.imwrite(str(out), res)
print(f"{out.name}: {res.shape[1]}x{res.shape[0]} (recorte {x0},{y0} -> {x1},{y1})")
