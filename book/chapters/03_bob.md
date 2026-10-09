# Building a station {#building}

A station is described entirely by data. STATION_TABLE gives the address of four lists for each station, and four more tables give the items, the mutants, Bob's starting position and the transporter column:

|List|Entry|Meaning|
|girders|sections, x, y|three sub-lists: sloping down, sloping up, flat|
|ladders|height, x, y, style|8 pixels wide, a rung every 4 lines|
|slides|rows, x, y, step|an 8-pixel band shifted "step" pixels per line|
|moving platforms|timer, width, x, y, travel, speed|a 3-line bar that moves back and forth|
|items|shape+$80, y, x|a picture copied byte by byte into the bitmap|
|mutants|8 records of 11 bytes|start position, patrol, speed, colour timing|

## Girders and sections {#girders}

The unit of the game is the girder *section*, 4 pixels wide. DRAW_GIRDERS draws each section as three thin stripes of colour 3, two lines apart, and counts it into SECTIONS. On sloping girders each section is one line higher or lower than the one before. On flat girders, sections alternate between two stripe patterns, which gives them a brickwork look. That alternation turns out to be essential to how claiming works (see "Claiming the floor").

## Station machinery {#machinery}

Station-specific set-up code adds the rest:

- **Stations 3 and 7: transporters.** DRAW_TRANSPORTER draws the column of four booths from an 8-bit run-length pattern (BOOTH_SHAPE), each bit two pixels wide, and writes the digits 1-4 in them with the font renderer.
- **Station 6: the waste tank.** DRAW_WASTE draws a solid colour-1 box and cuts "DANGER / Radioactive / Waste" into it in the background colour.
- **Station 8: the lift.** The lift's platform, scissor arms and cart are drawn into player 3, and its track into the bitmap.
- **Station 9: the pulverizers.** SETUP_PULVERIZERS draws the beam and posts and gives the four heads random starting delays.
- **Station 10: the cannon.** The cannon goes into player 3 plus the missiles. The TNT store is drawn with its shelves and sign.

!fig machines|The machinery as it appears on screen, cut from emulator frames and enlarged.

## Overlapping data {#overlap}

The data area is full of sharing:

- A list's 0 terminator is often the first byte of the next list.
- Station 1's item list ends with the 0 that also serves as "no ladders, no slides, no platforms" for every station that lacks them.
- Entry 0 of STATION_TABLE is also ITEM_SHAPES 33-36, the goblet and the three TNT bundles.
- Station 10's eighth mutant record runs ten bytes into station 1's girder list. That is harmless, because the record's first byte, 0, means "no mutant".
- Several girder lists start inside the slide list before them.
- JUMP_ARC is 30 bytes long but is read for 32 entries; the last two come from the next table, BOB_SIZE, whose first two bytes are zero. They give Bob two more frames of hang time.

Because the generated listing follows the ROM byte by byte, these overlaps show up as labels that sit in the middle of what looks like another table.

# Bounty Bob {#bob}

## Three players, four colours {#bobsprite}

Bob is drawn with players 0, 1 and 2 laid over each other at the same horizontal position: blue ($8A) for his coat, orange ($3A) for his face and hands, white ($0F) for his legs and the stripe down his front. START_STATION sets PRIOR to $31:

|PRIOR bit|Value|Effect|
|0|1|players 0-3 in front of the playfield|
|4|$10|fifth player: the four missiles take COLPF3's colour (used by the mutants)|
|5|$20|multicolour players: where players 0 and 1 overlap, GTIA ORs their colours|

Where players 0 and 1 overlap, $8A OR $3A = $BA, a green, so his hat comes out a fourth colour for free. Player 2 shows only where the other two are empty.

!fig bob|Bob's three players taken apart and combined, drawn from the ROM's frame data, with the walk cycle animated at the game's speed (one pixel and one frame every other frame).

Each animation frame stores the three layers back to back, 20, 17 and 17 lines, with each layer's first line shared with the previous layer's last: 52 bytes, stored 51 bytes apart, so a frame's last byte is also the next frame's first. DRAW_BOB copies them into player memory from the bottom up, and the blank lines at the ends erase his previous position as he moves.

## The movement state machine {#states}

MOVE_BOB runs once per frame from GAME_VBI. It tests Bob's state variables in a fixed order and jumps to the routine for the first one that applies; that routine handles the frame and returns.

!fig statemachine|MOVE_BOB's states and the conditions that move Bob between them, as they appear in the code. Tests are made in the order shown on the left.

|Order|Test|State|Routine|
|1|SPECIAL = 1|melting|MELT_BOB|
|2|SPECIAL = 2|dead|none (GAME_VBI ends the turn)|
|3|SPECIAL = 3-7|in the transporter|TRANSPORT|
|4|BOB_FALL ≠ 0|falling|FALLING|
|5|SLIDE_LEN ≠ 0|sliding|SLIDING|
|6|BOB_X, BOB_Y = top of a slide|start a slide|(inline)|
|7|BOB_FRAME ≥ 11|jumping|JUMPING|
|8|BOB_FRAME 7-10|on a ladder|ON_LADDER|
|9|otherwise|on a girder|button, then stick|

On a girder, the inputs are also tested in a fixed order. The button comes first, and only a fresh press counts: JUMP_LOCK is set to 6 while the button is held and must have run down to 0 before another jump. Then the stick: up, down, left, right, in that order, so a diagonal is read as its vertical part. Up and down start a climb only if there is a ladder; otherwise the stick falls through to walking.

**Walking** moves Bob one pixel every other frame and cycles through three frames. After each step, the routine tests the bitmap under his feet with READ_PIXEL:

- girder one line above his feet: the girder rises, so he steps up a line;
- girder under his feet: nothing to do;
- girder one line below: the girder falls, so he steps down a line;
- no girder at all: he has walked off the edge and starts to fall.

Bob follows sloping girders this way with no slope data at all: the bitmap is the collision map.

**Ladders.** TRY_CLIMB_UP walks the ladder list and accepts a ladder whose foot (y + height) is level with Bob's feet or one line below them, and whose x is within two pixels of his. It then snaps him onto the ladder's x and starts the climb. MOVE_A and MOVE_B count the lines to the top and to the bottom; reaching either end puts him back on his feet. Frames 9 and 10 show him stepping on or off at the top.

```
TCU_ENTRY:  iny                 ; bottom of the ladder = y + height
            iny
            clc
            adc (LADDERS),y
            sec                 ; - feet line (BOB_Y + $15)
            sbc BOB_Y
            sec
            sbc #$15
            cmp #$02            ; 0 or 1 line?
            bcs TCU_NEXT
```

:::op SBC
name: subtract with carry
enc: E9 nn (immediate), E5 zz (zero page) ...
cycles: 2 (immediate), 3 (zero page)
flags: N, V, Z, C
body: Computes A - operand - (1 - C). There is no plain subtract on the 6502: you set the carry first with SEC (2 cycles) to mean "no borrow". After SBC, C is set if no borrow was needed, so `SEC / SBC #n / CMP #2 / BCS` is "if the unsigned difference is 2 or more". TRY_CLIMB_UP relies on the wrap-around: if the ladder's foot is *above* Bob's feet the difference is negative, which as an unsigned byte is 255 or so, and the same `CMP #$02 / BCS` rejects it. One unsigned compare covers both "too far below" and "above".
:::

## The jump {#jump}

START_JUMP takes the direction from the stick (-1, 0 or +1), sets frame 11 or 12 depending on the way Bob faces, and clears MOVE_A, the position in the jump table. Then JUMPING runs every frame:

- every other frame, it moves Bob MOVE_B pixels sideways, unless CHECK_LEFT or CHECK_RIGHT finds a wall;
- every frame, it adds JUMP_ARC[MOVE_A] to BOB_Y. Past entry 31 it adds 1, so he keeps falling until he lands.

!fig jump|Bob's jump, frame by frame, from JUMP_ARC. The curve shows the height; the sprite follows it. Entries 30 and 31 are read from the next table, BOB_SIZE.

The table goes up 11 lines, hangs for 2 frames, rises 3 more, hangs again, rises 2, hangs 3 frames at the top (16 lines up), then comes down slowly before the free fall takes over. The sound follows the arc: the pitch of voice 3 rises while Bob climbs (AUDF3 decreasing by 3 a frame) and falls as he comes down.

From entry 21 on, each frame also calls LAND_CHECK, which counts FALL_LEN and looks for a girder under his feet. Forty frames of LAND_CHECK are fatal. Walking off a ledge, that is a fall of 40 lines. In a jump the count starts near the top of the arc, so landing 18 lines below the take-off point is safe and 19 lines kills him.

:::op ADC with a negative table
name: add with carry
enc: 6D lo hi (absolute)
cycles: 4
flags: N, V, Z, C
body: A + operand + C. JUMP_ARC stores its steps as signed bytes: $FF is -1, $01 is +1. Adding $FF to BOB_Y with the carry clear gives BOB_Y - 1 (plus a carry out that is ignored), so the same `CLC / ADC table,X` moves Bob up or down. Two's complement means the 6502 needs no separate signed add.
:::

**Falling** is one line down per frame with a falling whistle. When LAND_CHECK finds a girder, it also makes sure Bob's feet end up on the top stripe and not inside the girder, lifting him a line if needed.

**Slides.** If Bob stands exactly at the top of a slide, he rides it: one line down and "step" pixels sideways per frame, using the jump frames 11 and 12, with a falling whistle (AUDF3 rising by one every other frame).

## Dying {#dying}

When a mutant, a hazard or the timer kills Bob, START_DEATH sets SPECIAL = 1 and two things run at once:

- **The throb.** GAME_VBI counts DYING down 4, 3, 2, 1 every four frames and uses it to index BOB_SIZE and BOB_SIZE_X: the players switch between normal, double and quadruple width, with an x offset (0, -4, -8, -4) that keeps Bob centred.
- **The melt.** MELT_BOB feeds a random byte in at his feet in each of the three players and shifts the column above it down one line. MOVE_B, the top of the shifted part, moves down a line each frame. When it reaches BOB_Y + $11, around his shins, he is a puddle of noise and SPECIAL becomes 2.

!fig melt|MELT_BOB on Bob's standing frame. Each frame a byte from POKEY's RANDOM enters at the feet line and the column above shifts down; the shifted region shrinks from the top. Press "Melt again" for a different random sequence.

```
MELT_COLUMN: stx SPR_PTR          ; SPR_PTR = player page, row $1F
             ldx #$00
             sty SPR_PTR+1
             ldy TMP9B            ; feet line
             lda (pSKRES,x)       ; RANDOM
             sta (SPR_PTR),y
MELT_SHIFT:  dey                  ; row above ...
             dey
             lda (SPR_PTR),y
             iny                  ; ... copied one row down
             sta (SPR_PTR),y
             cpy MOVE_B
             bne MELT_SHIFT
             rts
```

If he dies in the air, the melt waits until he lands.

# Claiming the floor {#claiming}

## The idea {#claimidea}

CLAIM_FLOOR is the heart of the game. Bob must walk over every section of every girder, and the game must know which sections he has walked on. There is no table of sections anywhere in the program. The bitmap is the table.

An unclaimed section is drawn as three thin stripes with gaps between them. Claiming it fills the gaps, so the section turns solid. Whether a section is claimed is therefore visible to the code the same way it is visible to the player: look at the pixels.

!fig claim|Station 1's real bitmap, with the claiming routine ported from the ROM (and checked against it at 1,322 positions). Click a girder to put Bob's foot there and claim the section under it. The panel shows the gap rows and the bytes before and after.

## Step by step {#claimsteps}

CLAIM_FLOOR runs every frame while Bob walks or stands on a girder (not on the bottom floor, not while starting, dying, falling, sliding or in the transporter). FEET_OFFSETS gives the x of his two feet for the current animation frame, and CLAIM_AT runs once per foot:

1. **Is there girder under the foot?** READ_PIXEL at the feet line must return colour 3. If not, nothing happens.
2. **Is it unclaimed, and which pattern?** It reads the next line down. If that line is background, the gaps are at +1, +3 and +5 (three gap rows). If it is girder, it reads the line after: background means gaps at +2 and +4 (two gap rows); girder means both lines are solid, the section is already claimed, and nothing happens.
3. **Score it.** SECTIONS goes down by one and ADD_SCORE adds 5.
4. **Find the section's left edge.** Along the first gap row it looks at the pixel left of the foot. If that is girder, the foot was on the section's first pixel. Otherwise it steps left up to 3 more pixels looking for girder. If it finds none, the section must start further right: it steps 4 right and scans right until it finds girder, then backs up 5. Either way, the first gap pixel is one to the right of where it stopped.
5. **Fill.** It plots 4 pixels of colour 3 in each gap row, two lines apart.

The left-edge search works because neighbouring sections never have their gaps on the same lines. On a slope, the next section is a line higher or lower. On a flat girder, sections alternate between the two stripe patterns, the brickwork. In a gap row, a neighbour shows up as girder.

## What it saves {#claimsaves}

The design costs nothing in memory: no flags, no counters per section, nothing to initialise when a station is drawn beyond the single SECTIONS count. It also makes the drawing and the game logic impossible to get out of step, since there is only one copy of the truth. The price is time, since every check is a call to READ_PIXEL, which computes a line address and shifts bits, but Bob only moves a pixel every other frame.

There is one sharp edge. If the code were ever asked to claim at a spot where the gap row has no girder pixel anywhere to its right, the rightward scan would never end: the X position wraps around and the line is read again forever. Bob's feet cannot reach such a spot in play, so this never happens; it turned up only when the harness put Bob's feet at random places, including the middle of a girder's stripe.

:::op LSR A
name: logical shift right, accumulator
enc: 4A
cycles: 2
flags: N (always 0), Z, C (gets bit 0)
body: Shifts A one bit right; bit 0 goes into the carry. Two LSRs divide by 4, which turns a pixel column into the byte within the line (four pixels per byte). READ_PIXEL also uses LSR pairs to move a pixel's two bits down to the bottom. MOVE_BOB uses LSR the other way round: it shifts the joystick byte right one bit at a time and tests the carry with BCC/BCS, reading the four direction bits in turn without any masks.
:::

# Mutants {#mutants}

## The problem {#mutproblem}

A station has up to eight mutants. The hardware has four players and four missiles, and Bob has already taken three players. What is left is player 3 and the missiles: two sprites for eight monsters.

The answer is that a sprite's horizontal position, width and colour are registers, read by GTIA afresh on every scan line, while its shape is a full-height strip of memory. Put eight shapes at eight different heights in the strip, and change the horizontal position between them, and one sprite becomes several.

## Four bands {#bands}

The game's display list has four DLIs: at the end of the status line, and after bitmap lines 46, 93 and 140. They divide the mine into four bands of about 47 lines, and the stations are designed so that each band contains at most two mutants and no mutant crosses a band boundary.

!fig bands|One frame of the game screen, played back slowly. As the beam passes each display-list interrupt, DLI_MUTANTS moves player 3 and the missiles to the next band's two mutants. The strips on the right show the same player memory throughout: all eight shapes are there at once; only the horizontal position changes.

In each band:

- **player 3** draws one mutant, with its colour in COLPM3;
- **the four missiles** draw the other. Each missile is 2 pixels wide. DLI_MUTANTS places them side by side, 2 colour clocks apart, and PRIOR's fifth-player bit gives all four the colour COLPF3. Together they make one 8-pixel sprite.

!fig fifth|The fifth player. A missile byte holds two bits for each of the four missiles. Placed side by side, they read left to right as an ordinary 8-pixel row, so the same mutant shapes work in either sprite.

## What each DLI does {#dlijob}

```
DLI_MUTANTS:  pha                   ; save A, X, Y
              txa
              pha
              tya
              pha
              lda DLI_BAND          ; first DLI of the frame?
              cmp #$04
              beq DM_HITCLR
              lda #$04              ; band just finished: 1-3
              sec
              sbc DLI_BAND
              tax
              jsr READ_HITS         ; save its collisions
DM_HITCLR:    ldy #$00
              sta (pHITCLR),y       ; clear the collision registers
              ...                   ; band effects (booths, lift, cannon, glow)
DM_POSITION:  ldx MUT_IDX           ; this band's missile mutant
              lda MUT_TAB+11,x
              beq DM_PLAYER3
              ldx #$06
              clc
DM_MISSILES:  sta (pHPOSM0,x)       ; HPOSM3 = x, M2 = x+2, M1 = x+4, M0 = x+6
              adc #$02
              dex
              dex
              bpl DM_MISSILES
              ...
DM_PLAYER3:   lda MUT_TAB,x         ; this band's player-3 mutant
              beq DM_LOGIC
              sta (pHPOSP3),y
              lda MUT_TAB+3,x
              sta (pCOLPM3),y
DM_LOGIC:     ...                   ; move and animate two mutants
```

1. **Collisions for the band that just ended.** GTIA's collision bits accumulate until HITCLR is written. Saving them at each band boundary and then clearing them gives a separate record for each band. READ_HITS ORs M0PL-M3PL together (any missile touching a player) and keeps P3PL (player 3 touching a player). Bob is players 0-2, so bits 0-2 in either value mean "this band's missile mutant, or player-3 mutant, touched Bob".
2. **Position the two sprites for the band below.** Missiles first, then player 3, each with its colour.
3. **Band effects.** The same interrupt colours the transporter booths (green, or red while recharging), places the lift (station 8, band 3) or the cannon (station 10, bottom band), which borrow the same sprites in their bands, and makes colour 1 flicker in the bottom band on stations 5, 6, 8 and 9, which is what makes the radioactive waste glow.
4. **Move and animate two mutants.** The rest of the handler is the mutants' game logic: patrol steps, turning round, the shimmer, the edible countdown, being eaten. Two of the eight records are updated per DLI, so all eight are updated once per frame.

The collisions for the bottom band are saved at the start of GAME_VBI, which is the next thing to run after the bottom band is drawn.

## Timing {#dlitiming}

Running in the 6502 harness, DLI_MUTANTS took between 256 and 1,290 cycles per call across five stations (about 260 to 640 on average, depending on the band), and GAME_VBI from about 3,030 cycles on station 1 to as many as 5,800 on station 5. A band of mode E lines leaves the CPU roughly 60 of each line's 114 cycles, so even the longest DLI uses only about 22 of its band's 47 lines. That leaves the main loop plenty of time. The order inside the handler matters more: the DLI fires at the end of the boundary line, and the sprite positions must be written before the beam reaches the band's first mutant a few lines further down. So the collision save and the positioning come first, and the slow mutant logic last, while the band is already being drawn.

A mutant's shape is never redrawn because of the multiplexing. Each mutant has its own rows in the player or missile strip, so its shape is only rewritten when it animates or moves vertically. The sharing costs only register writes.

:::op PHA / TXA / PHA / TYA / PHA
name: save registers on the stack
enc: 48 8A 48 98 48
cycles: 3 + 2 + 3 + 2 + 3 = 13
flags: TXA and TYA set N, Z
body: An NMI saves only the program counter and the status register. A handler that uses A, X and Y must save them itself, and the 6502 can push only A, so X and Y go through A. NMI_EXIT, the common tail of every handler in the game, does the reverse (`PLA / TAY / PLA / TAX / PLA / RTI`). On the 400/800 the OS has already saved the registers before calling the VBI, but not before a DLI; on the 5200 the BIOS saves nothing. Miner's DLIs save their own, and its 5200 VBI stub saves them too, so all handlers can end the same way.
:::

## Behaviour {#mutbehaviour}

Each mutant patrols back and forth along a girder. Its station record gives:

- its height and starting position;
- the length of its patrol and its speed (frames per step);
- the timing of its shimmer (its brightness pulses up and down by 2).

The step delay is the record's value + 1 - zone, at least 1, so mutants get faster as the game goes on.

!fig mutants|The ten mutant shapes, drawn from MUTANT_SHAPES, with their walking animation. The edible pair raise their arms; an eaten mutant becomes the number of points it was worth.

When Bob picks up an item, ITEM_GOT is set, and on the next frame GAME_VBI turns every living mutant edible. Each turns green ($C6) with an edible counter of $AF - 16 x min(zone, 9): 159 in zone 1, falling to 31 from zone 9 (the subtraction runs with the carry clear, so it is one less than $B0 - 16n). It stays green for that many frames, then blinks: purple for 5 frames, green again for half the previous time, and so on until the counter reaches zero. The blinking speeds up as a warning. In zone 1 a mutant stays edible for about six seconds; from zone 9 on, about one and a half.

Touching an edible mutant eats it for 80 or 90 points, chosen at random, and the mutant shows the number, flashing in random colours, while a rising tone plays for about two seconds. Touching a mutant that is not edible kills Bob.

:::op SBC without SEC
name: the edible-time off-by-one
enc: E5 zz
cycles: 3
flags: N, V, Z, C
body: GV_EDIBLE_TIME computes `$B0 - 16 x min(zone, 9)` with `LDA #$B0 / SBC ITEM_GOT`, but the compare and the four ASLs before it leave the carry clear, and nothing sets it. On the 6502 a clear carry means "borrow one", so the result is one less than intended: 159 frames instead of 160 in zone 1. Nobody could ever see the difference, but it is the kind of slip that only shows up in a disassembly.
:::
