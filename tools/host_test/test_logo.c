#include <stdio.h>
#include "gbc.h"
#include "logo.h"
extern void host_snapshot(const char *name); extern void (*host_hook)(int); extern int host_frame;
static const int at[] = {1, 8, 40, 100, 140, 158, 175, 200, 210, 213, 225, 240, 262, 300, 400, 470, 478};
static void hook(int f) {
    for (unsigned i = 0; i < sizeof at / sizeof at[0]; i++)
        if (f == at[i] + 1) { char n[64]; sprintf(n, "snap/logo_%03d", at[i]); host_snapshot(n); }
}
int main(void) { host_hook = hook; logo_play(); printf("logo: %d frames\n", host_frame); return 0; }
