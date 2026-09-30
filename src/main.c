// THE LAST DAYS of danny steel - Game Boy Color port of the title screen (placeholder logic, as on GBA)
//   * DippInn logo (~8 s)
//   * title: painting drifting under the static title band, blinking PRESS START, chiptune bossa nova
//   * START -> fade out -> the title screen restarts (music too). Replace title_finished() later.
#include "gbc.h"
#include "logo.h"
#include "title.h"
#include "music.h"

// Scroll registers are set by two interrupts: VBlank (top zone, from line 0) and LYC (lower zone).
volatile u8 g_top_scx, g_top_scy, g_low_scx, g_low_scy;

static void vbl_isr(void) { rSCX = g_top_scx; rSCY = g_top_scy; }
static void lcd_isr(void) {
    while (rSTAT & 3);                             // wait for HBlank so the change lands between two lines
    rSCX = g_low_scx; rSCY = g_low_scy;
}

void main(void) {
    disable_interrupts();
    add_VBL(vbl_isr);
    add_LCD(lcd_isr);
    set_interrupts(VBL_IFLAG | LCD_IFLAG | TIM_IFLAG);
    enable_interrupts();
    logo_play();                                   // boot logo, then straight into the title screen
    music_init();
    title_setup();
    for (;;) {
        wait_vbl_done();
        title_frame();
    }
}
