"""Construye la marca Safary desde la referencia aprobada, sin IA generativa.

Uso: python tools/build_reference_brand.py /ruta/referencia.jpg static/brand
"""
from collections import deque
from pathlib import Path
import sys

from PIL import Image, ImageChops, ImageFilter

UBUNTU_ORANGE = (233, 84, 32)
AUBERGINE = (44, 0, 30)
LIGHT_AUBERGINE = (119, 41, 83)


def dark_ink(rgb):
    r, g, b = rgb
    # La referencia usa tinta azul marino sobre blanco. Umbral conservador.
    return b < 170 and r < 175 and g < 185 and (255 - (r + g + b) / 3) > 52


def components(image, max_y):
    w, h = image.size
    px = image.load()
    seen = set()
    rows = []
    for y in range(min(h, max_y)):
        for x in range(w):
            if (x, y) in seen or not dark_ink(px[x, y]):
                continue
            stack = [(x, y)]
            seen.add((x, y))
            points = []
            while stack:
                xx, yy = stack.pop()
                points.append((xx, yy))
                for nx, ny in ((xx + 1, yy), (xx - 1, yy), (xx, yy + 1), (xx, yy - 1)):
                    if not (0 <= nx < w and 0 <= ny < min(h, max_y)) or (nx, ny) in seen:
                        continue
                    if dark_ink(px[nx, ny]):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            if len(points) > 100:
                rows.append(points)
    return sorted(rows, key=len, reverse=True)


def render(reference, output):
    image = Image.open(reference).convert('RGB')
    comps = components(image, max_y=int(image.height * 0.49))
    if len(comps) < 2:
        raise RuntimeError('No se detectaron las siluetas principales.')
    # 1: círculo+Safary; 2: Sebastián. Olas/texto son componentes menores.
    dog_circle, human = comps[:2]
    selected = set(dog_circle) | set(human)
    xs = [p[0] for p in selected]
    ys = [p[1] for p in selected]
    margin = 18
    box = (max(0, min(xs) - margin), max(0, min(ys) - margin),
           min(image.width, max(xs) + margin + 1), min(image.height, max(ys) + margin + 1))
    cw, ch = box[2] - box[0], box[3] - box[1]

    main_mask = Image.new('L', (cw, ch), 0)
    human_mask = Image.new('L', (cw, ch), 0)
    mp, hp = main_mask.load(), human_mask.load()
    dog_set = set(dog_circle)
    for x, y in selected:
        target = mp if (x, y) in dog_set else hp
        target[x - box[0], y - box[1]] = 255

    # Suavizado subpíxel mínimo; conserva la composición original.
    main_mask = main_mask.filter(ImageFilter.GaussianBlur(0.45))
    human_mask = human_mask.filter(ImageFilter.GaussianBlur(0.45))
    total_alpha = ImageChops.lighter(main_mask, human_mask)

    mono = Image.new('RGBA', (cw, ch), AUBERGINE + (0,))
    mono.putalpha(total_alpha)

    colour = Image.new('RGBA', (cw, ch), AUBERGINE + (0,))
    colour.putalpha(total_alpha)
    # Sebastián en aubergine más claro para separar planos sin romper monocromía.
    human_layer = Image.new('RGBA', (cw, ch), LIGHT_AUBERGINE + (0,))
    human_layer.putalpha(human_mask)
    colour.alpha_composite(human_layer)

    # Acento Ubuntu: anillo exterior, calculado desde el círculo original.
    # El círculo real se conserva; solo cambia de color cerca de su radio.
    cx = ((86 + 618) / 2) - box[0]
    cy = ((164 + 709) / 2) - box[1]
    radius = ((618 - 86) / 2 + (709 - 164) / 2) / 2
    ring = Image.new('L', (cw, ch), 0)
    rp = ring.load()
    mm = main_mask.load()
    for y in range(ch):
        for x in range(cw):
            distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if abs(distance - radius) <= 4.5 and mm[x, y] > 80:
                rp[x, y] = mm[x, y]
    orange_layer = Image.new('RGBA', (cw, ch), UBUNTU_ORANGE + (0,))
    orange_layer.putalpha(ring)
    colour.alpha_composite(orange_layer)

    output.mkdir(parents=True, exist_ok=True)
    mono.save(output / 'safary-reference-mono.png', optimize=True)
    colour.save(output / 'safary-reference-ubuntu.png', optimize=True)

    # Raster masters and optical sizes. 16/32 use the authentic already-tested composition.
    for size in (16, 32, 64, 192, 512):
        for stem, source in (('mono', mono), ('ubuntu', colour)):
            canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            fitted = source.copy()
            fitted.thumbnail((size, size), Image.Resampling.LANCZOS)
            canvas.alpha_composite(fitted, ((size - fitted.width) // 2, (size - fitted.height) // 2))
            canvas.save(output / f'safary-{stem}-{size}.png', optimize=True)
    print(f'componentes={len(comps)} principal={len(dog_circle)} humano={len(human)} box={box}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('Uso: build_reference_brand.py referencia.jpg directorio_salida')
    render(Path(sys.argv[1]), Path(sys.argv[2]))
