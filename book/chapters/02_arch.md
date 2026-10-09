# Reading the listing {#reading}

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

# Architecture {#architecture}

## Memory map {#memmap}

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

## One ROM, two machines {#tworoms}

The last six bytes of the cartridge serve both machines:

```
$BFFA  .word RESTART      400/800: start address
$BFFC  .byte $00          400/800: "a cartridge is present"
$BFFD  .byte $FF          400/800: option byte;  5200: "skip the title screen"
$BFFE  .word COLD_START   400/800: init address;  5200: start address
```

On the 400/800, bit 7 of the option byte marks a *diagnostic* cartridge. The OS jumps to the init address straight after reset, before it has initialised anything, so the game owns the machine from the first instruction. On the 5200, the BIOS reads $FF at $BFFD as "no title screen" and jumps through the word at $BFFE, which is the same address.

COLD_START then works out which machine it is on. On the 5200, $F800 is the start of the BIOS character set, whose first two characters (space and "!") are made only of the bytes $00 and $18. On the 400/800, $F800 is in the middle of OS code. If all sixteen bytes from $F800 are $00 or $18, the game is on a 5200. It then builds the hardware pointer table described in the next chapter.

The other differences are handled where they arise:

- **Input.** On the 5200 the analog stick is read through POKEY's pot inputs and converted into the four direction bits of the 400/800's PIA joystick port (READ_STICK).
- **Keypad.** POLL_KEYS translates the 5200's keypad codes into the 400/800 key codes the game expects. The # key becomes the space bar, PAUSE becomes ESC and RESET restarts the cartridge.
- **Fonts.** The text renderer draws from whichever ROM font the machine has (FONTPAGE).
- **High scores.** On the 400/800 they survive the RESET key, because the OS's warm-start flag tells the game it was not a power-up. On the 5200 there is no such flag, so COLD_START clears them at power-up; the keypad's RESET key goes straight to RESTART, so they survive that too.
- **Interrupt entry.** The 400/800 OS saves A, X and Y before it calls the game's vertical-blank handler; the 5200 BIOS does not. So on the 5200 SET_VBI points the BIOS vector at a six-instruction stub, VBI_5200, which saves the registers itself and continues into the handler. Every handler can then end with the same NMI_EXIT on either machine.

:::op LDA abs,X (machine detection)
name: load absolute, indexed by X
enc: BD lo hi
cycles: 4 (5 if the index crosses a page)
flags: N, Z
body: COLD_START's test is `LDX #$0F / loop: LDA $F800,X / BEQ next / CMP #$18 / BNE not5200 / next: DEX / BPL loop`. It reads sixteen bytes of whatever ROM is at $F800 and accepts only $00 and $18. BPL ("branch if plus") ends the loop when DEX takes X from 0 to $FF, whose bit 7 is set; counting down to -1 this way lets the loop include index 0 without a separate compare.
:::

## Program flow {#flow}

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

The main loop, GAME_LOOP, has almost nothing to do. It polls the console keys (OPTION, START, and digit keys during the demo), keeps the TNT readout up to date on station 10, and waits for one of two events: the turn ends (ALIVE reaches 0), or the end-of-station wipe finishes (WIPE_LINE reaches 0) and the next station is built.

Running everything in the interrupt keeps the game's speed steady whatever the station looks like. There is no frame loop to fall behind.

!fig framebudget|One frame of the game screen, line by line, with the CPU time each interrupt handler uses on station 1. The cycle counts were measured by running the handlers in the 6502 harness (instruction cycles only; ANTIC's stolen cycles come on top). The vertical blank, where ANTIC fetches almost nothing, has room for the 3,000-cycle GAME_VBI.

## The vertical blank, step by step {#vbi}

GAME_VBI does the following, in order:

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

# The hardware pointer table {#pointers}

## Building it {#ptrbuild}

Right after machine detection, COLD_START fills zero page from $10 to $6F with 48 pointers:

```
$10 + 2r  ->  GTIA register r     ($D000 + r on the 400/800, $C000 + r on the 5200)
$50 + 2r  ->  POKEY register r    ($D200 + r,               $E800 + r)
```

The code is two short loops. Y holds the chip's page ($D0 or $C0, then $D2 or $E8), A counts the register number up from 0, and X steps through zero page two bytes at a time:

```
PWR_GTIA:  sta pHPOSP0,x      ; low byte  = register number
           sty pHPOSP0+1,x    ; high byte = the chip's page
           clc
           adc #$01
           inx
           inx
           cpx #$40
           bne PWR_GTIA
```

!fig pointers|The pointer table on each machine. Choose a machine to see where each pointer leads; choose an instruction to see how it uses the table.

## Using it {#ptruse}

From then on the program almost never names a GTIA or POKEY address. It writes `STA (pCOLPF1),Y` with Y = 0 instead of `STA $D017`. ANTIC, at $D400 on both machines, is the only chip addressed directly. Counting through the listing:

|Access|Count|
|`(pointer),Y` to GTIA or POKEY|153|
|`(pointer,X)` tricks|47|
|direct GTIA or POKEY addresses|4 reads of CONSOL, all in code that runs only on the 400/800 (the 5200 has no console keys), plus the title kernel, which patches its own addresses|

The cost is time. `STA (zp),Y` takes 6 cycles where `STA abs` takes 4, and `LDA (zp),Y` takes 5 against 4. Y must be zero, so routines start with `LDY #$00` and take care to keep it there. In return the table saves space: each indirect access is 2 bytes against 3 for an absolute one, about 200 bytes over the program, against 96 bytes of zero page and a few dozen bytes of set-up code. The real gain is that one binary serves two machines without a second copy of any routine.

## The (zp,X) tricks {#ptrx}

`(zp,X)` adds X to the zero-page address *before* reading the pointer. With the pointers two bytes apart, X = 2r selects pointer r. The table therefore doubles as an array of registers:

```
DM_MISSILES:  sta (pHPOSM0,x)   ; X = 6, 4, 2, 0: HPOSM3, HPOSM2, HPOSM1, HPOSM0
              adc #$02
              dex
              dex
              bpl DM_MISSILES
```

This loop places the four missiles side by side, 2 colour clocks apart, to form the fifth-player mutant. With absolute addressing the 400/800 version could have used `STA $D004,X`; the pointer table makes the same loop work on the 5200 too.

Hogue went further and used whatever X happened to hold to reach a register from an unrelated pointer:

|Code|X|Pointer used|Register reached|
|`lda (pAUDCTL,x)`|4|$60 + 4 = $64|RANDOM (the pSKRES entry)|
|`sta (pCOLPF1,x)`|8|$3E + 8 = $46|PRIOR|
|`sta (pAUDF3+1,x)`|1|$59 + 1 = $5A|AUDC3|
|`sta (pGRACTL-$3E,x)`|$3E|$0C + $3E = $4A|GRACTL|

These save a `LDX` or a `LDY` here and there, at the price of code that only works if X has the right value. Once, it does not: see "A harmless pointer bug" in the chapter on oddities.

:::op STA (zp,X)
name: store indexed indirect
enc: 81 zz
cycles: 6
flags: none
body: Adds X to zz (wrapping within zero page), reads the 16-bit pointer from there, and stores A at that address. It is the 6502's least-used addressing mode, because few programs keep tables of pointers in zero page. Miner does, so for it this mode is an indexed register write. Note the wrap: with zz = $59 and X = 0 the pointer is read from $59/$5A, which straddles two entries of the table. That is exactly the bug in LAND_CHECK.
:::

## Reading through a write name {#ptrread}

Because GTIA's read and write registers share addresses (see "GTIA"), a pointer named for a write register is also the way to read the register at the same address. READ_HITS, which saves the collisions of one screen band, reads them like this:

```
READ_HITS:  ldy #$00
            lda (pSIZEP0),y    ; M0PL: missile 0 touched which players
            ora (pSIZEP1),y    ; M1PL
            ora (pSIZEP2),y    ; M2PL
            ora (pSIZEP3),y    ; M3PL
            sta MUT_SCORE,x
            lda (pGRAFP2),y    ; P3PL: player 3 touched which players
            sta HIT_P3-1,x
            rts
```

The game writes SIZEP0-3 only to change sprite widths (Bob's throb when he dies, the lift's double width) and never writes GRAFP2 at all, because its players are drawn by DMA. A pointer is just an address; which register it reaches depends on whether the instruction reads or writes.

# The screen {#screen}

## The display list {#dlist}

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

!fig dlist|The game screen with its display list beside it. Hover over or tap a band to see the instruction that draws it.

## Pixels {#pixels}

In ANTIC mode E each byte holds four pixels, two bits each, leftmost pixel in the top bits. A pixel value of 0 is the background; 1, 2 and 3 select the colour registers COLPF0, COLPF1 and COLPF2. Miner uses them consistently:

|Value|Register|Used for|
|0|COLBK|background (black)|
|1|COLPF0|items, text, deadly objects (waste, crusher bar, pulverizers)|
|2|COLPF1|ladders, slides, points numbers|
|3|COLPF2|girders, platforms|

!fig modee|One byte of the bitmap. Click the bits to change them and watch the four pixels change.

PLOT and its variants find the byte as `LINE_LO/HI[y] + x/4`, where the two 184-entry tables give the address of each bitmap line. They then use the pixel's position within the byte, `x AND 3`, to index two small tables:

```
PIXEL_SET:   .byte $40,$10,$04,$01     ; +0  colour 1
             .byte $80,$20,$08,$02     ; +4  colour 2
PIXEL_MASK:  .byte $C0,$30,$0C,$03     ; +8  colour 3 (the mask is also colour 3)
             .byte $00,$00,$00,$00     ; +12 background
PIXEL_CLEAR: .byte $3F,$CF,$F3,$FC
```

PIXEL_SET is indexed by `PLOT_COLOR + (x AND 3)`, where PLOT_COLOR is 0, 4 or 8 for colours 1-3 and 12 for the background. The tables overlap: colour 3's entries are PIXEL_MASK itself, and the four zero bytes after it give the background. PLOT_IF_EMPTY draws only on background pixels, which is how ladders and slides avoid painting over girders.

READ_PIXEL returns a pixel's colour and sets the Z flag if it is 3, which makes "is there a girder here?" a single subroutine call:

```
READ_PIXEL_PTR: tya              ; P/M x -> pixel x
                sec
                sbc #$30
                tay
                and #$03         ; X = position in the byte
                tax
                tya
                lsr a            ; Y = byte in the line
                lsr a
                tay
                lda (PIX_PTR),y
RP_SHIFT:       cpx #$03         ; shift the pair down to bits 1-0
                beq RP_DONE
                lsr a
                lsr a
                inx
                bne RP_SHIFT
RP_DONE:        and #$03
                cmp #$03         ; Z = colour 3?
                rts
```

:::op CMP #imm
name: compare with immediate
enc: C9 nn
cycles: 2
flags: N, Z, C
body: Subtracts nn from A without storing the result, and sets the flags as if it had. Z is set when A equals nn; C is set when A is greater than or equal to nn (as an unsigned number). READ_PIXEL ends with `AND #$03 / CMP #$03` so that its caller can write `JSR READ_PIXEL / BNE not_girder` and still have the colour in A for any other test. The listing's automatic comments turn `CMP #n / BCC label` into "if A < n goto label" for this reason: BCC (carry clear) after a compare means "less than", BCS means "greater or equal".
:::

## Text in the bitmap {#text}

The game uses two kinds of text. Fixed screens such as the title, prepare, name-entry and high-score screens use ANTIC character modes. Text inside the mine ("TNT Charge= 0 Tons", "DANGER", the credits, "Game Over") is drawn into the bitmap pixel by pixel by DRAW_CHAR. DRAW_CHAR reads the machine's ROM font, either at $E000 or at $F800 on the 5200, and can double the height. It paints 1 bits in the ink colour and clears 0 bits, so text erases whatever is behind it.

# Station colours {#colours}

## The rules {#colourrules}

Each turn, START_STATION picks the three playfield colours at random. The background stays black. The code enforces two rules:

- the three **hues** must all differ, and each must also differ from the hue that colour had on the previous turn;
- the three **luminances** are 4, 6 and 8 in some order, so each colour has a different brightness.

The second rule matters on a black-and-white television, which shows only luminance. With distinct luminances, items (colour 1), ladders (colour 2) and girders (colour 3) are still three different greys.

!fig colours|START_STATION's colour picker, ported line for line from the ROM. Roll new colours and compare the colour screen with what a black-and-white set would show.

## The code {#colourcode}

```
START_STATION: ldx #$03
               stx CNT7
SS_CLEAR:      lda COLBK_V,x      ; keep only the hues of the old colours
               and #$F0
               sta COLBK_V,x
               dex
               bne SS_CLEAR
SS_HUE:        ldy #$00           ; random hue ...
               lda (pSKRES),y     ; RANDOM
               and #$F0
               sta MOVE_A
               ldx #$03
SS_HUE_CHK:    lda COLBK_V,x      ; ... not used by another colour
               and #$F0
               cmp MOVE_A
               beq SS_HUE
               dex
               bne SS_HUE_CHK
SS_LUM:        lda (pSKRES),y     ; random luminance 4, 6 or 8 ...
               and #$06
               beq SS_LUM
               clc
               adc #$02
               sta MOVE_B
               ldx #$03
SS_LUM_CHK:    lda COLBK_V,x      ; ... not used by another colour
               and #$0F
               cmp MOVE_B
               beq SS_LUM
               dex
               bne SS_LUM_CHK
               lda MOVE_A
               ora MOVE_B
               ldy CNT7
               sta a:$008A,y      ; COLBK_V + Y
               dec CNT7
               bne SS_HUE
```

Three details are worth following through:

- **The old colours take part.** SS_CLEAR strips the luminance from the three old colours but keeps their hues. The checks compare against all three slots, so the first new colour (slot 3) must differ in hue from all three old colours, the second from the two remaining old colours and the new first one, and so on. That is where the "differs from last turn" rule comes from; it is a side effect, not a separate test.
- **The luminance check never sees old values.** SS_CLEAR left the old luminances at 0, which is never 4, 6 or 8, so only newly chosen luminances conflict. The result is always a permutation of 4, 6 and 8.
- **`AND #$06 / BEQ / ADC #$02`** turns a random byte into 2, 4 or 6 (rejecting 0), then into 4, 6 or 8. Rejection sampling keeps the three values equally likely.

:::op STA abs,Y with a zero-page address
name: store absolute, indexed by Y
enc: 99 8A 00
cycles: 5
flags: none
body: The colour variables live in zero page ($8A-$8D), but the 6502 has no "store zero page indexed by Y" mode: zero page,Y exists only for LDX and STX. So `STA $008A,Y` has to be assembled as a three-byte absolute instruction that happens to point into zero page. The listing writes it `sta a:$008A,y`, where `a:` forces ca65 to keep the absolute form so that the rebuilt ROM matches byte for byte. The same pattern appears in MU_HIT as `lda a:$00E2,y`.
:::
