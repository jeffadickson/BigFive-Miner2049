# Introduction {#intro}

Miner 2049er came out for the Atari 400 and 800 at the end of 1982 on a 16-kilobyte cartridge, twice the size of a standard Atari cartridge of the time. Bill Hogue of Big Five Software wrote it alone, entirely in 6502 machine language. This book reconstructs that cartridge by disassembling the ROM.

The game itself is simple to describe. Bounty Bob, a Canadian Mountie, must walk over every section of every girder in an abandoned uranium mine while radioactive mutants patrol the levels. Picking up the prospecting tools left behind turns the mutants green, and for a short time he can eat them. There are ten "stations", each with its own gadget: slides, transporters, moving platforms, a lift, pulverizers and finally a cannon fired with TNT.

!fig hero|The attract-mode demo, every second frame, rendered by this book's 6502 harness running the unmodified cartridge code. Bob is driven by the input recording stored in the ROM (see "The demo recorder").

What makes the program remarkable is how much it fits into 16K and how hard it pushes the hardware:

- **One ROM, two machines.** The same 16K image boots on the Atari 400/800 and on the Atari 5200. At power-up it builds a table of pointers to the graphics and sound chips, which sit at different addresses on the two machines, and every later access goes through the table.
- **Ten colours on a scan line.** The high-score screen runs a cycle-counted loop from RAM that rewrites all four playfield colour registers twice per scan line. It patches its own delay opcode to match the cycles the display chip takes, which change with the fine-scroll value.
- **Eight mutants, two sprites.** Display-list interrupts cut the screen into four bands and reuse player 3 and the four missiles in each band. The collision registers are read band by band, so the game knows which mutant touched Bob.
- **The screen as the database.** Which girder sections Bob has claimed is recorded nowhere except in the bitmap itself.
- **A game that runs in the interrupt.** Almost all of the game runs in the vertical-blank interrupt. The main program only waits.

None of the original source survives. Every name, comment and explanation here was worked out from the machine code. Where the evidence is indirect, the text says so.

## What is in this package {#package}

- **This book.** History and background, the target hardware, the program's architecture, its algorithms with interactive figures, and the complete listing in an appendix.
- **miner2049er.asm**, the commented source: about 9,250 lines for the ca65 assembler (part of the free cc65 suite). It assembles to an image that is byte-for-byte identical to the original cartridge. Every routine has a name and a header describing what it does, and every subroutine call is commented with what the called routine does.
- **cart.cfg**, the linker configuration needed to rebuild the ROM.

## How the work was checked {#checks}

- **Reassembly.** The commented source is reassembled after every change and compared with the original ROM, which proves that no byte was misread.
- **Emulation.** The cartridge was run in the Atari800 emulator (version 5.0, with its built-in AltirraOS firmware instead of Atari's ROMs), both as a 400/800 cartridge and as a 5200 cartridge. The emulator's monitor was used to stop at chosen instructions, read the beam position and step through code.
- **A 6502 harness.** A small Python harness built on the py65 CPU emulator runs the ROM so that memory can be inspected, stations built on demand and single routines called.
- **Ported routines checked against the ROM.** The claiming routine used in the interactive figure was compared with the ROM's own code at 1,322 random girder positions on all ten stations, with identical results.
- **Independent review.** The text and the source comments were checked against the code by a separate reviewer, and the errors found were corrected.

Every picture of the game in this book comes from one of three places: frames captured from the Atari800 emulator; movies rendered by the harness, which runs the cartridge's own code and draws each scan line from the display list, the player/missile memory and the GTIA registers, with the collision registers modelled so that the game's collision code works; or drawings made by this page directly from the cartridge bytes, which are embedded in it. Harness frames were compared with emulator frames of the same scenes. The letter shapes come from AltirraOS, so they differ slightly from a real Atari's.

# From a TRS-80 shop {#trs80}

## Radio Shack, Reseda {#reseda}

Big Five Software began behind a Radio Shack counter. Bill Hogue first used a TRS-80 in high school, then worked at the Radio Shack store in Reseda, California, where he wrote BASIC programs between customers and moved on to assembly language. Jeff Konyu came into the store to buy parts; both were devoted Asteroids players. Hogue started a computer science degree at Cal State Northridge in 1979 and left in his second semester "when Big Five started up". The name came from a junior-high television class in which Hogue and four friends had called themselves "The Big Five".

The company sold games by mail order from his parents' house in Van Nuys. Its first advertisement, for Super Nova, ran in 80 Microcomputing in July 1980. Over the next two years Big Five sold a run of arcade-style games for the TRS-80 Model I and III, among them Super Nova, Attack Force, Galaxy Invasion, Meteor Mission II, Cosmic Fighter, Robot Attack and Defense Command, plus Stellar Escort and Weerd by other programmers. It also sold the TRISSTICK, an adapter that let TRS-80 owners use Atari joysticks.

The mail-order address in Super Nova's title screen in 1980, P.O. Box 9078-185, Van Nuys, is the same one printed in Miner 2049er's credits two years later.

## Super Nova and the Model I {#supernova}

The TRS-80 Model I was a hard machine to write arcade games for. It had a Z80 processor at 1.77 MHz, a 64 x 16 character screen whose only graphics were 2 x 3 blocks inside each character cell (128 x 48 "pixels"), one colour, no sprites and no sound chip: the only route to a speaker was the cassette port.

A disassembly of Super Nova (version 1.1, 1980), made before this one, shows how Hogue worked within that:

- **An off-screen frame buffer.** Every frame is composed in RAM and then copied to the screen, to avoid flicker.
- **Pre-shifted sprite tables** for the block-graphics cells.
- **Collisions by pixel overlap,** tested in software.
- **Timing by instruction counting.** The program uses no interrupts at all.
- **Self-modifying code everywhere.** The PLOT routine, for example, stores `SET 3,(HL)` as a placeholder and patches the bit number into the opcode before running it. Six distinct patterns of self-modification appear in the program.
- **No sound.** There is not one OUT instruction in Super Nova. Reviewers at the time noticed.

The tools were Radio Shack's own: "Nothing fancy — I just used the standard Radio Shack editors and assemblers for Z-80 code."

## Moving to the Atari {#move}

By 1982 the Model I had been out of production for a year and the TRS-80 games market was shrinking. Hogue wanted colour and sound. He considered the Color Computer and the Apple II and decided that "for the games I wanted to program, the Atari 400/800 was the best choice." The Atari gave him "color to play with" for the first time, though he had to learn a new processor and thought that "in many ways the Z-80 was the better CPU". He missed its block-copy instruction, LDIR.

He did not develop on the Atari itself. In an interview with trs-80.org he said: "I wrote a cross-assembler running on a TRS-80 Model 16." Source was edited and assembled on Tandy's business machine, and the object code was sent to an Atari for testing over a serial port. So Miner 2049er was, quite literally, built in a TRS-80 shop.

The game shipped in late 1982, the same month as Big Five's last TRS-80 release. In September 1983 Hogue told 80 Micro that the company had "officially left" the TRS-80 market, and that "if we hadn't come out with our Atari game at the time we did, we probably would have gone out of business." A black-and-white TRS-80 version of Miner, programmed by Kelly Bakst, was written but never released.

:::op LDIR
name: Z80 block copy (what Hogue missed)
enc: ED B0
cycles: 21 T-states per byte (16 for the last)
flags: P/V cleared
body: Copies BC bytes from (HL) to (DE), incrementing both pointers, in one instruction. The 6502 has nothing like it. The usual replacement is a four-instruction loop: `LDA src,X / STA dst,X / DEX / BNE loop`, 4 + 5 + 2 + 3 = 14 cycles per byte and at most 256 bytes per loop. At the Atari's 1.79 MHz that is about 7.8 µs a byte, against 11.9 µs for LDIR on a 1.77 MHz Model I, so the 6502 version is faster. It costs more code, and it needs a second loop or a pointer in zero page for anything longer than 256 bytes. Miner's COPY and CLEAR routines are exactly this kind of loop (see CLEAR_MEM, which counts a negative length up to zero).
:::

## What carried over {#carried}

Comparing the two disassemblies shows a programmer who brought his habits with him and threw away what the new hardware made unnecessary.

|Super Nova (Z80, TRS-80, 1980)|Miner 2049er (6502, Atari, 1982)|
|Off-screen frame buffer, copied every frame|Draws straight into the displayed bitmap; moving objects are hardware sprites|
|Collisions found by testing pixel overlap|GTIA's collision registers for mutants; the bitmap is read for floors and walls|
|No interrupts; timing by counting instructions|The whole game runs in the vertical-blank interrupt; cycle counting survives only in the title-screen kernel|
|Self-modifying code for speed (patched bit numbers, swapped operations)|Self-modifying code for timing and portability (patched delay opcodes, colour operands and chip addresses)|
|Silent|All four POKEY voices, a tune with calculated harmony|
|High-score name entry stubbed out|Full name entry on both machines|

The self-modifying code is the clearest thread. In Super Nova it saves cycles in the inner drawing loops. In Miner it shows up in the one place where every cycle matters, the scan-line loop that colours the title screen's lights.

# The target hardware {#hardware}

## The Atari 400 {#a400}

Atari announced its home computers in December 1978, showed the Atari 400 and 800 at the Winter Consumer Electronics Show in January 1979, and shipped them in November 1979. The 400 started life as "Candy", a low-cost design. Early in 1979 it became a full computer aimed at children and families, which is why it has a flat, spill-proof membrane keyboard instead of the 800's full-travel keys. Joe Decuir, one of its designers, later said the keyboard "didn't feel great, but it worked." Sources give its launch price as $495, $549.95 or $550.

Strict FCC limits on radio interference shaped the design. Both machines are wrapped in cast-aluminium shielding, and rather than expansion slots they talk to their peripherals over a single serial bus (SIO). The 400 has one cartridge slot under a lid on top; the 800 has two. Cartridges, keyed connectors and a sealed case made the machine friendly to people who had never owned a computer.

The 400 was planned with 4K of RAM (hence the name), shipped with 8K, and by 1981-82 was sold with 16K. Miner 2049er needs 16K of RAM. Prices fell steeply: about $400 with BASIC and a cassette recorder in 1981, $349 in 1982, and under $200 after rebates by the end of 1982. The 400 outsold the 800 by roughly two to one. About two million Atari 8-bit computers were sold between 1979 and 1985. Their main rivals were the Apple II, the TRS-80 and, from August 1982, the Commodore 64.

!fig blockdiagram|The Atari 400 as Miner 2049er sees it. The 6502 shares the bus with ANTIC, which takes memory cycles away from it to fetch the display. GTIA and POKEY are reached through the game's pointer table; ANTIC directly.

The 400 and 800 share their electronics. Next to a MOS 6502 processor sit three custom chips designed under Jay Miner (who later designed the Amiga's chips): ANTIC, which fetches the display; CTIA or GTIA, which turns it into colour and adds sprites; and POKEY, which makes sound and reads the keyboard. A 6520 PIA reads the joysticks. The operating system lives in a 10K ROM at the top of memory.

## The 6502 {#cpu}

The 6502 is a small processor even by 1982 standards. It has one accumulator (A), two index registers (X and Y), all 8 bits wide, an 8-bit stack pointer whose stack is fixed at $0100-$01FF, a status register and a 16-bit program counter. There are no 16-bit registers and no multiply.

What it has instead is **zero page**: the first 256 bytes of memory can be addressed with a one-byte address, which saves a byte and a cycle, and pairs of zero-page bytes can act as 16-bit pointers. A 6502 program treats zero page as its register file, and Miner uses all of it: $10-$6F hold the hardware pointer table and $70-$FF the game's variables.

|Mode|Example|Bytes|Cycles (LDA / STA)|Meaning|
|immediate|`LDA #$84`|2|2 / -|the value $84|
|zero page|`LDA $90`|2|3 / 3|byte at $0090|
|zero page,X|`LDA $90,X`|2|4 / 4|byte at $0090 + X, wrapping in page 0|
|absolute|`LDA $D016`|3|4 / 4|byte at $D016|
|absolute,X or ,Y|`LDA $0300,Y`|3|4+ / 5|byte at $0300 + Y (+1 cycle if a page is crossed on a read)|
|(indirect),Y|`LDA ($28),Y`|2|5+ / 6|take the pointer at $28/$29, add Y|
|(indirect,X)|`LDA ($28,X)`|2|6 / 6|take the pointer at $28 + X, then use it|

The two indirect modes are the ones Miner leans on hardest, because its whole access to the graphics and sound chips goes through pointers.

:::op STA (zp),Y
name: store indirect, indexed by Y
enc: 91 zz
cycles: 6
flags: none
body: Reads a 16-bit address from zero page at zz and zz+1, adds Y, and stores A there. With Y = 0 it is simply "store A through the pointer at zz". Miner writes nearly every GTIA and POKEY register this way, for example `STA (pCOLPF1),Y`. Compared with `STA $D017` it is one byte shorter and two cycles slower, and Y must be 0, which is why so many routines begin with `LDY #$00`.
:::

## Time on a television {#time}

An Atari draws an NTSC picture of 262 scan lines, 60 times a second. Everything in the machine is locked to that picture:

- one **scan line** lasts 114 processor cycles of 1.79 MHz (63.7 µs);
- one processor cycle is 2 **colour clocks**, the width of the narrowest coloured dot the hardware draws; a line is 228 colour clocks, of which a normal-width playfield shows 160;
- one **frame** is 262 x 114 = 29,868 cycles.

The processor does not get all of those cycles. ANTIC reads the screen from the same RAM over the same bus, and when it needs the bus it simply stops the 6502 for a cycle. This is called cycle stealing, and how much it steals depends on what is on the screen.

!fig linebudget|Where the 114 cycles of a scan line go on four kinds of line in Miner 2049er. ANTIC's fetches always win; the 6502 gets what is left. The numbers for the title row were measured in the emulator (see "The title-screen kernel"); the others follow ANTIC's fetch rules.

Two consequences shape the program. A routine that must do something at a particular point on a line cannot know how long its instructions will take without knowing ANTIC's fetches on that line. And there is a lot more CPU time in the vertical blank, where ANTIC fetches almost nothing, than in the middle of the screen.

## ANTIC {#antic}

ANTIC (designed by Joe Decuir, Francois Michel and Steve Smith) is a processor in its own right. It follows a **display list**, a small program in RAM in which each instruction describes one horizontal band of the screen: its graphics mode, where its data comes from, whether it scrolls, and whether it should interrupt the 6502 when it is drawn. Once started it runs with no help from the CPU.

|Display list byte|Meaning|
|$70|8 blank lines|
|$42 lo hi|mode 2 text (40 columns), Load Memory Scan: take the data from address hi lo|
|$0E|one line of mode E bitmap: 160 pixels, 4 colours|
|$8E|the same with bit 7 set: interrupt the CPU at the end of this line (a DLI)|
|$41 lo hi|Jump and wait for Vertical Blank: start again at hi lo next frame|

Two kinds of interrupt come from ANTIC, both as NMIs (interrupts the CPU cannot mask):

- **The display-list interrupt (DLI)** fires at the end of any display-list line with bit 7 set. Its handler can change colours or sprite positions for the lines below, which is how one set of hardware registers can serve several parts of the screen.
- **The vertical-blank interrupt (VBI)** fires at scan line 248, after the last visible line. It is the natural place to run a game's frame.

ANTIC also has registers the program uses directly: **WSYNC** ($D40A), which halts the CPU until the end of the current scan line when written; **VCOUNT** ($D40B), the current line divided by two; **HSCROL** ($D404), which shifts a line sideways by 0-15 colour clocks; DMACTL, PMBASE, CHBASE, CHACTL and the display-list pointer.

:::op STA WSYNC
name: store to ANTIC's WSYNC register
enc: 8D 0A D4
cycles: 4, then the CPU stops until the end of the line
flags: none
body: The value written does not matter. The write makes ANTIC hold the 6502's RDY line low until the beam reaches the end of the current scan line, so the next instruction starts at a known horizontal position. It is the only way a 6502 program can line itself up with the beam. Miner's title kernel uses one WSYNC and then counts cycles for the next 12 lines without another.
:::

## GTIA {#gtia}

GTIA (George McLeod; machines built before late 1981 have the earlier CTIA) turns ANTIC's data into colour. A colour is one byte: the high four bits choose one of 16 hues and bits 1-3 one of 8 luminances, so $84 is hue 8 (blue) at luminance 4. Hue 0 is grey.

GTIA also provides **player/missile graphics**, Atari's name for sprites: four 8-pixel players and four 2-pixel missiles, each a vertical strip the full height of the screen, with its own colour and horizontal position. Their shapes come from a block of RAM that ANTIC fetches line by line (PMBASE says where); to move a player up or down, the program moves its bytes within that strip. To move it sideways, it writes a new horizontal position. PRIOR sets which of players and playfield is in front and switches on two special modes Miner uses: *multicolour players* and the *fifth player*.

GTIA keeps **collision registers**: one bit for every pair of sprite and playfield colour, or sprite and sprite, that has overlapped since the last write to HITCLR. Here is a detail Miner depends on. GTIA's read registers and write registers share addresses:

|Address|Write|Read|
|$D000-$D003|HPOSP0-3 (player positions)|M0PF-M3PF (missile-playfield collisions)|
|$D004-$D007|HPOSM0-3 (missile positions)|P0PF-P3PF (player-playfield collisions)|
|$D008-$D00B|SIZEP0-3 (player widths)|M0PL-M3PL (missile-player collisions)|
|$D00C-$D00F|SIZEM, GRAFP0-2|P0PL-P3PL (player-player collisions)|
|$D010|GRAFP3|TRIG0 (fire button)|
|$D01F|CONSOL (speaker)|CONSOL (START, SELECT, OPTION keys)|

So when READ_HITS does `LDA (pSIZEP0),Y`, it reads M0PL through the pointer it otherwise uses to set player 0's width. The listing names each pointer after its write register and says in the comment which read register is meant.

## POKEY and the PIA {#pokey}

POKEY (Doug Neubauer) has four sound voices, each a frequency divider (AUDFn) and a control byte (AUDCn) with a 4-bit volume and a choice of pure tone or noise. It also scans the keyboard, reads eight paddle potentiometers, handles serial I/O and has a free-running 17-bit noise generator whose low byte can be read as RANDOM. Miner reads RANDOM through a pointer it calls pSKRES, because the write register at that address is SKRES.

The 6520 PIA's port A ($D300) gives the two joystick directions as four bits each, 0 meaning pushed.

## Memory with Miner plugged in {#memory}

|Address|400/800|Used by Miner as|
|$0000-$00FF|zero page|pointer table ($10-$6F), variables ($70-$FF)|
|$0100-$01FF|6502 stack|stack|
|$0200-$02FF|OS vectors|interrupt vectors|
|$0300-$3FFF|RAM (16K machine)|sprites, tables, display list, the mine's bitmap|
|$8000-$BFFF|cartridge|Miner 2049er|
|$D000-$D0FF|GTIA|through the pointer table|
|$D200-$D2FF|POKEY|through the pointer table|
|$D300-$D3FF|PIA|joysticks|
|$D400-$D4FF|ANTIC|directly|
|$D800-$FFFF|OS ROM (font at $E000)|the font only|

## The Atari 5200 {#a5200}

In 1982 Atari repackaged the same chipset as a games console, the 5200 SuperSystem. It shipped in October 1982 at $299.95 and sold just over a million units before it was discontinued in May 1984. David Ahl called it "a 400 computer in disguise". The differences matter to this program:

|Item|Atari 400/800|Atari 5200|
|ANTIC|$D400|$D400|
|GTIA|$D000|$C000|
|POKEY|$D200|$E800|
|PIA (joysticks)|$D300|none|
|Joysticks|digital switches|analog pots (POKEY), non-centring|
|Keys|keyboard + START/SELECT/OPTION|12-key keypad + START/PAUSE/RESET|
|Firmware|10K OS, font at $E000|2K BIOS, font at $F800|
|Cartridge start|vector at $BFFA, init at $BFFE|vector at $BFFE|

Miner 2049er was the first game from an independent publisher for the 5200, in July 1983. As the next chapters show, the 5200 support is already in the 400/800 cartridge.

## Why the hardware mattered {#mattered}

Each part of the game maps onto a hardware feature:

- **The mine** is a bitmap in ANTIC mode E: 160 pixels across, four colours, two bits per pixel, 40 bytes per line.
- **Bounty Bob** is three players laid over each other, which gives him four colours.
- **The mutants** are player 3 and the missiles, reused down the screen by display-list interrupts.
- **The cannon** is drawn with player 3 and the missiles, and **the lift** with player 3.
- **Collisions with mutants** come from GTIA's collision registers; collisions with floors and walls come from reading the bitmap.
- **The sound effects** use all four POKEY voices.

# Miner 2049er and Big Five {#game}

Miner 2049er was Big Five's first Atari game, released at the end of 1982 (sources say November or December). Hogue built the game play first and added the mining theme and story afterwards. He combined Donkey Kong-style climbing with the Pac-Man ideas of covering the whole maze and of enemies that become vulnerable. The title is a pun on the "forty-niners" of the 1849 California Gold Rush, moved a century into the future. The folk song "Oh My Darling, Clementine" has the line "dwelt a miner, forty-niner", and the cartridge plays that tune after a game ends. Curtis Mikolyski designed levels for the series; Hogue coded them.

The game was a hit. Creative Computing's reviewer called it "a greater game" than Donkey Kong in February 1983, and Tom Hudson of ANALOG wrote that it "looks as if it were designed, not just thrown together". It won Electronic Game of the Year at the 1984 Arkie Awards. Hogue said later that "Atari paid me a boatload of money for Miner." Licensing was handled by Barry Friedman's International Computer Group. Ports followed for about twenty systems, including the 5200, ColecoVision, Apple II, IBM PC, Commodore 64, VIC-20, TI-99/4A and a two-cartridge Atari 2600 version by Tigervision. It also inspired Matthew Smith's Manic Miner. Hogue's sequel, Bounty Bob Strikes Back!, followed in 1985 on a bank-switched cartridge, after which Big Five wound down.

## The ten stations {#stations}

!fig stations|The ten stations, captured from the emulator after jumping to each with the cheat code. Colours are picked at random each time a station starts.

|Station|Name|What is special|Sections|Bonus (zone 1)|
|1|The Mine Shaft|ladders and sloping girders|175|3000|
|2|The Slides|chutes that carry Bob down|144|3500|
|3|The Transporters|four numbered booths; press 1-4|124|4000|
|4|The Lillipads|many small floating girders|154|4500|
|5|Advanced Lillipads|slides, moving platforms, a poisoned goblet|131|5000|
|6|Radioactive Waste|a deadly glowing tank|83|5500|
|7|Advanced Transporters|transporters and long slides|90|6000|
|8|The Lift|a scissor lift Bob drives himself|114|4500|
|9|The Pulverizers|pistons, platforms that wait for Bob|78|6500|
|10|The Cannon|load TNT, fire yourself upwards|134|7000|

The station names are from Creative Computing's 1983 guide. The section counts and bonuses come from the station data in the ROM. A "zone" is one pass through all ten stations; each new zone adds 500 to every starting bonus and speeds up the mutants.
