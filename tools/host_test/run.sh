#!/bin/sh
# Compiles the real src/ files with gcc against a fake hardware layer, runs logo/title/music, renders snapshots.
# Needs: gcc, python3 + Pillow + numpy.   Run from the repo root: sh tools/host_test/run.sh
set -e
mkdir -p snap
CF="-DHOST_TEST -Wall -Wextra -Wno-unused-parameter -Isrc -Itools/host_test/stub"
SRCS="tools/host_test/host.c src/logo.c src/title.c src/music.c src/logo_data.c src/title_data.c src/music_data.c"
for t in logo title music; do gcc $CF -o /tmp/test_$t tools/host_test/test_$t.c $SRCS; done
/tmp/test_logo; /tmp/test_title; /tmp/test_music > snap/music.log
python3 tools/host_test/ppu.py snap/logo.png snap/logo_040.bin snap/logo_100.bin snap/logo_158.bin snap/logo_225.bin snap/logo_300.bin
python3 tools/host_test/ppu.py snap/title.png snap/title_0003.bin snap/title_0350.bin snap/title_0900.bin
echo "wrote snap/logo.png snap/title.png"
