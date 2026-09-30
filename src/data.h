#pragma once
#include "gbc.h"
// ---- generated assets ----
typedef struct { u16 t; u16 val; u8 ch; u8 arg; } MusEv;      // music event (see music.c)
extern const unsigned int MUSIC_COUNT, MUSIC_LOOP_IDX, MUSIC_LOOP_TICKS;
extern const MusEv music_events[];

// title screen (tools/make_gbc_title.py)
extern const u16 title_pal[32];
extern const unsigned int title_tiles0_count, title_tiles1_count;
extern const u8 title_tiles0[], title_tiles1[];
extern const u8 title_band_map[], title_band_attr[];          // 20 x 8
extern const u8 title_low_map[], title_low_attr[];            // 26 x 11
extern const u8 press_map[], press_attr[];                    // 20 x 2 (window)

// logo (tools/make_gbc_logo.py)
extern const unsigned int sc_tile_count, tx_tile_count;
extern const u8 sc_tiles[], sc_map[], sc_attr[];              // map: 32 x 18
extern const u16 sc_pal[12];
extern const u8 spr_tiles[];
extern const u16 spr_pal[8];
extern const u8 gr_tiles[];
extern const u16 gr_pal[4];
extern const u8 tx_tiles[], tx_map[], rope_map[];             // tx_map 20 x 3, rope_map 4 frames x 16
extern const u16 tx_pal[8];
extern const signed char sin_q7[256];
