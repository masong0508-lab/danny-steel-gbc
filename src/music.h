#pragma once
// Plays the song on the Game Boy's 4 sound channels (2 pulse, 1 wave, 1 noise) from a 1024 Hz timer interrupt.
void music_init(void);    // once, at boot
void music_start(void);   // restart from the 4-bar intro
void music_stop(void);
