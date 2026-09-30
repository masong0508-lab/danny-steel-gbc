#pragma once
// logo_play(): plays the ~8 s DippInn logo (blocking). Call once at boot; leaves the LCD off with black palettes.
// Uses BG + sprites (8x16), the LYC interrupt for the two-speed parallax split, and palette fades.
void logo_play(void);
#define LOGO_FRAMES (359 + 120)   /* +120 frames (2 s) hold before the fade-out */
