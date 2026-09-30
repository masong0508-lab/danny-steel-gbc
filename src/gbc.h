#pragma once
// Game Boy Color hardware access (raw registers, so nothing depends on GBDK's register names).
#include <gb/gb.h>
#include <stdint.h>
typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32; typedef int8_t s8; typedef int16_t s16; typedef int32_t s32;

#ifdef HOST_TEST                                  // tools/host_test: run the code on a PC against a fake memory map
volatile u8 *host_addr(u16 a);
#define R8(a) (*host_addr((u16)(a)))
#else
#define R8(a) (*(volatile u8 *)(a))
#endif
#define rLCDC R8(0xFF40)
#define rSTAT R8(0xFF41)
#define rSCY  R8(0xFF42)
#define rSCX  R8(0xFF43)
#define rLY   R8(0xFF44)
#define rLYC  R8(0xFF45)
#define rWY   R8(0xFF4A)
#define rWX   R8(0xFF4B)
#define rVBK  R8(0xFF4F)
#define rBCPS R8(0xFF68)
#define rBCPD R8(0xFF69)
#define rOCPS R8(0xFF6A)
#define rOCPD R8(0xFF6B)
#define rTIMA R8(0xFF05)
#define rTMA  R8(0xFF06)
#define rTAC  R8(0xFF07)
// sound
#define rNR10 R8(0xFF10)
#define rNR11 R8(0xFF11)
#define rNR12 R8(0xFF12)
#define rNR13 R8(0xFF13)
#define rNR14 R8(0xFF14)
#define rNR21 R8(0xFF16)
#define rNR22 R8(0xFF17)
#define rNR23 R8(0xFF18)
#define rNR24 R8(0xFF19)
#define rNR30 R8(0xFF1A)
#define rNR32 R8(0xFF1C)
#define rNR33 R8(0xFF1D)
#define rNR34 R8(0xFF1E)
#define rNR42 R8(0xFF21)
#define rNR43 R8(0xFF22)
#define rNR44 R8(0xFF23)
#define rNR50 R8(0xFF24)
#define rNR51 R8(0xFF25)
#define rNR52 R8(0xFF26)
#define WAVE_RAM (&R8(0xFF30))

// LCDC bits
#define LCDC_ON     0x80
#define LCDC_WIN9C  0x40
#define LCDC_WINON  0x20
#define LCDC_BG8000 0x10
#define LCDC_OBJ16  0x04
#define LCDC_OBJON  0x02
#define LCDC_BGON   0x01

// scroll values applied by the VBlank / LYC interrupts (see main.c)
extern volatile u8 g_top_scx, g_top_scy, g_low_scx, g_low_scy;

// helpers (gfx.c)
void lcd_off(void);
void vcopy(u16 dst, const u8 *src, u16 n);
void vfill(u16 dst, u8 v, u16 n);
void bpal_write(const u16 *c, u8 first, u8 n, u8 lvl);   // BG colours, faded to black by lvl (0 = as is, 16 = black)
void opal_write(const u16 *c, u8 first, u8 n, u8 lvl);   // sprite colours
