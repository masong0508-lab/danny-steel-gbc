#include <stdio.h>
#include "gbc.h"
#include "title.h"
#include "music.h"
extern void host_snapshot(const char *name); extern void (*host_hook)(int); extern int host_frame; extern u8 host_joy;
static int fr;
int main(void) {
    static const int at[] = {3, 30, 200, 350, 500, 900, 1400, 2200, 2210, 2216, 2224, 2232};
    music_init(); title_setup();
    for (fr = 0; fr < 2300; fr++) {
        host_joy = (fr >= 2200 && fr < 2204) ? J_START : 0;      // press START at frame 2200
        title_frame();
        for (unsigned i = 0; i < sizeof at / sizeof at[0]; i++)
            if (fr == at[i]) { char n[64]; sprintf(n, "snap/title_%04d", fr); host_snapshot(n); }
    }
    printf("title: ok\n"); return 0;
}
