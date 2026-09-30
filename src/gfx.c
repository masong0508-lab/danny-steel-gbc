#include "gbc.h"

void lcd_off(void) {
    if (rLCDC & LCDC_ON) {
        while (rLY < 144);                       // only switch the LCD off during VBlank
        rLCDC &= (u8)~LCDC_ON;
    }
}
void vcopy(u16 dst, const u8 *src, u16 n) {      // LCD must be off (or VRAM otherwise accessible)
    volatile u8 *d = (volatile u8 *)dst;
    while (n--) *d++ = *src++;
}
void vfill(u16 dst, u8 v, u16 n) {
    volatile u8 *d = (volatile u8 *)dst;
    while (n--) *d++ = v;
}
static u16 fade_col(u16 c, u8 lvl) {
    u8 m = (u8)(16 - lvl);
    u16 r = c & 31, g = (c >> 5) & 31, b = (c >> 10) & 31;
    r = (r * m) >> 4; g = (g * m) >> 4; b = (b * m) >> 4;
    return r | (g << 5) | (b << 10);
}
void bpal_write(const u16 *c, u8 first, u8 n, u8 lvl) {
    rBCPS = 0x80 | (u8)(first * 2);              // bit 7: auto-increment
    while (n--) {
        u16 v = lvl ? fade_col(*c, lvl) : *c; c++;
        while (rSTAT & 2);                       // palette RAM is locked while the LCD reads OAM/VRAM
        rBCPD = (u8)v;
        while (rSTAT & 2);
        rBCPD = (u8)(v >> 8);
    }
}
void opal_write(const u16 *c, u8 first, u8 n, u8 lvl) {
    rOCPS = 0x80 | (u8)(first * 2);
    while (n--) {
        u16 v = lvl ? fade_col(*c, lvl) : *c; c++;
        while (rSTAT & 2);
        rOCPD = (u8)v;
        while (rSTAT & 2);
        rOCPD = (u8)(v >> 8);
    }
}
