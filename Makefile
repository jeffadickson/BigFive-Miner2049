# Miner 2049er (Atari 400/800/5200), commented disassembly.
#
#   make            assemble src/miner2049er.asm and verify the binary   (needs cc65)
#   make test       verify, then boot the rebuilt cartridge in the 6502 emulator (needs python3, py65)
#   make regen      regenerate src/miner2049er.asm from src/annot/ and your own cartridge
#                   dump at rom/miner.rom (not distributed)
#   make web        rebuild web/out/index.html from book/chapters/
#   make book       rebuild the Word/PDF book in book/docx/ (needs node, docx, LibreOffice)
#
# The rebuilt binary must be byte-identical to the original 16K cartridge:
SHA256 := f74be2d09336ab22259731d3abdc898375f75b16ac304628a818098199f19ff8

ROM_OUT := build/miner2049er.rom
SHA := $(shell command -v sha256sum >/dev/null 2>&1 && echo sha256sum || echo "shasum -a 256")

.PHONY: all verify test regen web book clean

all: verify

$(ROM_OUT): src/miner2049er.asm src/cart.cfg
	@mkdir -p build
	ca65 -o build/miner.o src/miner2049er.asm -l build/miner.lst
	ld65 -C src/cart.cfg -o $@ build/miner.o

verify: $(ROM_OUT)
	@got=$$($(SHA) $(ROM_OUT) | cut -d' ' -f1); \
	if [ "$$got" = "$(SHA256)" ]; then echo "VERIFIED: $(ROM_OUT) matches the original cartridge (SHA-256 $(SHA256))"; \
	else echo "MISMATCH: $(ROM_OUT) has SHA-256 $$got, expected $(SHA256)"; exit 1; fi
	@if [ -f rom/miner.rom ]; then cmp $(ROM_OUT) rom/miner.rom && echo "IDENTICAL to rom/miner.rom, byte for byte"; fi

test: verify
	ROM=$(ROM_OUT) python3 tests/test_emulator.py

regen:
	@[ -f rom/miner.rom ] || { echo "regen needs your own cartridge dump at rom/miner.rom"; exit 1; }
	python3 tools/gen.py src/miner2049er.asm
	$(MAKE) verify

web:
	python3 web/tools/build.py

book:
	sh book/docx/rebuild.sh

clean:
	rm -rf build/*
