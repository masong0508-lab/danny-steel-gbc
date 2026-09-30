// Steps the 1024 Hz music interrupt and logs every register change -> checks order, timing and loop wrap.
#include <stdio.h>
#include <string.h>
#include "gbc.h"
#include "music.h"
extern void tim_tick(void); extern u8 host_reg(u16 a);
int main(void) {
    u8 prev[0x17]; memset(prev, 0, sizeof prev);
    music_init(); music_start();
    unsigned total = 34 * 1024 + 23406 * 2 + 500;          // intro + loop + one more full loop
    int lastcnt = 0;
    for (unsigned t = 0; t < total; t++) {
        tim_tick();
        for (int r = 0; r < 0x17; r++) {
            u8 v = host_reg(0xFF10 + r);
            if (v != prev[r]) { printf("%u %02x %02x\n", t, 0x10 + r, v); prev[r] = v; lastcnt++; }
        }
    }
    fprintf(stderr, "register changes: %d\n", lastcnt);
    return 0;
}
