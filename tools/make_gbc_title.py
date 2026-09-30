"""Painting + grunge title  ->  Game Boy Color background data (src/title_data.c)
Run: python3 tools/make_gbc_title.py     (needs Pillow, numpy, opencv-python)

Screen layout (160x144, see src/title.c):
  lines   0- 63  TOP BAND   : 20x8 tiles at BG map rows 0-7. Static. Title text is baked into it.
  lines  64-127  LOWER BAND : the painting drifts here (SCX/SCY are changed by a LYC interrupt at line 63).
                              26x11 tiles at BG map rows 8-18, columns 0-25.
  lines 128-143  WINDOW     : PRESS START on black (20x2 tiles, window map).
Palettes (8 BG palettes of 4 colours):
  0-3 painting     4-6 title text (colour 0 = flat backdrop colour of that tile, 1 outline, 2 cream, 3 tan)
  7   PRESS START (black, outline, cream, tan)
VRAM: two banks of 256 BG tiles.  Band + PRESS START tiles first, painting tiles fill the rest of bank 0, then bank 1.
"""
import sys, random
sys.path.insert(0, 'tools')
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from gbc_common import *

random.seed(7); rng = np.random.default_rng(7)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
SS = 4
BAND_W, BAND_H = 20, 8          # tiles
LOW_W, LOW_H = 26, 11
WORLD_W = LOW_W * 8             # 208
BAND_X0 = 24                    # band shows world x 24..183
LOW_Y0 = 52                     # lower band tile row 0 = world y 52
CROP_Y = 4                      # first painting row used

# ------------------------------------------------------------------ painting
im = cv2.imread('assets/painting_stitched.png')
H_full = int(round(WORLD_W * im.shape[0] / im.shape[1]))
im = cv2.resize(im, (WORLD_W, H_full), interpolation=cv2.INTER_AREA)
f = im.astype(np.float32) / 255.0
f = np.power(f, 1.25) * 0.92                                    # darker, so the title text pops (same look as the GBA build)
lab = cv2.cvtColor(f, cv2.COLOR_BGR2LAB)
lab[..., 0] = np.clip((lab[..., 0] - 50) * 1.12 + 47, 0, 100)
f = np.clip(cv2.cvtColor(lab, cv2.COLOR_LAB2BGR), 0, 1)
world = (f[..., ::-1] * 255.0)[CROP_Y:CROP_Y + 140]             # RGB float, 208 x 140

def vignette(y):                                                # darker near the seam between the bands
    y = np.asarray(y, np.float32)
    top = np.where(y < 44, 1.0, 1.0 - 0.45 * np.clip((y - 44) / 19.0, 0, 1))
    low = 0.55 + 0.45 * np.clip((y - 60) / 30.0, 0, 1)
    return np.where(y < 64, top, low)
band_img = world[0:64, BAND_X0:BAND_X0 + 160] * vignette(np.arange(0, 64))[:, None, None]
low_img = world[LOW_Y0:LOW_Y0 + LOW_H * 8, :] * vignette(np.arange(LOW_Y0, LOW_Y0 + LOW_H * 8))[:, None, None]

def to_tiles(img, tw, th):
    return img.reshape(th, 8, tw, 8, 3).transpose(0, 2, 1, 3, 4).reshape(th * tw, 64, 3)

# ------------------------------------------------------------------ title text (placeholder grunge, as make_text.py on GBA)
def fit(text, width, maxh):
    lo, hi = 6, 200
    while lo < hi:
        mid = (lo + hi + 1) // 2
        fo = ImageFont.truetype(FONT, mid)
        if fo.getlength(text) <= width and mid <= maxh: lo = mid
        else: hi = mid - 1
    return ImageFont.truetype(FONT, lo)

def line(canvas, text, width, size_cap, cy, jitter):
    fo = fit(text, width * SS, size_cap * SS)
    total = sum(fo.getlength(c) for c in text)
    cap = fo.getbbox('H', anchor='ls'); capH = -cap[1]
    base = cy * SS + capH / 2                                   # cy = vertical centre of the capital letters
    x = (canvas.width - total) / 2
    for c in text:
        w = fo.getlength(c)
        if c != ' ':
            g = Image.new('L', (int(w * 2 + 20), int(fo.size * 2)), 0)
            gy = int(fo.size * 1.4)
            ImageDraw.Draw(g).text((g.width // 2 - w / 2, gy), c, font=fo, fill=255, anchor='ls')
            g = g.rotate(random.uniform(-jitter, jitter), resample=Image.BICUBIC)
            dy = random.uniform(-0.05, 0.05) * fo.size
            canvas.paste(255, (int(x - g.width / 2 + w / 2), int(base - gy + dy)), g)
        x += w

def grunge(mask_ss, strength):
    h, w = mask_ss.shape
    n1 = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 3)
    n2 = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 3)
    n1 = (n1 - n1.mean()) / n1.std(); n2 = (n2 - n2.mean()) / n2.std()
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    m = cv2.remap(mask_ss, xx + n1 * 2.2 * strength, yy + n2 * 2.2 * strength, cv2.INTER_LINEAR)
    bite = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 1.6)
    bite = (bite - bite.mean()) / bite.std()
    m = np.where(bite > 1.9 - 0.3 * strength, 0, m)
    return cv2.resize(m, (w // SS, h // SS), interpolation=cv2.INTER_AREA)

def colourise(cov):
    """coverage -> indices (0 clear, 1 outline, 2 cream, 3 tan)"""
    fill = cov > 120
    k = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], np.uint8)
    edge = cv2.dilate(fill.astype(np.uint8), k) > 0
    sh = np.zeros_like(edge); sh[1:, 1:] = edge[:-1, :-1]; shadow = sh & ~edge
    out = np.zeros(cov.shape, np.uint8)
    out[shadow] = 1; out[edge & ~fill] = 1
    out[fill] = 2
    h, w = cov.shape
    t = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 1.0)
    t = (t - t.mean()) / t.std()
    out[fill & (t > 1.25)] = 3
    yy = np.arange(h)[:, None]
    out[fill & (yy % 8 >= 6) & (t > 0.6)] = 3
    for _ in range(int(w * h / 140)):                           # scratches
        x, y = random.randrange(w), random.randrange(h); L = random.randrange(3, 9)
        for i in range(L):
            if 0 <= x + i < w and 0 <= y + i // 5 < h and out[y + i // 5, x + i] == 2:
                out[y + i // 5, x + i] = 3 if random.random() < 0.6 else 1
    return out

def build(lines, tw, th, jitter, strength):
    canvas = Image.new('L', (tw * 8 * SS, th * 8 * SS), 0)
    for text, width, cap, cy in lines: line(canvas, text, width, cap, cy, jitter)
    return colourise(grunge(np.array(canvas, np.float32), strength))

# widths / cap heights / centres picked to match the preview (160x64 title band, 160x16 strip)
title = build([('The', 24, 10, 12), ('LAST DAYS', 122, 20, 33), ('of danny steel', 112, 14, 54)], BAND_W, BAND_H, 2.5, 0.55)
press = build([('PRESS START', 74, 8, 8)], 20, 2, 1.0, 0.3)

# ------------------------------------------------------------------ palettes + tiles
band_tiles = to_tiles(band_img, BAND_W, BAND_H)
low_tiles = to_tiles(low_img, LOW_W, LOW_H)
title_tiles_idx = title.reshape(BAND_H, 8, BAND_W, 8).transpose(0, 2, 1, 3).reshape(-1, 8, 8)
has_text = title_tiles_idx.reshape(len(title_tiles_idx), 64).max(1) > 0

paint_src = np.concatenate([band_tiles[~has_text], low_tiles])
pals, grp = fit_palettes(paint_src, 4)
grp_band = np.zeros(len(band_tiles), int); grp_band[~has_text] = grp[:(~has_text).sum()]
grp_low = grp[(~has_text).sum():]

# flat backdrop colours for tiles carrying text: 3 clusters of the mean colour under the text
tm = band_tiles[has_text].mean(1)
bgc = snap5(kmeans_colors(tm, 3))
bg_of = _d = None
tile_bg = np.zeros(len(band_tiles), int)
d = ((tm[:, None, :] - bgc[None].astype(np.float32)) ** 2 * W_RGB).sum(-1)
tile_bg[has_text] = d.argmin(1)

TEXT_COL = [(0x14, 0x08, 0x0a), (0xf4, 0xe8, 0xc6), (0xc4, 0x9a, 0x5c)]      # outline, cream, tan (as on GBA)
pal_words = []
for p in range(4):
    pal_words += [rgb555(*pals[p][i]) for i in range(4)]
for k in range(3):
    pal_words += [rgb555(*bgc[k])] + [rgb555(*c) for c in TEXT_COL]
pal_words += [0] + [rgb555(*c) for c in TEXT_COL]                             # 7 = PRESS START on black

tiles = {0: [], 1: []}          # bank -> list of tile bytes
lookup = {}                     # (bytes, ) -> (bank, index)
def add_tile(data, prefer_bank):
    if data in lookup: return lookup[data]
    for b in (prefer_bank, 1 - prefer_bank):
        if len(tiles[b]) < 256:
            tiles[b].append(data); lookup[data] = (b, len(tiles[b]) - 1); return lookup[data]
    raise SystemExit('out of VRAM tiles (512 max)')

def emit_map(cells, w, h):
    m = bytearray(); a = bytearray()
    for (bank, idx, pal) in cells:
        m.append(idx); a.append(pal | (bank << 3))
    return m, a

# band (bank 0 first)
band_cells = []
for i in range(len(band_tiles)):
    if has_text[i]:
        px = title_tiles_idx[i]; pal = 4 + tile_bg[i]
    else:
        px = dither_tile(band_tiles[i], pals[grp_band[i]]); pal = grp_band[i]
    b, idx = add_tile(enc_tile(px), 0)
    band_cells.append((b, idx, pal))
# PRESS START (window)
press_idx = press.reshape(2, 8, 20, 8).transpose(0, 2, 1, 3).reshape(-1, 8, 8)
press_cells = []
for i in range(len(press_idx)):
    b, idx = add_tile(enc_tile(press_idx[i]), 0)
    press_cells.append((b, idx, 7))
n_fixed = sum(len(v) for v in tiles.values())
# lower band
low_cells = []
for i in range(len(low_tiles)):
    px = dither_tile(low_tiles[i], pals[grp_low[i]])
    b, idx = add_tile(enc_tile(px), 0)
    low_cells.append((b, idx, grp_low[i]))

bm, ba = emit_map(band_cells, BAND_W, BAND_H)
lm, la = emit_map(low_cells, LOW_W, LOW_H)
pm, pa = emit_map(press_cells, 20, 2)
t0 = b''.join(tiles[0]); t1 = b''.join(tiles[1])

with open('src/title_data.c', 'w') as o:
    o.write('// GENERATED by tools/make_gbc_title.py - do not edit\n#include "data.h"\n')
    o.write(c_words('title_pal', pal_words))
    o.write('const unsigned int title_tiles0_count = %d;\nconst unsigned int title_tiles1_count = %d;\n' % (len(tiles[0]), len(tiles[1])))
    o.write(c_bytes('title_tiles0', t0)); o.write(c_bytes('title_tiles1', t1))
    o.write(c_bytes('title_band_map', bm, 20)); o.write(c_bytes('title_band_attr', ba, 20))
    o.write(c_bytes('title_low_map', lm, 26)); o.write(c_bytes('title_low_attr', la, 26))
    o.write(c_bytes('press_map', pm, 20)); o.write(c_bytes('press_attr', pa, 20))
print('bank0 tiles %d, bank1 tiles %d (max 256 each); text tiles %d of %d band tiles; painting tiles %d'
      % (len(tiles[0]), len(tiles[1]), has_text.sum(), len(band_tiles), len(low_tiles)))
print('bytes: %d' % (len(t0) + len(t1) + len(bm) * 2 + len(lm) * 2 + len(pm) * 2 + 64))
