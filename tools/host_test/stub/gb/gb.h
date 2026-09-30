#pragma once
// Minimal stand-in for GBDK's <gb/gb.h>, only what src/ uses (host testing).
#include <stdint.h>
typedef void (*int_handler)(void);
void add_VBL(int_handler h); void add_LCD(int_handler h); void add_TIM(int_handler h);
void set_interrupts(uint8_t f); void enable_interrupts(void); void disable_interrupts(void);
void wait_vbl_done(void); uint8_t joypad(void);
#define J_START 0x80
#define VBL_IFLAG 0x01
#define LCD_IFLAG 0x02
#define TIM_IFLAG 0x04
void hide_sprite(uint8_t nb); void set_sprite_tile(uint8_t nb, uint8_t t); void set_sprite_prop(uint8_t nb, uint8_t p);
void move_sprite(uint8_t nb, uint8_t x, uint8_t y);
