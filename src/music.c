#include "music.h"
#include "data.h"

// Time base: the timer fires at 1024 Hz (TAC = 4096 Hz clock, TMA = 252 -> 4 ticks per overflow), and the whole
// event list is stepped from that interrupt, so the song stays on time whatever the main loop is doing.
static volatile u16 now;
static volatile u8 playing;
static u16 idx;

static const u8 bass_wave[16] = {0x01,0x23,0x45,0x67,0x89,0xab,0xcd,0xef, 0xfe,0xdc,0xba,0x98,0x76,0x54,0x32,0x10};

static void silence(void) {
    rNR12 = 0; rNR22 = 0; rNR32 = 0; rNR42 = 0;   // volume 0 / DAC off = silent
}
void music_stop(void) { playing = 0; silence(); }

static void play(const MusEv *e) {
    u8 v = (u8)e->val, hi = (u8)(e->val >> 8), a = e->arg;
    switch (e->ch) {
    case 0:                                        // lead: pulse 1, 25% duty, slow fade
        if (a) { rNR12 = (u8)((a << 4) | 6); rNR13 = v; rNR14 = 0x80 | hi; }
        else rNR12 = 0;
        break;
    case 1:                                        // comp: pulse 2, 12.5% duty, held
        if (a) { rNR22 = (u8)(a << 4); rNR23 = v; rNR24 = 0x80 | hi; }
        else rNR22 = 0;
        break;
    case 2:                                        // bass: wave channel at 50% volume
        if (a) { rNR32 = 0x40; rNR33 = v; rNR34 = 0x80 | hi; }
        else rNR32 = 0;
        break;
    default:                                       // percussion: noise, quick decay. kind 1 = hat, 2 = side-stick
        rNR42 = (u8)(((a & 15) << 4) | 1);
        rNR43 = ((a >> 4) == 1) ? 0x21 : 0x5B;
        rNR44 = 0x80;
    }
}

static void music_isr(void) {
    const MusEv *e;
    if (!playing) return;
    now++;
    for (;;) {
        if (idx >= MUSIC_COUNT) { idx = MUSIC_LOOP_IDX; now -= MUSIC_LOOP_TICKS; }   // back to the loop start
        e = &music_events[idx];
        if (now < e->t) break;
        play(e); idx++;
    }
}

void music_init(void) {
    u8 i;
    rNR52 = 0x80;                                  // sound on
    rNR50 = 0x77; rNR51 = 0xFF;                    // both sides, full volume, all 4 channels
    rNR10 = 0x00;                                  // no sweep
    rNR11 = 0x40; rNR21 = 0x00;                    // duty 25% / 12.5%
    rNR30 = 0x00;                                  // wave DAC off while wave RAM is written
    for (i = 0; i < 16; i++) WAVE_RAM[i] = bass_wave[i];
    rNR30 = 0x80;
    silence();
    playing = 0;
    rTAC = 0; rTMA = 252; rTIMA = 252; rTAC = 0x04;   // 4096 Hz, reload 252 -> 1024 Hz interrupt
    add_TIM(music_isr);
}
void music_start(void) {
    playing = 0; silence();
    now = 0; idx = 0;
    playing = 1;
}
