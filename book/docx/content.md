# Introduction

Source, corrections and issues: https://github.com/jeffadickson/BigFive-Miner2049


Miner 2049er came out for the Atari 400 and 800 at the end of 1982 on a 16-kilobyte cartridge, twice the size of a standard Atari cartridge of the time. It was written by one programmer, Bill Hogue of Big Five Software, entirely in 6502 machine language. This document is a guided tour of that cartridge, reconstructed by disassembling the ROM.

The game itself is simple to describe. Bounty Bob, a Canadian Mountie, must walk over every section of every girder in an abandoned uranium mine while radioactive mutants patrol the levels. Picking up the prospecting tools left behind turns the mutants green, and for a short time he can eat them. There are ten "stations", each with its own gadget: slides, transporters, moving "lillipads", a lift, pulverizers and finally a cannon fired with TNT.

What makes the program remarkable is how much it fits into 16K, and how hard it pushes the hardware. Among the things described in the chapters that follow:

- **One ROM, two machines.** The same 16K image boots on the Atari 400/800 and on the Atari 5200 SuperSystem. At power-up it checks whether the 5200's character set is at $F800, then builds a table of pointers to the graphics and sound chips, which sit at different addresses on the two machines. Every later access to those chips goes through the table. I confirmed this by booting the unmodified file as a 5200 cartridge in an emulator.
- **Ten colours on a scan line.** The high-score screen's "chasing lights" use a cycle-counted routine that runs from RAM. It rewrites all four playfield colour registers twice on every scan line and patches its own opcodes to stay in step with the fine scroll.
- **Eight mutants, two sprites.** Display-list interrupts cut the screen into four bands and reuse player 3 and the four missiles in each band. The hardware collision registers are read band by band, so the game knows which mutant touched Bob.
- **A game that runs in the interrupt.** Almost all of the game, from Bob's movement to the mutants and the timer, runs in the vertical-blank interrupt. The main program only waits.
- **Data packed into data.** Tables overlap their neighbours wherever their bytes happen to agree. A display list's jump address doubles as two characters of text, the phone number printed in the credits is also the cheat code, and the lift's wheels are also a bonus value.

None of the original source survives. Every name, comment and explanation here was worked out from the machine code. Where the evidence is indirect, the text says so.

## What is in this package

- **Miner 2049er Commented** (this document). It covers the Atari 400 and its background, the program's architecture, its algorithms and its graphics, and ends with the complete listing in an appendix.
- **miner2049er.asm**, the commented source: about 9,200 lines for the ca65 assembler (part of the free cc65 suite). It assembles to an image that is byte-for-byte identical to the original cartridge. Every routine has a name and a header describing what it does, and every subroutine call is commented with what the called routine does.
- **cart.cfg**, the linker configuration needed to rebuild the ROM.

## How the work was checked

Three kinds of checking were used. First, the commented source is reassembled after every change and compared with the original ROM, which proves that no byte was misread. Second, the cartridge was run in the Atari800 emulator, both as a 400/800 cartridge and as a 5200 cartridge. Third, a small 6502 harness written for this project runs the ROM so that memory can be inspected, stations can be built on demand and claims can be tested. For example, Bob jumping at the start of station 5 touches the goblet and is killed; that was confirmed this way. The station screenshots were taken in Atari800 using the game's own cheat code. Atari's original ROMs were not used: the screenshots show the emulator's built-in replacement firmware (AltirraOS), so the letter shapes differ slightly from a real Atari's.

# The Atari 400

## Origins

Atari announced its home computers in December 1978, showed the Atari 400 and 800 at the Winter Consumer Electronics Show in January 1979, and shipped them in November 1979. The 400 started life as "Candy", a low-cost design. Early in 1979 it became a full computer aimed at children and families, which is why it has a flat, spill-proof membrane keyboard instead of the 800's full-travel keys. Joe Decuir, one of its designers, later said the keyboard "didn't feel great, but it worked." Sources give its launch price as $495, $549.95 or $550.

Strict FCC limits on radio interference shaped the design. Both machines are wrapped in cast-aluminium shielding, and rather than expansion slots they talk to their peripherals over a single serial bus (SIO). The 400 has one cartridge slot under a lid on top; the 800 has two. Cartridges, keyed connectors and a sealed case made the machine friendly to people who had never owned a computer.

The 400 was planned with 4K of RAM (hence the name), shipped with 8K, and by 1981-82 was sold with 16K. Miner 2049er needs 16K of RAM. Prices fell steeply: about $400 with BASIC and a cassette recorder in 1981, $349 in 1982, and under $200 after rebates by the end of 1982. The 400 outsold the 800 by roughly two to one. About two million Atari 8-bit computers were sold between 1979 and 1985. Their main rivals were the Apple II, the TRS-80 and, from August 1982, the Commodore 64.

## Inside the machine

The 400 and 800 share their electronics. The processor is a MOS 6502 running at 1.79 MHz (1.77 MHz on PAL machines). What made the Ataris different from their rivals was a set of three custom chips, designed under Jay Miner, who later designed the Amiga's chips:

- **ANTIC** (Joe Decuir, Francois Michel and Steve Smith) is a processor in its own right. It fetches screen data from RAM by DMA and follows a *display list*, a little program in which each instruction describes one horizontal band of the screen: its graphics mode, where its data comes from, whether it scrolls, and whether it should interrupt the 6502 when it is drawn (a *display list interrupt*, or DLI). Once started it runs with no help from the CPU, stealing memory cycles from it as it goes.
- **CTIA/GTIA** (George McLeod) turns ANTIC's data into colour. It also provides *player/missile graphics*, Atari's name for sprites: four 8-pixel-wide "players" and four 2-pixel "missiles", each a vertical strip the full height of the screen with its own colour and horizontal position. GTIA records which players, missiles and playfield colours touched each other in *collision registers*. Machines built from late 1981 have GTIA; earlier ones have CTIA.
- **POKEY** (Doug Neubauer) provides four sound voices, the keyboard scanner, eight paddle (potentiometer) inputs, a 17-bit random-number generator, timers and serial I/O.

A fourth chip, a 6520 PIA, reads the joysticks. The operating system lives in a 10K ROM at the top of memory.

## The Atari 5200

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

## Why the hardware mattered to Miner 2049er

The design of the game follows the hardware closely. Each element maps onto a feature:

- **The mine** is a bitmap in ANTIC mode E: 160 pixels across, four colours, two bits per pixel, 40 bytes per line.
- **Bounty Bob** is three players laid over each other, which gives him three colours.
- **The mutants** are player 3 and the missiles, reused down the screen.
- **The cannon** is drawn with player 3 and the missiles, and **the lift** with player 3.
- **Collisions with scenery** come from GTIA's collision registers.
- **The sound effects** use all four POKEY voices.

# Miner 2049er and Big Five Software

Big Five Software was founded in 1980 in Van Nuys, California, by Bill Hogue and Jeff Konyu. Hogue had been a Radio Shack salesman and Heathkit builder. Their first products were arcade-style games for the TRS-80, among them Super Nova, Galaxy Invasion, Attack Force, Meteor Mission II and Robot Attack. Big Five also sold the TRISSTICK, an adapter that let TRS-80 owners use Atari joysticks. Defense Command was Hogue's last TRS-80 game. In 1983 he told 80 Micro that Big Five had "officially left" the TRS-80 market: "if we hadn't come out with our Atari game at the time we did, we probably would have gone out of business."

Miner 2049er was that Atari game, released at the end of 1982. Sources say November or December. Hogue built the game play first and added the mining theme and story afterwards. He combined Donkey Kong-style climbing with the Pac-Man ideas of covering the whole maze and of enemies that become vulnerable. The title is a pun on the "forty-niners" of the 1849 California Gold Rush, moved a century into the future. The folk song "Oh My Darling, Clementine" has the line "dwelt a miner, forty-niner", and the cartridge plays that tune after a game ends (see the chapter on sound and music).

The game was a hit. Reviewers praised it: Tom Hudson of ANALOG wrote that it "looks as if it were designed, not just thrown together". It won Electronic Game of the Year at the 1984 Arkie Awards. Licensing was handled by Barry Friedman's International Computer Group. Ports followed for about twenty systems, including the 5200, ColecoVision, Apple II, IBM PC, Commodore 64, VIC-20, TI-99/4A and a two-cartridge Atari 2600 version by Tigervision. It also inspired Matthew Smith's Manic Miner. Hogue's sequel, Bounty Bob Strikes Back!, followed in 1985 on a bank-switched cartridge.

## The ten stations

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

# Reading the listing

The listing follows a few conventions:

- **Names.** Routines have upper-case names (for example CLAIM_FLOOR or GAME_VBI). Local labels inside a routine share a short prefix (CF_, MU_ ...). Zero-page variables have names such as BOB_X or SECTIONS. The hardware pointers are named after the register they reach, with a "p" in front: pAUDC3 is the zero-page word that holds the address of POKEY's AUDC3 register.
- **Headers.** Each routine starts with a header that says what it does, what it takes and what it returns.
- **Comments.** Inline comments explain the line or block they sit on. Lines whose comment begins with "if", "loop until" or "X = Y + Z" were summarised automatically from short instruction patterns; the rest were written by hand.
- **Data.** Tables are shown in whichever form is clearest: sprites as bit pictures (# for a set bit, or 0-3 for two-bit pixels), text as screen codes with the decoded string, display lists one instruction per line.

Positions use the game's own conventions:

- **Horizontal** positions are in player/missile coordinates, where the playfield's left edge is 48 ($30). Bitmap routines subtract $30 to get the pixel column 0-159.
- **Vertical** positions are bitmap lines 8-191, counted so that bitmap line y is drawn on scan line y + 32, which is also player/missile row y + 32. Bob's BOB_Y is the top of his sprite; his feet are 21 ($15) lines lower.

To rebuild the cartridge:

```
ca65 miner2049er.asm -o miner.o
ld65 -C cart.cfg -o miner.rom miner.o
```

The result is identical to the original 16,384-byte image.

# Architecture

## Memory map

|Address|Contents|
|$0000-$00FF|zero page: hardware pointer table $10-$6F; game variables $70-$FF|
|$0200-$0223|interrupt vectors (both the 400/800 and the 5200 layouts are written)|
|$0300-$07FF|player/missile graphics: missiles at $0300, Bob in players 0-2, mutants in player 3|
|$0800-$08EF|high-score table and the text of the title screens|
|$0917-$0A24|screen text, item table, mutant records, pulverizers|
|$1C00-$1FFF|second player/missile buffer for the high-score screen; the 5200's font copy|
|$2000-$20FF|game display list and status line|
|$2100-$3DBF|the mine: 184 lines x 40 bytes|
|$3DC0-$3F2F|bitmap line-address tables (LINE_LO/LINE_HI, indexed from y = 8)|
|$3F30-$3F5F|moving platforms|
|$8000-$91F0|cartridge data: screens, text, sprites, items, station descriptions|
|$91F1-$BFBC|cartridge code|
|$BFBD-$BFFF|tables and the cartridge trailer|

The 16K of RAM the game needs is used almost entirely. The display list, status line and bitmap alone take 7.6K.

## One ROM, two machines

The last six bytes of the cartridge serve both machines:

```
$BFFA  .word RESTART      400/800: start address
$BFFC  .byte $00          400/800: "a cartridge is present"
$BFFD  .byte $FF          400/800: option byte;  5200: "skip the title screen"
$BFFE  .word COLD_START   400/800: init address;  5200: start address
```

On the 400/800, bit 7 of the option byte marks a *diagnostic* cartridge. The OS jumps to the init address straight after reset, before it has initialised anything, so the game owns the machine from the first instruction. On the 5200, the BIOS reads $FF at $BFFD as "no title screen" and jumps through the word at $BFFE, which is the same address.

COLD_START then works out which machine it is on. On the 5200, $F800 is the start of the BIOS character set, whose first two characters (space and "!") are made only of the bytes $00 and $18. On the 400/800, $F800 is in the middle of OS code. If all sixteen bytes from $F800 are $00 or $18, the game is on a 5200.

It then builds the **hardware pointer table** in zero page:

```
$10 + 2r  ->  GTIA register r     ($D000 + r on the 400/800, $C000 + r on the 5200)
$50 + 2r  ->  POKEY register r    ($D200 + r,               $E800 + r)
```

From then on, nearly every access to GTIA and POKEY is indirect through the table, `STA (pAUDC1),Y` with Y = 0, so the same code works on both machines. Only ANTIC, which is at $D400 on both, is addressed directly. The cost is small: an indirect store takes 6 cycles instead of 4 and needs Y = 0. A few places use a well-chosen X with `(zp,X)` to reach a different register from a nearby pointer. For example, `STA ($3A,X)` with X = $1E writes AUDF3, because $3A + $1E = $58, which is pAUDF3.

The other differences are handled where they arise:

- **Input.** On the 5200 the analog stick is read through POKEY's pot inputs and converted into the four direction bits of the 400/800's PIA joystick port (READ_STICK).
- **Keypad.** POLL_KEYS translates the 5200's keypad codes into the 400/800 key codes the game expects. The # key becomes the space bar, PAUSE becomes ESC and RESET restarts the cartridge.
- **Fonts.** The text renderer draws from whichever ROM font the machine has (FONTPAGE).
- **High scores.** On the 400/800 they survive the RESET key, because the OS's warm-start flag tells the game it was not a power-up. On the 5200 there is no such flag, so COLD_START clears them at power-up; the keypad's RESET key goes straight to RESTART, so they survive that too.

The SET_VBI routine shows how far this goes. The 400/800 OS saves A, X and Y before it calls the game's vertical-blank handler; the 5200 BIOS does not. So on the 5200 the game points the BIOS vector at a six-instruction stub, VBI_5200, which saves the registers itself and continues through the handler. Every handler can then end with the same NMI_EXIT on either machine.

## Program flow

The cartridge cycles through these screens:

```
power-up / RESET
   COLD_START  ->  RESTART
                     credits (station 11, recorded demo)   --START-->  game
                     game-over tune (Clementine)
                     high-score screen   ---- 30 s --->  demo of station 1
                                         --START-->  game
game:  START_GAME -> PLAY_STATION:  prepare screen -> station -> next station / next player
       out of lives -> "Game Over" -> name entry -> high-score screen
```

PLAY_STATION draws a station behind the "MINER 1 / PREPARE FOR / STATION 1 / ZONE 1" screen. The station is drawn pixel by pixel and takes a while, so the three-second prepare screen hides it. When the countdown ends, START_STATION switches the display to the game screen and installs two handlers:

- **GAME_VBI**, the vertical-blank handler. It runs the whole game once per frame.
- **DLI_MUTANTS**, the display-list interrupt. It runs four times per frame and manages the mutants.

The main loop, GAME_LOOP, has almost nothing to do. It polls the console keys (OPTION, START, and digit keys during the demo), keeps the TNT readout up to date on station 10, and waits for one of two events:

- the turn ends (ALIVE reaches 0), after which TURN_OVER decides what comes next;
- the end-of-station wipe finishes (WIPE_LINE reaches 0), after which the next station is built.

Running everything in the interrupt keeps the game's speed steady whatever the station looks like. The game drops no frames, because there is no frame loop to fall behind.

## The vertical blank, step by step

GAME_VBI is a long routine that does the following, in order:

1. Read the keyboard (POLL_KEYS), count the frame, reload the display list pointer, and place the bonus box (the four missiles, double width, behind the bonus digits).
2. Read the collision registers for the bottom band, set the status-line colours, and read the 5200 stick.
3. If an item was just picked up, turn every living mutant edible.
4. If the bonus is under 700, flash the bonus box, make Bob's face flicker and play a ticking sound that speeds up as time runs out.
5. Handle pause.
6. Make the current player's score blink (it is written with bit 7 set, and CHACTL bit 0 blanks such characters).
7. Check whether Bob touched a deadly colour-1 object: the waste on station 6, the moving bar on station 8, a pulverizer on station 9.
8. If Bob is dying, make him throb (the players change width) and play noise.
9. Play the extra-life jingle.
10. Move Bob (MOVE_BOB) and the moving platforms (UPDATE_LIFTS), set Bob's sprite position and size, claim girder sections under his feet (CLAIM_FLOOR), then move the pulverizers.
11. Count down to the end of the turn after a death.
12. On station 11 only: run the credits reveal and skip straight to step 16.
13. Redraw the status line, update the items, run the bonus timer, and count the bonus into the score and wipe the screen once the station is clear.
14. Add points for an eaten mutant.
15. Check the phone-number cheat.
16. In VBI_TAIL: advance the demo recording, run the cannon or the lift, and return.

# The screen

## The display list

BUILD_DLIST writes the game's display list at $2000:

```
$2000  3 x "8 blank lines"
$2003  mode 2, LMS $20D8, DLI       status line, 40 text characters
$2006  184 x mode E                 the mine, 160 x 184, four colours
       lines 46, 93, 140 set DLI    band boundaries for the mutants
       line 96 has LMS $3000        ANTIC cannot cross a 4K boundary
$20C0  JVB $2000
```

ANTIC's address counter wraps within 4K. A bitmap that starts at $2100 would run past $3000 on its 97th line, so that line reloads the address explicitly. It is needed only because the bitmap is 7,360 bytes long.

!img screen_bands.png|The game screen with its display-list interrupts. Each band shows two mutants: one in player 3, one in the four missiles.|6.5

## Pixels

In ANTIC mode E each byte holds four pixels, two bits each, leftmost pixel in the top bits. A pixel value of 0 is the background; 1, 2 and 3 select the colour registers COLPF0, COLPF1 and COLPF2. Miner uses them consistently:

|Value|Register|Used for|
|0|COLBK|background (black)|
|1|COLPF0|items, text, deadly objects (waste, crusher bar, pulverizers)|
|2|COLPF1|ladders, slides, points numbers|
|3|COLPF2|girders, platforms|

!img mode_e.png|How a mode E byte maps to pixels, and the tables used to set them.|6.3

PLOT and its variants find the byte as `LINE_LO/HI[y] + x/4`, where the two 184-entry tables give the address of each bitmap line. They then use the pixel's position within the byte, `x AND 3`, to index two small tables. PIXEL_MASK ($C0 $30 $0C $03) isolates a pixel's two bits. PIXEL_SET supplies the bits for a colour, and is indexed by `PLOT_COLOR + (x AND 3)`, where PLOT_COLOR is 0, 4 or 8 for colours 1-3 and 12 for the background. The tables overlap: colour 3's entries are PIXEL_MASK itself, and the four zero bytes after it give the background. PLOT_IF_EMPTY draws only on background pixels, which is how ladders and slides avoid painting over girders. READ_PIXEL returns a pixel's colour and sets the Z flag if it is 3, which makes "is there a girder here?" a single subroutine call.

## Colours

Each turn, START_STATION picks the three playfield colours at random, with two rules: the three hues must differ, and so must the three brightness values, which are taken from {4, 6, 8}. The second rule keeps items, ladders and girders apart on a black-and-white television. Every play of a station therefore looks different, as the screenshots show.

The status line takes its colours from GAME_VBI. The first display-list interrupt then sets colours 2 and 3 for the mine below it (and, on the transporter stations, colour 1 as well).

## Text in the bitmap

The game uses two kinds of text. Fixed screens such as the title, prepare, name-entry and high-score screens use ANTIC character modes. Text inside the mine ("TNT Charge= 0 Tons", "DANGER", the credits, "Game Over") is drawn into the bitmap pixel by pixel by DRAW_CHAR. DRAW_CHAR reads the machine's ROM font, either at $E000 or at $F800 on the 5200, and can double the height. It paints 1 bits in the ink colour and clears 0 bits, so text erases whatever is behind it.

# Building a station

A station is described entirely by data. STATION_TABLE gives the address of four lists for each station, and four more tables give the items, the mutants, Bob's starting position and the transporter column:

|List|Entry|Meaning|
|girders|sections, x, y|three sub-lists: sloping down, sloping up, flat|
|ladders|height, x, y, style|8 pixels wide, a rung every 4 lines|
|slides|rows, x, y, step|an 8-pixel band shifted "step" pixels per line|
|moving platforms|timer, width, x, y, travel, speed|a 3-line bar that moves back and forth|
|items|shape+$80, y, x|a picture copied byte by byte into the bitmap|
|mutants|8 records of 11 bytes|start position, patrol, speed, colour timing|

## Girders and sections

The unit of the game is the girder *section*, 4 pixels wide. DRAW_GIRDERS draws each section as three thin stripes of colour 3, two lines apart, and counts it into SECTIONS. On sloping girders each section is one line higher or lower than the one before. On flat girders, sections alternate between two stripe patterns, which gives them a brickwork look. That alternation turns out to be essential to how claiming works (see "Claiming the floor").

!img girders_zoom.png|Part of station 1, magnified: unclaimed sections (striped brickwork) on the left, sections Bob has claimed (solid) on the right.|5.0

## Station machinery

Station-specific set-up code adds the rest:

- **Stations 3 and 7: transporters.** DRAW_TRANSPORTER draws the column of four booths from an 8-bit run-length pattern (BOOTH_SHAPE), each bit two pixels wide, and writes the digits 1-4 in them with the font renderer.
- **Station 6: the waste tank.** DRAW_WASTE draws a solid colour-1 box and cuts "DANGER / Radioactive / Waste" into it in the background colour.
- **Station 8: the lift.** The lift's platform, scissor arms and cart are drawn into player 3, and its track into the bitmap.
- **Station 9: the pulverizers.** SETUP_PULVERIZERS draws the beam and posts and gives the four heads random starting delays.
- **Station 10: the cannon.** The cannon goes into player 3 plus the missiles. The TNT store is drawn with its shelves and sign.

!img machines.png|The machinery, drawn from the ROM's data: a transporter booth, a pulverizer head, the lift and the cannon.|6.0

## Overlapping data

The data area is full of sharing:

- A list's 0 terminator is often the first byte of the next list.
- Station 1's item list ends with the 0 that also serves as "no ladders, no slides, no platforms" for every station that lacks them.
- Entry 0 of STATION_TABLE is also ITEM_SHAPES 33-36, the goblet and the three TNT bundles.
- Station 10's eighth mutant record runs ten bytes into station 1's girder list. That is harmless, because the record's first byte, 0, means "no mutant".
- Several girder lists start inside the slide list before them.

Because the generated listing follows the ROM byte by byte, these overlaps show up as labels that sit in the middle of what looks like another table.

# Bounty Bob

## Three players, three colours

Bob is drawn with players 0, 1 and 2 laid over each other: blue ($8A) for his coat, orange ($3A) for his face and hands, white ($0F) for his legs and the stripe down his front. PRIOR is set to $31: players in front of the playfield, with *multicolour* mode on. In multicolour mode, where players 0 and 1 overlap, GTIA ORs their colours, so the hat comes out a fourth colour, $BA (green). Player 2 shows only where the other two are empty.

!img bob_layers.png|Frame 1 taken apart: the three players and the combined sprite.|5.5

Each animation frame stores the three layers back to back, 20, 17 and 17 lines, with each layer's first line shared with the previous layer's last: 52 bytes, stored 51 bytes apart, so a frame's last byte is also the next frame's first. DRAW_BOB copies them into player memory from the bottom up, and the blank lines at the ends erase his previous position as he moves.

!img bob_frames.png|Bob's twelve animation frames (frame 0, standing, is the same data as frame 1).|6.5

## The movement state machine

MOVE_BOB is called once per frame and branches on Bob's state:

|State|Condition|Routine|
|dying|SPECIAL = 1|MELT_BOB|
|dead|SPECIAL = 2|nothing; GAME_VBI ends the turn|
|transporting|SPECIAL = 3-7|TRANSPORT|
|falling|BOB_FALL|FALLING|
|sliding|SLIDE_LEN|SLIDING|
|jumping|frame 11-12|JUMPING|
|climbing|frame 7-10|ON_LADDER|
|on a girder|otherwise|button, stick, ladders, walking, booths|

**Walking** moves Bob one pixel every other frame and cycles through three frames. After each step, the routine tests the bitmap under his feet with READ_PIXEL:

- girder one line above his feet: the girder rises, so he steps up a line;
- girder under his feet: nothing to do;
- girder one line below: the girder falls, so he steps down a line;
- no girder at all: he has walked off the edge and starts to fall.

Bob follows sloping girders this way with no slope data at all: the bitmap is the collision map.

**Ladders.** TRY_CLIMB_UP looks for a ladder whose foot is level with Bob's feet or one line below them and within two pixels of his x, lines him up with it, and starts the climb. MOVE_A and MOVE_B count the lines to the top and to the bottom, and reaching either end puts him back on his feet. Frames 9 and 10 show him stepping on or off at the top.

**Jumping.** START_JUMP takes the direction from the stick. Each frame JUMPING moves Bob vertically by the next entry of JUMP_ARC: 11 lines up, a pause, 3 up, a pause, 2 up, then down. Sideways he moves one pixel every other frame, unless a wall stops him. After the table runs out he falls one line per frame until LAND_CHECK finds a girder.

!img jump_arc.png|Height of Bob's jump frame by frame, from JUMP_ARC.|6.0

**Falling** is counted in FALL_LEN, one per frame. Forty frames of falling kill him; because a jump also counts its descent, a drop of about 18 lines below the take-off point is already fatal. When he lands, LAND_CHECK makes sure his feet are on the top stripe of the girder, not inside it.

**Slides.** If Bob stands exactly at the top of a slide, he rides it: one line down and "step" pixels sideways per frame, with a falling whistle.

**Dying.** Bob throbs, his players switching between normal, double and quadruple width with an offset that keeps him centred, and at the same time he melts (if he dies in the air, he melts when he lands): MELT_BOB feeds random bytes in at his feet and shifts each player's column down a line per frame until he is a puddle of noise.

## Claiming the floor

CLAIM_FLOOR is the heart of the game. It runs every frame while Bob walks or stands:

1. FEET_OFFSETS gives the x positions of his two feet for the current animation frame. For each foot, the routine reads the pixel at the feet line. It must be girder (colour 3).
2. It reads the next two lines down. An unclaimed section has gaps between its stripes. If the line under the feet is a gap, the gaps are at +1, +3 and +5; if not, they are at +2 and +4. If both lines are solid, the section is already claimed and there is nothing to do.
3. It finds the section's left edge by scanning along a gap row. A neighbouring section's stripes are at different heights, either because it belongs to the other brickwork pattern or because it is a step higher or lower on a slope, so where the gap row turns solid is the boundary.
4. It fills the gap rows of those four pixels with colour 3. The section turns solid, SECTIONS decreases by one and the score goes up by 5.

So the bitmap is not just the picture of the mine. It is also the record of what has been claimed. There is no array of section flags, which saves both memory and time. The brickwork pattern of the flat girders is what makes the boundaries findable. The station is complete when SECTIONS reaches zero.

# Mutants

## Two sprites, eight mutants

Each station has up to eight radioactive mutants, but the hardware has only player 3 and the missiles free once Bob has used three players. Miner divides the screen into four horizontal bands with display-list interrupts: one at the end of the status line and three in the bitmap. Each band shows two mutants: one drawn with player 3, the other with the four missiles placed side by side in "fifth player" mode (PRIOR bit 4), which makes them an 8-pixel sprite coloured by COLPF3. At each band boundary, DLI_MUTANTS re-positions the two sprites and sets their colours for the band below. The player and missile memory holds all eight shapes at once, each at its own height, so only positions and colours need to change mid-screen.

DLI_MUTANTS also does three other jobs:

- **Collisions.** At the start of each band it saves the collision registers for the band that just ended, then clears them (READ_HITS). Bob is players 0-2, so a collision bit 0-2 in the missile-to-player or player-3-to-player registers means that band's mutant touched him. Reading and clearing per band is what lets two sprites stand in for eight mutants and still tell which one hit Bob.
- **Movement.** It moves and animates two mutants per interrupt, spreading the work over the frame. The mutant it moves is not the one it is currently positioning; the indexing is arranged so that each record is updated once per frame.
- **Band effects.** It sets the transporter booths' colour (green, or red while the transporter recharges), positions the cannon (station 10) or the lift (station 8), which borrow the same sprites in their own band, and makes colour 1 flicker in the bottom band on stations 5, 6, 8 and 9. On station 6 that makes the radioactive waste glow.

!img mutants.png|The ten mutant shapes. The "edible" pair raise their arms; an eaten mutant becomes the number of points it was worth.|6.0

## Behaviour

Each mutant patrols back and forth along a girder. Its station record gives:

- its height and starting position;
- the length of its patrol and its speed (frames per step);
- the timing of its shimmer (its brightness pulses up and down by 2).

The step delay is reduced by the zone number, so mutants get faster as the game goes on.

When Bob picks up an item, ITEM_GOT is set, and on the next frame GAME_VBI turns every living mutant edible. Each turns green ($C6) with an edible counter of $AF - 16 x min(zone, 9): 159 in zone 1, falling to 31 from zone 9 (the subtraction runs with the carry clear, so it is one less than $B0 - 16n). It stays green for that many frames, then blinks: purple for 5 frames, green again for half the previous time, and so on until the counter reaches zero. The blinking speeds up as a warning. In zone 1 a mutant stays edible for about six seconds; from zone 9 on, about one and a half. Touching an edible mutant eats it for 80 or 90 points, chosen at random, and the mutant shows the number, flashing in random colours, while a rising tone plays for about two seconds. Touching a mutant that is not edible kills Bob.

# Items, scoring and time

## Items

Items are small pictures stored as whole bytes (four pixels per byte) and copied straight into the bitmap. Each has a width, a height and a points value. When Bob touches one, UPDATE_ITEMS does five things:

- draws the points number over the item ("100" ... "500"; the points byte doubles as the shape number of the number picture);
- erases the rest of the item;
- adds points x 100 to the score;
- sets ITEM_GOT, which turns the mutants edible;
- plays a falling whistle.

The "BF" (Big Five) logo on station 7 is worth 1,100.

On station 10 the items are bundles of TNT. Their points value, 1 to 3, is also the number of tons added to the cannon's charge.

On station 5 one item is a trap. UPDATE_ITEMS treats the goblet (shape 33) specially there: touching it sets KILLED. The goblet sits just above Bob's starting place, so a jump straight up at the start of the station kills him. This was confirmed in the emulator.

!img items.png|All 36 item shapes in ITEM_SHAPES, with their points. Shapes 1-5 and 11 are the points numbers themselves.|6.5

## Score

The score is six decimal digits, one per byte. ADD_SCORE adds a value to any digit and carries upwards. Points come from:

|Event|Points|
|claiming a section|5|
|item|100-500 (BF logo 1,100)|
|eating a mutant|80 or 90|
|bonus left at the end of a station|counted in at 100 a tick|

When the score first reaches 10,000, Bob gets an extra life. The award is detected by the ten-thousands digit becoming non-zero while XLIFE still holds its initial value, 10. A short jingle then plays while the screen background flashes blue.

## The bonus timer

Each station starts with a bonus of BONUS_BASE + 500 per zone (at most 9,900), shown in a box on the status line. The box is the four missiles, set to double width. The bonus drops by 100 every three seconds. Below 700 the box flashes, Bob's face flickers and a tick plays faster and faster. If the bonus reaches zero before the station is clear, Bob dies.

## The end of a station

When the last section is claimed:

1. Bob vanishes.
2. TALLY counts the bonus into the score 100 at a time, with a click each time.
3. WIPE removes the screen from the bottom up. Each frame it overwrites the next display-list line with a JVB (jump and wait for vertical blank), so ANTIC simply stops drawing there, and a rising tone plays.
4. When the wipe reaches the top, the main loop builds the next station.

# Station machinery in detail

## Transporters (stations 3 and 7)

To use a transporter, Bob stands still inside a booth and presses a digit key 1-4. The transporter runs as a five-state sequence in TRANSPORT:

1. Bob dissolves into sparkles: SPARKLE_BOB ANDs every line of his sprite with a random byte. A random buzz on voice 3 grows louder.
2. A short pause follows.
3. Bob appears at the destination booth, while sparkles linger at the old booth and his colours flash in both booths.
4. He sparkles in place at the new booth.
5. He re-forms as the buzz fades.

Afterwards the transporter is locked for five steps of 64 frames, about five seconds (128 frames each from zone 5 on, about ten seconds), and the booths are red until it recharges. They are also red, briefly, when the station starts.

## The lift (station 8)

Standing on the lift and pressing the space bar (the # key on a 5200) hands the joystick to the lift. The stick then drives it left and right along its track and up and down. It rises at half the speed it falls. Bob rides along, and pressing space or the button again gives control back.

The lift is player 3 in the band that contains it. As it moves up or down, LIFT_CONTROL rewrites the top of its column of player data: it clears the line above, writes the two-line platform and one more line of the scissor pattern. The arms seem to extend and fold because the pattern's phase steps through a seven-line cycle.

## Pulverizers (station 9)

Four heads hang from a beam. Each waits, drops 22 lines, rises again and waits for a delay that shrinks with the zone. Each head's top line is a thin rod. As the head descends, that line is left behind each frame, so the rod grows down from the beam with no extra drawing code. The heads are drawn in colour 1, and touching colour 1 on this station is fatal. Station 9's moving platforms behave as lifts: the code holds each one at the end of its run until Bob stands on it.

## The cannon (station 10)

Bob collects TNT bundles worth 1-3 tons each, then steps into the cannon's mouth. The cannon then follows him along its track, and the button fires it:

|Charge|Result|
|1 ton|Bob reaches the first platform|
|2 tons|the second platform|
|3 tons|the third platform|
|4 tons or more|he is shot off the top of the screen and falls back upside down|

With 4 tons or more loaded, the word "DANGER" appears on the screen as a warning. After such an over-charged shot, DRAW_BOB_FLIPPED draws Bob upside down for the rest of the turn, by copying his sprite top-to-bottom instead of bottom-to-top. SHOW_TNT keeps "TNT Charge= nn Tons" up to date on the screen.

# Title screens and the attract sequence

## The credits

After power-up the game plays station 11, a station of plain girders with no mutants, which hides the credits. The credits are drawn at the start in pixel colour 1, whose register is set to black, so they are invisible. Bob, driven by the recording DEMO_CREDITS, walks the girders. Every frame GAME_VBI looks at a one-pixel column 30 lines tall through him and repaints every colour-1 pixel in colour 2, so the words appear behind him as he passes. When he reaches the bottom right, colour 1 is made visible, the full text appears, and a display-list interrupt (DLI_RAINBOW) runs alone, with no vertical-blank interrupt, striping the text with a scrolling rainbow while Clementine plays.

!img credits_start.png|The credits being revealed as Bob walks.|3.2
!img credits_end.png|The finished credits. The last line is the cheat code.|3.2

## The high-score screen

The high-score screen surrounds the table with a frame of 36 "5" characters whose colours march round it like theatre lights. The effect combines most of the techniques in the program:

- **The rows never move.** The top and bottom rows are single lines of ANTIC mode 7 text kept in ROM. HSCROL slides each row by 0-15 colour clocks, which is two character cells. Each time the scroll wraps, the colours rotate one light, so the eye sees continuous motion.
- **Ten colours on a line.** Mode 7 gives four colours per line. A display-list interrupt jumps into TITLE_KERNEL, a 62-byte loop copied to RAM at $0400. On each of the row's 12 scan lines it writes all four playfield colour registers for the left four lights, then all four again for the right four, while the beam is half-way across. The two middle lights are players 1 and 2, which have their own colour registers: 4 + 2 + 4 = 10.
- **Cycle counting.** The kernel has one WSYNC before the first line and none inside the loop. Each pass is about 76-78 CPU cycles; with the cycles ANTIC steals for its own memory accesses on a mode 7 line, that is meant to fill a scan line. To follow the fine scroll, SET_FINE_SCROLL patches two opcodes, one before the loop and one in it, to CPX zp, CMP zp,X or ASL zp, which take 3, 4 or 5 cycles, so the colour changes move by 6, 8 or 10 colour clocks.
- **Patched for both machines.** Every frame, KERNEL_COLS_TOP and KERNEL_COLS_BOTTOM write the colours into the kernel's eight `LDA #` operands, and KERNEL_COLS_TOP also rewrites the high byte of each `STA COLPFn` with the GTIA page taken from the pointer table, $D0 or $C0, because the kernel has to use absolute addresses to stay fast enough. That is why it must run from RAM.
- **Side columns.** Players 0 and 3, in double-line resolution, form the side columns. A display-list interrupt on every text line recolours them. They move by redrawing into a second player/missile buffer and switching PMBASE between $0400 and $1C00, which is double buffering.
- **Smaller effects.** The ten score lines get a moving rainbow from the same interrupts, "HIGH SCORES:" pulses in brightness, "START" blinks in inverse video, and a soft tone repeats.

The display list itself is in ROM ($8000). Its final JVB instruction's address bytes are also the first two characters of the bottom row of lights, so the jump target is nonsense. That is harmless, because TITLE_VBI reloads the display list pointer every frame.

!img title_lights.png|Who draws which light on the high-score screen.|5.5
!img kernel_timing.png|One pass of TITLE_KERNEL.|6.5

Thirty seconds after the screen appears, unless a game has been started, the demo begins: station 1 played from the recording DEMO_STATION1. Each recording is a list of (input, frames) pairs, where the input byte has the joystick in the low four bits and the button in bit 4. READ_STICK and READ_BUTTON read from the recording instead of the hardware whenever DEMO_PTR is set.

## Other screens

!img prep.png|"Prepare for Station": the background flashes and a siren plays while the station is drawn behind it.|3.2
!img go_06.png|"Game Over / Miner 1" is cut into a box that is filled column by column with a rising two-tone sound.|3.2
!img go_name.png|Name entry: up to eight characters, typed on the keyboard or picked with the 5200 stick. The missiles form the cursor and the background is a rainbow from a DLI.|3.2

## The phone-number cheat

During a game, typing Big Five's telephone number, 213-782-6861, then SHIFT plus a digit, warps to that station (0 means station 10). PHONE_CODE compares each digit typed with the bytes of the number as printed at the end of the credits text, "(213) 782-6861", skipping the bracket, the space and the dash. The printed text and the cheat code are the same bytes. A wrong digit starts the count again, and a held key repeating the same digit is ignored. On the 5200, the lower fire button plays the part of SHIFT.

# Sound and music

POKEY's four voices are used for different effects:

|Voice|Used for|
|1|game-over tune melody, siren on the prepare screen, death noise, time-running-out tick, title tone|
|2|game-over tune harmony, mutant being eaten, name-entry clicks|
|3|footsteps, jumps, falls, slides, transporter buzz, lift motor, cannon|
|4|item whistle, extra-life jingle, bonus tally clicks, screen-wipe tone|

GAME_OVER_TUNE plays "Oh My Darling, Clementine" three times: on voice 1, then on voice 2, then on both together. The tune table holds the melody as POKEY dividers ($28 C, $35 the G below, $1F E, $1A G, $1D F, $23 D, $2A B) with lengths in frames. Voice 2 does not read the table; its note is calculated from the melody note as (note - $1D) x 4 + $79, which places it roughly two octaves lower, and a single special case covers note $1A. Each note starts at full volume with a pure tone and decays one step per frame, which sounds like a plucked instrument. START, the button or a digit key cuts the tune short.

The footsteps are a 14-frame pattern on voice 3: a low thud, silence, a click, silence.

# Tricks lost to time

Many of the techniques in this program were common knowledge among Atari programmers in 1982 and are now mostly forgotten:

- **A pointer table instead of fixed addresses** lets one binary drive chips at different addresses on two machines.
- **A diagnostic cartridge** owns the machine from the first instruction.
- **Self-modifying code for timing:** opcodes chosen for their cycle counts, patched into a scan-line loop.
- **Self-modifying code for portability:** the high bytes of absolute stores patched with the chip's page at run time.
- **Mid-line colour changes** go beyond the hardware's colours-per-line limit.
- **Sprite multiplexing** with display-list interrupts, and collision registers read per band.
- **Fifth-player mode,** which turns the four missiles into one more sprite.
- **Double-buffered player graphics** by flipping PMBASE.
- **The screen as the database:** the girders' claimed or unclaimed state lives only in the bitmap.
- **A display list rewritten on the fly** to wipe the screen line by line.
- **Hidden text revealed by recolouring pixels** whose colour register is set to black.
- **Harmony calculated from the melody** instead of stored.
- **Tables that overlap their neighbours** to save bytes.
- **Analog joystick input converted to digital directions,** so one input routine serves both machines.

# Oddities and bugs

**A harmless pointer bug.** When Bob lands safely from a jump or fall, LAND_CHECK means to write 0 (silence) to AUDC3 with the same `STA (pAUDF3+1,X)` that START_DEATH, a few lines earlier, uses to start its death tone. START_DEATH has X = 1 at that point, which makes the pointer pAUDC3. LAND_CHECK has X = 0, so the 6502 forms an address from bytes $59 and $5A: the high byte of the AUDF3 pointer and the low byte of the AUDC3 pointer. The result is $05D2 ($05E8 on the 5200): row $D2 of player 1, which belongs to Bob's sprite only when he is at that height, and is redrawn whenever he is (on the 5200, row $E8 is below the visible screen). Voice 3 is left as it was and is set again by the footstep code a frame later, so nobody would ever notice.

**Filler that does nothing.** BUILD_STATION and SETUP_ITEMS contain short sequences with no effect, such as `LDA #$4C / LDA $A546`. $4C is the JMP opcode, so these may be places kept free for a patch. COLD_START has three NOPs, and UPDATE_ITEMS starts with a sequence that compares a ROM byte with itself minus 5 and ignores the result, padded with NOPs. That looks like a check that was patched out. The evidence for either reading is only the shape of the code.

**Tables read past their ends.** The bonus for station 10 is read from one byte past the end of BONUS_BASE, which is the first byte of the next table. Station 11 reads its starting x and its transporter column from one past the end of their tables in the same way. The values happen to be the ones wanted.

**The poisoned goblet.** Station 5's goblet kills Bob on contact. It is hard to know whether this was meant as a trap or as a protection against something; it is a deliberate test in the code, not a side effect.

**The credits station's mutant pointer.** MUTANT_LISTS has an entry for station 11 that points into RAM ($1E18), because that word is really the first two bytes of the mutant shapes. The 88 bytes it points to are read, but through a mask of zero, so the credits get no mutants.

# Graphics gallery

The ten stations below are screenshots from the Atari800 emulator, reached with the cheat code. Colours are chosen at random each time a station starts, so they will differ from play to play.

!img st_1.png|Station 1, The Mine Shaft.|3.2
!img st_2.png|Station 2, The Slides.|3.2
!img st_3.png|Station 3, The Transporters.|3.2
!img st_4.png|Station 4, The Lillipads.|3.2
!img st_5.png|Station 5, Advanced Lillipads.|3.2
!img st_6.png|Station 6, Radioactive Waste.|3.2
!img st_7.png|Station 7, Advanced Transporters (the "BF" logo is an item worth 1,100).|3.2
!img st_8.png|Station 8, The Lift.|3.2
!img st_9.png|Station 9, The Pulverizers.|3.2
!img st_10.png|Station 10, The Cannon.|3.2

# Sources

Facts about the Atari hardware, its history and the game's history come from these sources. Everything about how the program works comes from the disassembly itself.

- Atari 8-bit computers. Wikipedia. https://en.wikipedia.org/wiki/Atari_8-bit_computers
- Atari 400. Wikipedia. https://en.wikipedia.org/wiki/Atari_400
- ANTIC; CTIA and GTIA; POKEY. Wikipedia. https://en.wikipedia.org/wiki/ANTIC
- Atari 5200. Wikipedia. https://en.wikipedia.org/wiki/Atari_5200
- Claus Buchholz, "Converting to 5200", A.N.A.L.O.G. Computing #15, January 1984. https://atarimuseum.ctrl-alt-rees.com/videogames/consoles/5200/conv_to_5200.html
- oldcomputers.net, Atari 400. https://www.oldcomputers.net/atari400.html
- Low End Mac, "A history of Atari's 8-bit personal computers". https://lowendmac.com/2015/a-history-of-ataris-8-bit-personal-computers/
- Miner 2049er. Wikipedia. https://en.wikipedia.org/wiki/Miner_2049er
- Big Five Software. Wikipedia. https://en.wikipedia.org/wiki/Big_Five_Software
- Owen Linzmayer, "Atari strikes gold", Creative Computing, February 1983. https://www.atarimagazines.com/creative/v9n2/128_Atari_strikes_gold.php
- John J. Anderson, "Mastering Miner 2049er", Creative Computing Video & Arcade Games, Fall 1983. https://atarimagazines.com/cva/v1n2/miner.php
- "Miner 2049er" and "Interview with Bill Hogue", trs-80.org. https://www.trs-80.org/miner-2049er.html and https://www.trs-80.org/interview-bill-hogue.html
- Atarimania, Miner 2049er (the cheat code). https://www.atarimania.com/game-atari-400-800-xl-xe-miner-2049er_3410.html
- Oh My Darling, Clementine. Wikipedia. https://en.wikipedia.org/wiki/Oh_My_Darling,_Clementine
