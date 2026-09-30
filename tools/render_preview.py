"""Rebuilds what the Game Boy Color would show, straight from the generated C data (a check that the
tile / attribute / palette encoding is right).   python3 tools/render_preview.py [title|logo|all]
Writes assets/gbc_title_preview.png and assets/gbc_logo_preview.png"""
import re, sys
sys.path.insert(0, 'tools')
import numpy as np
from PIL import Image
from gbc_common import unpack555

def load_c(path):
    txt = open(path).read()
    d = {}
    for m in re.finditer(r'const (?:unsigned (?:char|short|int)|signed char)\s+(\w+)(?:\[\d*\])?\s*=\s*(\{.*?\}|[-\w]+);', txt, re.S):
        body = m.group(2).strip()
        if body.startswith('{'):
            d[m.group(1)] = [int(x, 0) for x in re.findall(r'-?0x[0-9a-fA-F]+|-?\d+', body)]
        else:
            d[m.group(1)] = int(body, 0)
    return d

def decode_tile(b):
    px = np.zeros((8, 8), np.uint8)
    for y in range(8):
        lo, hi = b[2 * y], b[2 * y + 1]
        for x in range(8):
            px[y, x] = ((lo >> (7 - x)) & 1) | (((hi >> (7 - x)) & 1) << 1)
    return px

def tiles_of(data):
    return [decode_tile(data[i:i + 16]) for i in range(0, len(data), 16)]

def pal_rgb(words):
    return np.array([unpack555(w) for w in words], np.uint8).reshape(-1, 4, 3)

def draw_map(canvas, tiles_by_bank, mp, at, w, h, pal, ox=0, oy=0):
    for r in range(h):
        for c in range(w):
            i = r * w + c
            a = at[i]; t = tiles_by_bank[(a >> 3) & 1][mp[i]]
            rgb = pal[a & 7][t]
            y, x = oy + r * 8, ox + c * 8
            canvas[y:y + 8, x:x + 8] = rgb

def title_frame(d, sx, sy):
    """160x144 frame with the top band static, lower band scrolled by (sx, sy) after line 63, PRESS START window at 128"""
    tb = [tiles_of(bytes(d['title_tiles0'])), tiles_of(bytes(d['title_tiles1']))]
    pal = pal_rgb(d['title_pal'])
    bgmap = np.zeros((256, 256, 3), np.uint8)                 # 32x32 map painted
    draw_map(bgmap, tb, d['title_band_map'], d['title_band_attr'], 20, 8, pal, 0, 0)
    draw_map(bgmap, tb, d['title_low_map'], d['title_low_attr'], 26, 11, pal, 0, 64)
    win = np.zeros((16, 160, 3), np.uint8)
    draw_map(win, tb, d['press_map'], d['press_attr'], 20, 2, pal, 0, 0)
    fr = np.zeros((144, 160, 3), np.uint8)
    for L in range(128):
        if L < 64: fr[L] = bgmap[L, 0:160]
        else:
            y = (sy + L) & 255
            row = np.concatenate([bgmap[y], bgmap[y]])
            fr[L] = row[sx:sx + 160]
    fr[128:144] = win
    return fr

if __name__ == '__main__':
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if what in ('title', 'all'):
        d = load_c('src/title_data.c')
        a = title_frame(d, 24, 12); b = title_frame(d, 24 + 20, 12 + 8)
        im = Image.fromarray(np.concatenate([a, b], 1)).resize((960, 432), Image.NEAREST)
        im.save('assets/gbc_title_preview.png'); print('title preview written')

# ---------------------------------------------------------------- logo
def logo_scene(d, scx_a, scx_b, clouds, moon):
    pal = pal_rgb(d['sc_pal']); tl = tiles_of(bytes(d['sc_tiles']))
    idxb = np.zeros((144, 256), np.uint8); palb = np.zeros((144, 256), np.uint8); prio = np.zeros((144, 256), bool)
    for r in range(18):
        for c in range(32):
            i = r * 32 + c; a = d['sc_attr'][i]
            idxb[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = tl[d['sc_map'][i]]
            palb[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = a & 7; prio[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = bool(a & 0x80)
    fr = np.zeros((144, 160, 3), np.uint8); fi = np.zeros((144, 160), np.uint8); fp = np.zeros((144, 160), bool)
    for L in range(144):
        sx = scx_a if L < 96 else scx_b
        cols = (sx + np.arange(160)) & 255
        fi[L] = idxb[L, cols]; fp[L] = prio[L, cols]
        fr[L] = pal[palb[L, cols], fi[L]]
    sp = tiles_of(bytes(d['spr_tiles'])); sp_pal = pal_rgb(d['spr_pal'])
    def blit(base, x, y, pidx):
        for half in range(2):
            for t in range(2):
                tile = sp[base + half * 2 + t]
                for yy in range(8):
                    for xx in range(8):
                        X, Y = x + half * 8 + xx, y + t * 8 + yy
                        if 0 <= X < 160 and 0 <= Y < 144 and tile[yy, xx] and not (fp[Y, X] and fi[Y, X]):
                            fr[Y, X] = sp_pal[pidx][tile[yy, xx]]
    for (shape, x, y) in clouds: blit(shape * 4, x, y, 0)
    blit(12, moon[0], moon[1], 1)
    return fr

def logo_grey(d):
    pal = pal_rgb(d['gr_pal']); tl = tiles_of(bytes(d['gr_tiles']))
    fr = np.zeros((144, 160, 3), np.uint8); fr[:] = pal[0][0]
    for c in range(20):
        t = tl[2] if c < 9 else tl[1]
        fr[80:88, c * 8:c * 8 + 8] = pal[0][t]
    return fr

def logo_text(d):
    pal = pal_rgb(d['tx_pal']); tl = tiles_of(bytes(d['tx_tiles']))
    fr = np.zeros((144, 160, 3), np.uint8)
    for r in range(3):
        for c in range(20):
            fr[(8 + r) * 8:(9 + r) * 8, c * 8:c * 8 + 8] = pal[0][tl[d['tx_map'][r * 20 + c]]]
    for i in range(16):
        c = 2 + i
        fr[88:96, c * 8:c * 8 + 8] = pal[1][tl[d['rope_map'][i]]]
    return fr

if __name__ == '__main__' and what in ('logo', 'all'):
    d = load_c('src/logo_data.c')
    A = logo_scene(d, 0, 0, [(0, 17, 16), (1, 61, 36), (2, 107, 60), (0, 151, 82), (1, 30, 100)], (150, 44))
    B = logo_scene(d, 40, 70, [(1, 5, 50), (2, 60, 26), (0, 120, 14), (1, 75, 84), (0, 25, 70)], (112, 44))
    im = np.concatenate([A, B, logo_grey(d), logo_text(d)], 1)
    Image.fromarray(im).resize((1280, 288), Image.NEAREST).save('assets/gbc_logo_preview.png'); print('logo preview written')
