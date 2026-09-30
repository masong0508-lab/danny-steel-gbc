// Title screen: static title band (top 64 lines), drifting painting (lines 64-127), PRESS START window (lines 128-143).
// Map layout: band = BG map rows 0-7 cols 0-19, painting = rows 8-18 cols 0-25 (scrolled by the LYC interrupt), window map rows 0-1.
#include "title.h"
#include "data.h"
#include "music.h"

enum { ST_FADE_IN, ST_RUN, ST_FADE_OUT };
static u8 state, was_down, last_lvl, last_blink;
static int state_t;
static u16 frames, ph_x, ph_y;                       // scroll phases: 65536 = one full turn

static const u16 black4[4] = {0, 0, 0, 0};

static int clampi(int v, int lo, int hi) { return v < lo ? lo : v > hi ? hi : v; }
static int sin15(u16 ph) {                            // interpolated sine, +-32512
    u8 i = (u8)(ph >> 8), f = (u8)ph;
    int a = sin_q7[i], b = sin_q7[(u8)(i + 1)];
    return a * 256 + (b - a) * f;
}
static void apply_pal(u8 lvl, u8 blink_on) {          // palette 7 is PRESS START: blinking = swapping it for black
    last_lvl = lvl; last_blink = blink_on;
    bpal_write(title_pal, 0, 28, lvl);
    if (blink_on) bpal_write(title_pal + 28, 28, 4, lvl);
    else bpal_write(black4, 28, 4, 0);
}
static void scroll_pos(void) {                        // lower band drifts inside the 208 x 88 painting: SCX 0..48, SCY 0..24
    g_low_scx = (u8)(24 + (int)(((s32)sin15(ph_x) * 24) >> 15));
    g_low_scy = (u8)(12 + (int)(((s32)sin15(ph_y) * 12) >> 15));
}

void title_setup(void) {
    u8 r;
    music_stop();
    lcd_off();
    vfill(0x9800, 0, 1024); vfill(0x9C00, 0, 1024);
    rVBK = 1; vfill(0x9800, 0, 1024); vfill(0x9C00, 0, 1024); rVBK = 0;
    vcopy(0x8000, title_tiles0, title_tiles0_count * 16);
    for (r = 0; r < 8; r++) vcopy(0x9800 + r * 32, title_band_map + r * 20, 20);
    for (r = 0; r < 11; r++) vcopy(0x9800 + (8 + r) * 32, title_low_map + r * 26, 26);
    for (r = 0; r < 2; r++) vcopy(0x9C00 + r * 32, press_map + r * 20, 20);
    rVBK = 1;
    vcopy(0x8000, title_tiles1, title_tiles1_count * 16);
    for (r = 0; r < 8; r++) vcopy(0x9800 + r * 32, title_band_attr + r * 20, 20);
    for (r = 0; r < 11; r++) vcopy(0x9800 + (8 + r) * 32, title_low_attr + r * 26, 26);
    for (r = 0; r < 2; r++) vcopy(0x9C00 + r * 32, press_attr + r * 20, 20);
    rVBK = 0;
    ph_x = ph_y = 0; frames = 0;
    g_top_scx = g_top_scy = 0; scroll_pos();
    rSCX = 0; rSCY = 0;
    rWX = 7; rWY = 128;                                 // window: PRESS START strip, lines 128-143
    rSTAT |= 0x40; rLYC = 63;                           // LYC interrupt after line 63: painting scroll starts
    apply_pal(16, 1);
    rLCDC = LCDC_ON | LCDC_WIN9C | LCDC_WINON | LCDC_BG8000 | LCDC_BGON;
    music_start();
    state = ST_FADE_IN; state_t = 0;
}

// PLACEHOLDER game logic: for now START simply sends us back to the title screen.
// Later: start the game / show a menu here instead.
static void title_finished(void) { title_setup(); }

void title_frame(void) {
    u8 lvl = 0, blink_on = 1, down, pressed;
    frames++;
    ph_x += 55; ph_y += 84;                             // ~20 s and ~13 s per loop
    scroll_pos();
    down = (joypad() & J_START) ? 1 : 0;
    pressed = (down && !was_down) ? 1 : 0; was_down = down;
    switch (state) {
    case ST_FADE_IN:
        lvl = (u8)clampi(16 - state_t * 16 / 24, 0, 16);
        if (++state_t >= 24) { state = ST_RUN; state_t = 0; }
        break;
    case ST_RUN:
        blink_on = ((frames / 30) & 1) == 0;
        if (pressed) { state = ST_FADE_OUT; state_t = 0; }
        break;
    default:                                            // ST_FADE_OUT
        lvl = (u8)clampi(state_t * 16 / 24, 0, 16); blink_on = (state_t >> 2) & 1;   // fast blink
        if (++state_t >= 24) { title_finished(); return; }
    }
    if (lvl != last_lvl || blink_on != last_blink) apply_pal(lvl, blink_on);
}
