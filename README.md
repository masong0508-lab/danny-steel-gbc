# THE LAST DAYS of danny steel - Game Boy Color title screen

GBC-only port of the GBA title project (DippInn logo -> title screen with drifting painting, blinking PRESS START, chiptune bossa nova).
Built with [GBDK-2020](https://github.com/gbdk-2020/gbdk-2020) 4.5.0 into a 32 KB ROM, no mapper. `make GBDK_HOME=/path/to/gbdk`
or push to GitHub: the workflow builds `danny_steel_title.gbc` and uploads it as an artifact (and to a release on `v*` tags).

## Layout
| file | role |
|---|---|
| `src/main.c` | boot, VBlank + LYC interrupts (scroll split), main loop |
| `src/logo.c` | DippInn logo, 3 phases (scene / grey scan line / text + rope) |
| `src/title.c` | title screen, START -> fade -> restart (`title_finished()` is the placeholder to replace) |
| `src/music.c` | sound engine, stepped from a 1024 Hz timer interrupt |
| `src/gfx.c`, `gbc.h` | register definitions, VRAM/palette helpers |
| `src/*_data.c` | **generated** by `tools/make_gbc_*.py` (`make assets`) |
| `tools/host_test/` | runs the real C sources on a PC against a fake GBC and renders frames |

## What changed from the GBA version
* **Screen 160x144, 4-colour tiles, 8 BG palettes.** The painting is re-quantised per tile (`fit_palettes` + ordered dither).
  Tiles are split over both VRAM banks (bank bit in the map attribute).
* **Title band is static.** GBC has one opaque BG layer, so the title text is baked into the top 64 lines
  (text tiles use a flat backdrop colour + outline/cream/tan). The painting drifts in lines 64-127; a LYC interrupt swaps SCX/SCY
  there. Both sides of the seam are vignetted so it is not obvious. PRESS START is the window (lines 128-143); it blinks by swapping its palette for black.
* **Logo**: GBA per-scanline HBlank-DMA effects became a two-speed scroll split (ridge / hills). Sky is flat tile rows,
  clouds and moon are 8x16 sprites (near lilac clouds dropped: sprite budget). The rope underline grows in 8 px steps instead of pixel-smooth.
* **Music**: same arrangement and event table as the GBA build; GBA sound registers translated to NR1x-NR4x. Timing is now
  a 1024 Hz interrupt with u16 tick times (`tools/make_gbc_music.py`), 6 bytes per event.

## Status
Compiled and executed only on a PC with a hardware stub (`sh tools/host_test/run.sh`): frame renders, fades, blink,
restart-on-START and an exact music-loop repeat check pass. **Not yet built with real GBDK or run on an emulator/hardware** -
check the first CI build, and test in an accurate emulator (SameBoy, BGB, mGBA).
