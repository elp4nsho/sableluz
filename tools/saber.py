"""Malla y textura del sable de luz.

La malla es un 'torno': un perfil (altura, radio) que se gira alrededor del eje Y.
  Y bajo = pomo / empunadura,  Y alto = punta de la hoja (mismo eje y largo que la v1.0).

UV: u = vuelta alrededor del eje (0..1, con costura duplicada para que no haya salto),
    v = a lo largo del sable; la empunadura ocupa la mitad inferior de la textura
    (HILT_V .. 1) para tener detalle, la hoja la mitad superior (0 .. HILT_V).
Cada tramo del perfil lleva una etiqueta; la textura se pinta con esas mismas etiquetas,
asi el dibujo siempre calza con la geometria.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HILT_TOP = 0.126     # donde termina el emisor y empieza la hoja
BLADE_TIP = 0.600
HILT_V = 0.45        # v de la union empunadura/hoja en la textura


def profile():
    """[(y, radio, etiqueta del tramo que sigue)] de abajo hacia arriba."""
    p = [(0.000, 0.0100, 'pommel'), (0.003, 0.0140, 'pommel'), (0.011, 0.0145, 'pommel_ring'),
         (0.014, 0.0132, 'grip')]
    # grip con estrias: anillos alternados
    y = 0.016
    k = 0
    while y < 0.078:
        p.append((y, 0.0140 if k % 2 == 0 else 0.0128, 'grip_ridge' if k % 2 == 0 else 'grip'))
        y += 0.005
        k += 1
    p += [(0.080, 0.0134, 'band'), (0.082, 0.0152, 'band'), (0.094, 0.0152, 'band'),
          (0.096, 0.0150, 'shroud'), (0.117, 0.0176, 'shroud_lip'), (0.122, 0.0176, 'emitter'),
          (0.124, 0.0112, 'emitter'), (HILT_TOP, 0.0096, 'blade')]
    # hoja: casi recta, levemente mas delgada hacia la punta, punta redondeada
    for t in np.linspace(0.0, 1.0, 12)[1:]:
        p.append((HILT_TOP + 0.005 + t * (0.585 - HILT_TOP - 0.005), 0.0096 - 0.0008 * t, 'blade'))
    p += [(0.592, 0.0080, 'blade'), (0.597, 0.0056, 'blade'), (BLADE_TIP, 0.0022, 'blade')]
    return p


def v_of(y):
    """Posicion vertical en la textura (DirectX: v=0 arriba)."""
    if y <= HILT_TOP:
        return 1.0 - (y / HILT_TOP) * (1.0 - HILT_V)
    return HILT_V * (1.0 - (y - HILT_TOP) / (BLADE_TIP - HILT_TOP))


def build_mesh(n_around=24):
    prof = profile()
    verts, normals, uvs, faces = [], [], [], []
    ring_start = []
    for i, (y, r, _) in enumerate(prof):
        # normal del torno segun la pendiente del perfil
        y0, r0, _ = prof[max(i - 1, 0)]
        y1, r1, _ = prof[min(i + 1, len(prof) - 1)]
        dy, dr = y1 - y0, r1 - r0
        ln = math.hypot(dy, dr) or 1.0
        ny_, nr = -dr / ln, dy / ln
        ring_start.append(len(verts))
        for a in range(n_around + 1):           # +1: costura con u=1 duplicada
            ang = 2 * math.pi * a / n_around
            c, s = math.cos(ang), math.sin(ang)
            verts.append((r * c, y, r * s))
            normals.append((nr * c, ny_, nr * s))
            uvs.append((a / n_around, v_of(y)))
    for i in range(len(prof) - 1):
        for a in range(n_around):
            i00, i01 = ring_start[i] + a, ring_start[i] + a + 1
            i10, i11 = ring_start[i + 1] + a, ring_start[i + 1] + a + 1
            faces.append((i00, i10, i11))
            faces.append((i00, i11, i01))
    # tapas
    for ring, y, ny, sign in ((0, prof[0][0], -1.0, -1), (len(prof) - 1, prof[-1][0], 1.0, 1)):
        ci = len(verts)
        verts.append((0.0, y, 0.0)); normals.append((0.0, ny, 0.0)); uvs.append((0.5, v_of(y)))
        for a in range(n_around):
            p0, p1 = ring_start[ring] + a, ring_start[ring] + a + 1
            faces.append((ci, p1, p0) if sign < 0 else (ci, p0, p1))
    return verts, faces, normals, uvs


def _band_rows(S):
    """Filas de la textura (y0, y1) que ocupa cada tramo del perfil."""
    prof = profile()
    out = []
    for (ya, _, lab), (yb, _, _) in zip(prof[:-1], prof[1:]):
        r0, r1 = v_of(yb) * (S - 1), v_of(ya) * (S - 1)
        out.append((int(math.floor(min(r0, r1))), int(math.ceil(max(r0, r1))), lab))
    return out


def blade_colors(color):
    """Paleta de la hoja a partir del color del cristal: nucleo casi blanco y borde de color."""
    r, g, b = color
    core = (255, int(235 + (g / 255) * 20), int(228 + (b / 255) * 27))
    mid = tuple(int(255 * 0.55 + c * 0.45) for c in color)
    return core, mid, tuple(color)


def make_texture(path, color=(255, 30, 24), S=256):
    """Textura del sable. La hoja es 'incandescente': casi blanca, con el color del cristal
    concentrado en la punta y junto al emisor; la empunadura es metal con detalles."""
    core, mid, edge = blade_colors(color)
    im = Image.new('RGBA', (S, S), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    chrome, chrome_hi, chrome_lo = (170, 174, 182), (220, 224, 232), (96, 100, 108)
    black, black_hi = (28, 28, 32), (58, 58, 64)
    for y0, y1, lab in _band_rows(S):
        for yy in range(y0, y1 + 1):
            for x in range(S):
                u = x / (S - 1)
                shine = 0.5 + 0.5 * math.cos(2 * math.pi * (u - 0.15))   # reflejo del metal
                if lab in ('pommel', 'band', 'shroud', 'shroud_lip', 'emitter'):
                    base = chrome_lo if lab == 'emitter' else chrome
                    col = tuple(int(base[i] + (chrome_hi[i] - base[i]) * shine * 0.8) for i in range(3))
                elif lab == 'pommel_ring':
                    col = black_hi
                elif lab == 'grip_ridge':
                    col = tuple(int(black_hi[i] + 30 * shine) for i in range(3))
                elif lab == 'grip':
                    col = black
                else:  # blade
                    # En el juego no hay 'bloom': si la hoja fuera blanca se veria rosada y palida.
                    # Cuerpo de color vivo y claro, con una franja caliente (casi blanca) que
                    # recorre la hoja, y el color puro en la base y la punta.
                    t = 1 - (yy / (S - 1)) / HILT_V          # 0 junto al emisor, 1 en la punta
                    hot = max(0.0, math.cos(2 * math.pi * (u - 0.15))) ** 3
                    body = tuple(int(edge[i] * 0.72 + 255 * 0.28 + (core[i] - edge[i] * 0.72 - 255 * 0.28) * hot * 0.8)
                                 for i in range(3))
                    if t < 0.05:
                        k = t / 0.05
                        col = tuple(int(edge[i] + (body[i] - edge[i]) * k) for i in range(3))
                    elif t > 0.94:
                        k = (t - 0.94) / 0.06
                        col = tuple(int(body[i] + (edge[i] - body[i]) * k) for i in range(3))
                    else:
                        col = body
                im.putpixel((x, yy), col + (255,))
    rows = {lab: (y0, y1) for y0, y1, lab in _band_rows(S)}
    # boton de encendido rojo y ventilas del emisor
    by = [r for r in _band_rows(S) if r[2] == 'band']
    if by:
        y0, y1 = min(r[0] for r in by), max(r[1] for r in by)
        d.rectangle([int(S * 0.20), y0 + 2, int(S * 0.27), y1 - 2], fill=(200, 20, 20))
        d.rectangle([int(S * 0.205), y0 + 3, int(S * 0.225), y1 - 4], fill=(255, 120, 110))
        d.line([(0, y0), (S, y0)], fill=chrome_lo, width=1)
        d.line([(0, y1), (S, y1)], fill=chrome_lo, width=1)
    sh = [r for r in _band_rows(S) if r[2] in ('shroud', 'shroud_lip')]
    if sh:
        y0, y1 = min(r[0] for r in sh), max(r[1] for r in sh)
        for k in range(8):
            x = int((k + 0.5) / 8 * S)
            d.rectangle([x - 3, y0 + 3, x + 3, y1 - 3], fill=(40, 40, 46))
    im.save(path)
    return im


def make_poster(path, color=(255, 30, 24), size=512, title='SABLE DE LUZ'):
    """Poster del mod: sable en diagonal con resplandor."""
    im = Image.new('RGB', (size, size), (10, 10, 16))
    glow = Image.new('RGB', (size, size), (0, 0, 0))
    g = ImageDraw.Draw(glow)
    a, b = (size * 0.30, size * 0.78), (size * 0.84, size * 0.16)
    hilt_a, hilt_b = (size * 0.14, size * 0.96), a
    g.line([a, b], fill=tuple(color), width=int(size * 0.075))
    glow = glow.filter(ImageFilter.GaussianBlur(size * 0.045))
    im = Image.blend(im, glow, 1.0)
    im = Image.fromarray(np.clip(np.asarray(im, float) * 1.4 + 10, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    core, mid, edge = blade_colors(color)
    d.line([a, b], fill=mid, width=int(size * 0.034))
    d.line([a, b], fill=core, width=int(size * 0.020))
    d.line([hilt_a, hilt_b], fill=(150, 154, 162), width=int(size * 0.05))
    for k in range(6):
        t = 0.2 + k * 0.1
        p = (hilt_a[0] + (hilt_b[0] - hilt_a[0]) * t, hilt_a[1] + (hilt_b[1] - hilt_a[1]) * t)
        d.ellipse([p[0] - size * 0.018, p[1] - size * 0.018, p[0] + size * 0.018, p[1] + size * 0.018],
                  fill=(35, 35, 40))
    try:
        from PIL import ImageFont
        f = ImageFont.load_default(size=int(size * 0.09))
        tw = d.textlength(title, font=f)
        d.text(((size - tw) / 2 + 3, size * 0.05 + 3), title, font=f, fill=(0, 0, 0))
        d.text(((size - tw) / 2, size * 0.05), title, font=f, fill=(255, 235, 230))
    except Exception:
        pass
    im.save(path)
