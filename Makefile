# Game Boy Color build - requires GBDK-2020 4.x  (https://github.com/gbdk-2020/gbdk-2020/releases)
#   make GBDK_HOME=/path/to/gbdk        (default /opt/gbdk)
TARGET := danny_steel_title
TITLE  := DANNYSTEEL

GBDK_HOME ?= /opt/gbdk
LCC := $(GBDK_HOME)/bin/lcc
SRC := $(wildcard src/*.c)
HDR := $(wildcard src/*.h)

ifeq ($(wildcard $(LCC)),)
$(error lcc not found at $(LCC). Install GBDK-2020 or set GBDK_HOME=/path/to/gbdk)
endif

# -Wm-yC : Game Boy Color only header flag   -Wm-yn : cartridge title   (32 KB ROM, no mapper)
all: $(TARGET).gbc

$(TARGET).gbc: $(SRC) $(HDR)
	$(LCC) -Wm-yC -Wm-yn"$(TITLE)" -o $@ $(SRC)

# regenerate the asset C files from the painting + MIDI (needs Pillow, numpy, opencv-python)
assets:
	python3 tools/make_gbc_title.py
	python3 tools/make_gbc_logo.py
	python3 tools/make_gbc_music.py
	python3 tools/render_preview.py all

clean:
	rm -f $(TARGET).gbc $(TARGET).map $(TARGET).noi *.lst *.rel *.asm *.sym *.ihx *.adb *.cdb *.lk

.PHONY: all assets clean
