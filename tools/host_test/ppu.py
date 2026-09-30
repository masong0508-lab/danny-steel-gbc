"""Tiny GBC PPU model: renders a snapshot written by host.c (VRAM banks, palettes, OAM, scroll split, window)."""
import sys, numpy as np
sys.path.insert(0, 'tools')
from gbc_common import unpack555
from render_preview import decode_tile

def load(fn):
    d = open(fn, 'rb').read()
    v0, v1 = d[:8192], d[8192:16384]
    bg = d[16384:16448]; ob = d[16448:16512]; oam = d[16512:16672]; regs = d[16672:16680]
    return v0, v1, bg, ob, oam, regs, d[16680]
def pal(ram):
    return np.array([unpack555(ram[i] | ram[i + 1] << 8) for i in range(0, 64, 2)], np.uint8).reshape(8, 4, 3)
def render(fn, lyc_split=True):
    v0, v1, bgr, obr, oam, regs, wx = load(fn)
    lcdc, tsx, tsy, lsx, lsy, lyc, wy, lycen = regs
    P = pal(bgr); O = pal(obr); vr = [v0, v1]
    def tile(bank, n, base8000=True):
        return decode_tile(vr[bank][n * 16:n * 16 + 16])
    mapbase = 0x1800
    cache = {}
    idx = np.zeros((256, 256), np.uint8); col = np.zeros((256, 256, 3), np.uint8); pr = np.zeros((256, 256), bool)
    for r in range(32):
        for c in range(32):
            n = v0[mapbase + r * 32 + c]; a = v1[mapbase + r * 32 + c]
            t = tile((a >> 3) & 1, n)
            idx[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = t; col[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = P[a & 7][t]; pr[r * 8:r * 8 + 8, c * 8:c * 8 + 8] = bool(a & 0x80)
    wmap = 0x1C00 if lcdc & 0x40 else 0x1800
    fr = np.zeros((144, 160, 3), np.uint8); fi = np.zeros((144, 160), np.uint8); fp = np.zeros((144, 160), bool)
    if not lcdc & 0x80: return fr
    for L in range(144):
        split = lycen and L > lyc
        sx, sy = (lsx, lsy) if split else (tsx, tsy)
        if not lycen: sx, sy = tsx, tsy
        y = (sy + L) & 255; cols = (sx + np.arange(160)) & 255
        fr[L] = col[y, cols]; fi[L] = idx[y, cols]; fp[L] = pr[y, cols]
        if lcdc & 0x20 and L >= wy:
            wl = L - wy
            for c in range(20):
                n = v0[wmap + (wl // 8) * 32 + c]; a = v1[wmap + (wl // 8) * 32 + c]
                t = tile((a >> 3) & 1, n)[wl % 8]
                fr[L, c * 8:c * 8 + 8] = P[a & 7][t]
    if lcdc & 2:
        for s in range(40):
            y, x, t, a = oam[s * 4:s * 4 + 4]
            if y == 0: continue
            X, Y = x - 8, y - 16
            for half in range(2):
                td = decode_tile(vr[0][(t + half) * 16 + 0x0000 + 0:(t + half) * 16 + 16]) if False else None
            for h in range(2):
                tt = decode_tile(vr[0][(t + h) * 16 : (t + h) * 16 + 16]) if True else None
                for yy in range(8):
                    for xx in range(8):
                        px, py = X + xx, Y + h * 8 + yy
                        if 0 <= px < 160 and 0 <= py < 144 and tt[yy, xx] and not (fp[py, px] and fi[py, px]):
                            fr[py, px] = O[a & 7][tt[yy, xx]]
    return fr
if __name__ == '__main__':
    from PIL import Image
    names = sys.argv[2:]; frs = [render(n) for n in names]
    Image.fromarray(np.concatenate(frs, 1)).resize((160 * len(frs) * 2, 288), Image.NEAREST).save(sys.argv[1])
