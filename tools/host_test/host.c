// Host-side fake hardware: memory map, VRAM banks, palette RAM, OAM, snapshots for tools/host_test/ppu.py
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include "gbc.h"

static u8 mem[65536];
static u8 vram[2][8192];
u8 host_bgpal[64], host_objpal[64];
static u8 oam[40][4];
static int_handler h_vbl, h_lcd, h_tim;
volatile u8 g_top_scx, g_top_scy, g_low_scx, g_low_scy;
int host_frame = 0;
u8 host_joy = 0;
void (*host_hook)(int frame);

volatile u8 *host_addr(u16 a) {
    static int init = 0;
    if (!init) { init = 1; mem[0xFF44] = 144; mem[0xFF40] = 0x80; }
    if (a >= 0x8000 && a < 0xA000) return &vram[mem[0xFF4F] & 1][a - 0x8000];
    return &mem[a];
}
void add_VBL(int_handler h) { h_vbl = h; } void add_LCD(int_handler h) { h_lcd = h; } void add_TIM(int_handler h) { h_tim = h; }
void set_interrupts(uint8_t f) { (void)f; } void enable_interrupts(void) {} void disable_interrupts(void) {}
void tim_tick(void) { if (h_tim) h_tim(); }
uint8_t joypad(void) { return host_joy; }
void wait_vbl_done(void) {
    if (host_hook) host_hook(host_frame);
    host_frame++;
}
void hide_sprite(uint8_t nb) { oam[nb][0] = 0; }
void set_sprite_tile(uint8_t nb, uint8_t t) { oam[nb][2] = t; }
void set_sprite_prop(uint8_t nb, uint8_t p) { oam[nb][3] = p; }
void move_sprite(uint8_t nb, uint8_t x, uint8_t y) { oam[nb][1] = x; oam[nb][0] = y; }

// same helpers as src/gfx.c, palette RAM replaced by arrays
void lcd_off(void) { R8(0xFF40) &= (u8)~0x80; }
void vcopy(u16 dst, const u8 *src, u16 n) { while (n--) R8(dst++) = *src++; }
void vfill(u16 dst, u8 v, u16 n) { while (n--) R8(dst++) = v; }
static u16 fade_col(u16 c, u8 lvl) {
    u8 m = (u8)(16 - lvl);
    u16 r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31;
    r = (r * m) >> 4; g = (g * m) >> 4; b = (b * m) >> 4;
    return r | (g << 5) | (b << 10);
}
static void pal(u8 *ram, const u16 *c, u8 first, u8 n, u8 lvl) {
    u8 i = first * 2;
    while (n--) {
        u16 v = lvl ? fade_col(*c, lvl) : *c; c++;
        ram[i++] = (u8)v; ram[i++] = (u8)(v >> 8);
    }
}
void bpal_write(const u16 *c, u8 first, u8 n, u8 lvl) { pal(host_bgpal, c, first, n, lvl); }
void opal_write(const u16 *c, u8 first, u8 n, u8 lvl) { pal(host_objpal, c, first, n, lvl); }

void host_snapshot(const char *name) {
    char fn[128]; snprintf(fn, sizeof fn, "%s.bin", name);
    FILE *f = fopen(fn, "wb");
    fwrite(vram[0], 1, 8192, f); fwrite(vram[1], 1, 8192, f);
    fwrite(host_bgpal, 1, 64, f); fwrite(host_objpal, 1, 64, f); fwrite(oam, 1, 160, f);
    u8 regs[8] = { mem[0xFF40], g_top_scx, g_top_scy, g_low_scx, g_low_scy, mem[0xFF45], mem[0xFF4A], (u8)((mem[0xFF41] & 0x40) | (mem[0xFF4B] & 0x3F)) };
    u8 wx = mem[0xFF4B]; regs[7] = (mem[0xFF41] & 0x40) ? 1 : 0;
    fwrite(regs, 1, 8, f); fwrite(&wx, 1, 1, f);
    fclose(f);
}
u8 host_reg(u16 a) { return mem[a]; }
