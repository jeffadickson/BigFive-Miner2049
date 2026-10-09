# Miner 2049er — a commented disassembly

A complete, commented reconstruction of Bill Hogue's *Miner 2049er* (Big Five Software,
1982), the 16K cartridge for the Atari 400/800 and 5200. The source reassembles to the
original cartridge byte for byte.

Repository: https://github.com/jeffadickson/BigFive-Miner2049

## Layout

| Path | Contents |
|---|---|
| `src/` | `miner2049er.asm` (ca65 source), `cart.cfg` (linker map), `annot/` (the annotations the source is generated from) |
| `build/` | build output (empty in git) |
| `tools/` | source generator, 6502 tracer, figure and movie makers; `analysis/` one-off studies |
| `emulator/` | the 6502 + Atari harness (py65) that runs the unmodified cartridge code |
| `tests/` | emulator smoke test |
| `web/` | the interactive book: `out/index.html` and the code that builds it |
| `book/` | chapters, the Word book and its generator, figures |
| `rom/` | where your own cartridge dump goes (not distributed) |

## Build and verify

Needs [cc65](https://cc65.github.io/) (`ca65`, `ld65`); the tests need Python 3 and `pip install py65`.

    make          # assemble and check the binary against the original's SHA-256
    make test     # ... then boot it in the emulator
    make regen    # regenerate the source from src/annot/ (needs rom/miner.rom)
    make web      # rebuild web/out/index.html
    make book     # rebuild the Word/PDF book (node, docx, LibreOffice)

## Licence

Code (tools, emulator, tests, web code, Makefile): MIT — see `LICENSE`.
The book and art (text, commentary, figures, rendered pages and movies): all rights
reserved — see `book/LICENSE`. Miner 2049er itself: see `NOTICE`.
