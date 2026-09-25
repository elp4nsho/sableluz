"""Iconos de inventario (32 px): se dibujan a 256 px, se reducen y llevan contorno de 1 px."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from saber import blade_colors

W = 256


def _finish(big, size=32, outline=(20, 20, 24, 255)):
    small = big.resize((size - 2, size - 2), Image.LANCZOS)
    rgb = small.convert('RGB').filter(ImageFilter.UnsharpMask(radius=1, percent=70, threshold=2))
    rgb.putalpha(small.getchannel('A'))
    icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    icon.alpha_composite(rgb, (1, 1))
    arr = np.asarray(icon).copy()
    solid = arr[..., 3] >= 110
    grow = solid.copy()
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        grow |= np.roll(np.roll(solid, dy, 0), dx, 1)
    arr[..., 3] = np.where(solid, 255, 0)
    arr[grow & ~solid] = outline
    return Image.fromarray(arr, 'RGBA')


def _glow_line(im, a, b, color, width):
    """Linea con halo: resplandor difuso de color + nucleo claro."""
    core, mid, edge = blade_colors(color)
    glow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(glow).line([a, b], fill=tuple(edge) + (230,), width=int(width * 2.2))
    glow = glow.filter(ImageFilter.GaussianBlur(width * 0.35))
    im.alpha_composite(glow)
    d = ImageDraw.Draw(im)
    d.line([a, b], fill=tuple(mid) + (255,), width=int(width * 1.2))
    d.line([a, b], fill=tuple(core) + (255,), width=int(width * 0.6))


def _hilt(im, a, b, width):
    d = ImageDraw.Draw(im)
    d.line([a, b], fill=(165, 170, 178, 255), width=width)
    for k in range(5):                                   # estrias del grip
        t = 0.15 + k * 0.13
        p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        r = width * 0.55
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=(30, 30, 34, 255))
    t = 0.86                                             # boton rojo
    p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    d.ellipse([p[0] - width * 0.3, p[1] - width * 0.3, p[0] + width * 0.3, p[1] + width * 0.3],
              fill=(220, 30, 30, 255))


def saber_icon(color=(255, 30, 24)):
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    a, b = (W * 0.36, W * 0.64), (W * 0.93, W * 0.07)       # hoja
    h0 = (W * 0.10, W * 0.90)                               # pomo
    _glow_line(im, a, b, color, W * 0.075)
    _hilt(im, h0, a, int(W * 0.12))
    return _finish(im)


def hilt_icon():
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    _hilt(im, (W * 0.18, W * 0.82), (W * 0.80, W * 0.20), int(W * 0.17))
    d = ImageDraw.Draw(im)
    e = (W * 0.80, W * 0.20)                                # emisor apagado
    d.ellipse([e[0] - W * 0.11, e[1] - W * 0.11, e[0] + W * 0.11, e[1] + W * 0.11], fill=(120, 124, 132, 255))
    d.ellipse([e[0] - W * 0.05, e[1] - W * 0.05, e[0] + W * 0.05, e[1] + W * 0.05], fill=(35, 35, 40, 255))
    return _finish(im)


def crystal_icon(color=(255, 30, 24)):
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    core, mid, edge = blade_colors(color)
    glow = Image.new('RGBA', im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W * 0.2, W * 0.2, W * 0.8, W * 0.8], fill=tuple(edge) + (200,))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(W * 0.08)))
    d = ImageDraw.Draw(im)
    top, bot = (W * 0.5, W * 0.10), (W * 0.5, W * 0.90)
    l, r = (W * 0.30, W * 0.42), (W * 0.70, W * 0.42)
    l2, r2 = (W * 0.34, W * 0.66), (W * 0.66, W * 0.66)
    d.polygon([top, r, r2, bot, l2, l], fill=tuple(edge) + (255,))
    d.polygon([top, (W * 0.5, W * 0.42), (W * 0.5, W * 0.66), bot, l2, l], fill=tuple(mid) + (255,))
    d.polygon([top, (W * 0.42, W * 0.40), (W * 0.46, W * 0.60), (W * 0.36, W * 0.44)], fill=tuple(core) + (255,))
    return _finish(im)
