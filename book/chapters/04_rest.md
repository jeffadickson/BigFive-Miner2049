# Items, scoring and time {#items}

## Items {#itemlist}

Items are small pictures stored as whole bytes (four pixels per byte) and copied straight into the bitmap. Each has a width, a height and a points value. When Bob touches one, UPDATE_ITEMS does five things:

- draws the points number over the item ("100" ... "500"; the points byte doubles as the shape number of the number picture);
- erases the rest of the item;
- adds points x 100 to the score;
- sets ITEM_GOT, which turns the mutants edible;
- plays a falling whistle.

The "BF" (Big Five) logo on station 7 is worth 1,100. On station 10 the items are bundles of TNT; their points value, 1 to 3, is also the number of tons added to the cannon's charge.

On station 5 one item is a trap. UPDATE_ITEMS treats the goblet (shape 33) specially there: touching it sets KILLED. The goblet sits just above Bob's starting place, so a jump straight up at the start of the station kills him. This was confirmed in the emulator.

!fig items|All 36 item shapes in ITEM_SHAPES, drawn from the ROM in four example colours. Shapes 1-5 and 11 are the points numbers themselves.

## Score {#score}

The score is six decimal digits, one per byte. ADD_SCORE adds a value to any digit and carries upwards. Points come from:

|Event|Points|
|claiming a section|5|
|item|100-500 (BF logo 1,100)|
|eating a mutant|80 or 90|
|bonus left at the end of a station|counted in at 100 a tick|

When the score first reaches 10,000, Bob gets an extra life. The award is detected by the ten-thousands digit becoming non-zero while XLIFE still holds its initial value. A jingle then plays: in each 16 frames, 8 frames of one note on a blue background and 8 of a higher note on black.

## The bonus timer {#bonus}

Each station starts with a bonus of BONUS_BASE + 500 per zone (at most 9,900), shown in a box on the status line. The box is the four missiles, set to double width. The bonus drops by 100 every three seconds. Below 700 the box flashes, Bob's face flickers and a tick plays faster and faster. If the bonus reaches zero before the station is clear, Bob dies.

## The end of a station {#stationend}

When the last section is claimed:

1. Bob vanishes.
2. TALLY counts the bonus into the score 100 at a time, with a click each time.
3. WIPE removes the screen from the bottom up. Each frame it overwrites the next display-list line with a JVB (jump and wait for vertical blank), so ANTIC simply stops drawing there, and a rising tone plays.
4. When the wipe reaches the top, the main loop builds the next station.

# Station machinery in detail {#machines}

## Transporters (stations 3 and 7) {#transporters}

To use a transporter, Bob stands still inside a booth and presses a digit key 1-4. The transporter runs as a five-state sequence in TRANSPORT:

1. Bob dissolves into sparkles: SPARKLE_BOB ANDs every line of his sprite with a random byte. A random buzz on voice 3 grows louder.
2. A short pause follows.
3. Bob appears at the destination booth, while sparkles linger at the old booth and his colours flash in both booths.
4. He sparkles in place at the new booth.
5. He re-forms as the buzz fades.

Afterwards the transporter is locked for five steps of 64 frames, about five seconds (128 frames each from zone 5 on, about ten seconds), and the booths are red until it recharges. They are also red, briefly, when the station starts.

## The lift (station 8) {#lift}

Standing on the lift and pressing the space bar (the # key on a 5200) hands the joystick to the lift. The stick then drives it left and right along its track and up and down. It rises at half the speed it falls: a line every 4 frames up, every 2 frames down. Bob rides along, and pressing space or the button again gives control back.

The lift is player 3 in the band that contains it. As it moves up or down, LIFT_CONTROL rewrites the top of its column of player data: it clears the line above, writes the two-line platform and one more line of the scissor pattern. The arms seem to extend and fold because the pattern's phase steps through a seven-line cycle.

## Pulverizers (station 9) {#pulverizers}

Four heads hang from a beam. Each waits, drops 22 lines, rises again and waits for a delay that shrinks with the zone. Each head's top line is a thin rod. As the head descends, that line is left behind each frame, so the rod grows down from the beam with no extra drawing code. The heads are drawn in colour 1, and touching colour 1 on this station is fatal. Station 9's moving platforms behave as lifts: the code holds each one at the end of its run until Bob stands on it.

## The cannon (station 10) {#cannon}

Bob collects TNT bundles worth 1-3 tons each, then steps into the cannon's mouth. The cannon then follows him along its track, and the button fires it:

|Charge|Result|
|1 ton|Bob reaches the first platform|
|2 tons|the second platform|
|3 tons|the third platform|
|4 tons or more|he is shot off the top of the screen and falls back upside down|

With 4 tons or more loaded, the word "DANGER" appears on the screen as a warning. After such an over-charged shot, DRAW_BOB_FLIPPED draws Bob upside down for the rest of the turn, by copying his sprite top-to-bottom instead of bottom-to-top. SHOW_TNT keeps "TNT Charge= nn Tons" up to date on the screen.

# The title-screen kernel {#kernel}

## Ten colours on a line {#tenlights}

The high-score screen surrounds the table with a frame of 36 "5" characters whose colours march round it like theatre lights. Along the top and bottom there are ten lights on one line of ANTIC mode 7 text. Mode 7 can colour a character with one of four registers, COLPF0-3, chosen by the top two bits of its code. Four registers, ten lights.

!fig titlemovie|The high-score screen, six seconds recorded frame by frame from the emulator. Every light keeps one colour from top to bottom. The rows scroll two colour clocks every five frames, and each time the scroll wraps, after 40 frames, the colours move one light along.

The ten lights are made like this:

- the left four are playfield characters using COLPF0-3;
- the middle two are players 1 and 2, with their own colour registers, holding copies of the "5" glyph;
- the right four are playfield characters using COLPF0-3 again, after the colour registers have been rewritten while the beam is in the middle of the line.

So on each of the row's 12 visible scan lines, the four playfield colour registers must hold the left lights' colours while the beam crosses the left third of the screen, and the right lights' colours by the time it reaches the right third. The program that does this is TITLE_KERNEL.

## The kernel {#kernelcode}

TITLE_KERNEL is 62 bytes, copied at start-up from the cartridge at $9630 to RAM at $0400. Assembled for $0400 it reads:

```
$0400  8D 0A D4    STA WSYNC          ; line up with the beam
$0403  E4 B1       CPX $B1            ; KERNEL_DELAY1: 3, 4 or 5 cycles (patched)
$0405  A9 cc       LDA #c0            ; KERNEL_LINE: left four lights
$0407  8D 16 D0    STA COLPF0
$040A  A9 cc       LDA #c1
$040C  8D 17 D0    STA COLPF1
$040F  A9 cc       LDA #c2
$0411  8D 18 D0    STA COLPF2
$0414  A9 cc       LDA #c3
$0416  8D 19 D0    STA COLPF3
$0419  A9 cc       LDA #c4            ; right four lights
$041B  8D 16 D0    STA COLPF0
$041E  A9 cc       LDA #c5
$0420  8D 17 D0    STA COLPF1
$0423  A9 cc       LDA #c6
$0425  8D 18 D0    STA COLPF2
$0428  A9 cc       LDA #c7
$042A  8D 19 D0    STA COLPF3
$042D  01 B1       ORA ($B1,X)        ; 6-cycle pads x 3
$042F  01 B1       ORA ($B1,X)
$0431  01 B1       ORA ($B1,X)
$0433  E4 B1       CPX $B1            ; KERNEL_DELAY2: 3, 4 or 5 cycles (patched)
$0435  CA          DEX                ; 12 lines
$0436  F0 03       BEQ $043B
$0438  4C 05 04    JMP $0405
$043B  4C 6E 96    JMP DLI_AFTER_ROW  ; back to the cartridge
```

Everything in it that changes is patched by the cartridge code:

- **Colours.** Every frame, KERNEL_COLS_TOP and KERNEL_COLS_BOTTOM write the eight `LDA #` operands from a ten-colour ring, CHASE_COLOURS, starting at the current rotation.
- **Chip addresses.** KERNEL_COLS_TOP also rewrites the high byte of each `STA COLPFn` with the GTIA page taken from the pointer table, $D0 or $C0. The kernel cannot afford the pointer table's indirect stores, so it uses absolute ones and fixes their addresses for the machine it finds itself on. That is the reason it runs from RAM: a ROM cannot be patched.
- **Delays.** SET_FINE_SCROLL writes the opcode of both delay instructions.

There is one WSYNC at the start and none inside the loop. From the first line to the twelfth, the kernel keeps step with the beam only by taking exactly as long as a scan line.

:::op ORA (zp,X) as a delay
name: OR indirect, used for its timing
enc: 01 B1
cycles: 6
flags: N, Z (A is changed, harmlessly)
body: The kernel needs 18 cycles of padding after its last colour write. A NOP is 1 byte and 2 cycles, so 18 cycles of NOPs would be 9 bytes; three `ORA ($B1,X)` do it in 6 bytes. Any 2-byte, 6-cycle instruction would do, provided it has no side effects that matter: this one only changes A, which is reloaded at the top of the loop, and reads from wherever the pointer at $B1+X leads, which is harmless on this screen.
:::

## Counting the cycles {#kernelcycles}

One pass of the loop takes:

|Part|Cycles|
|8 x (LDA # / STA abs)|8 x 6 = 48|
|3 x ORA ($B1,X)|18|
|delay|d = 3, 4 or 5|
|DEX / BEQ (not taken) / JMP|2 + 2 + 3 = 7|
|total|73 + d|

A scan line is 114 cycles, but ANTIC takes some of them. On each line of this mode 7 row it fetches one byte of character data per character (24 of them, because a horizontally scrolled line fetches the wider amount), refreshes the dynamic RAM (9 cycles) and fetches player/missile data (5 cycles). That leaves about 76 cycles for the CPU, which matches the loop with d = 3. Why then change d?

The answer came from stepping through the kernel in the emulator and reading the beam's horizontal position at the top of every pass:

|HSCROL|Delay opcode|Loop length|Beam position at the top of each pass (cycle)|Cycles ANTIC took per line|
|0|CPX zp (3)|76|110, 110, 110 ...|38|
|2|CMP zp,X (4)|77|110, 110, 110 ...|37|
|4, 6, 8|CMP zp,X (4)|77|111, 111, 111 ...|37|
|10, 12, 14|ASL zp (5)|78|111 or 112, steady|36|

At every scroll value the pass starts at the same beam position on every line, so the loop is exactly one line long, and the cycles ANTIC takes from a line change with the fine scroll: 38 at HSCROL 0, 37 at 2-8, 36 at 10-14. In the emulator's cycle-by-cycle model of ANTIC, shifting the character fetches sideways changes how many of the nine refresh cycles still fit on the line. SET_FINE_SCROLL picks the delay that makes the loop exactly as long as what ANTIC leaves:

```
SET_FINE_SCROLL: sta HSCROL
                 ldx #$E4            ; CPX zp, 3 cycles   (HSCROL 0-1)
                 lsr a
                 beq SFS_PATCH
                 ldx #$D5            ; CMP zp,X, 4 cycles (HSCROL 2-9)
                 cmp #$05
                 bcc SFS_PATCH
                 ldx #$06            ; ASL zp, 5 cycles   (HSCROL 10-15)
SFS_PATCH:       stx KERNEL_DELAY2
                 stx KERNEL_DELAY1
                 rts
```

The title code scrolls two colour clocks at a time, so only the even values 0-14 ever occur. For each of them, the delay the code chooses is the one that the emulator's cycle-by-cycle model of ANTIC says is needed. Hogue would have found these thresholds on real hardware, by trial or by working through ANTIC's fetch timing; nothing in the code says which.

A loop one cycle too long would drift two colour clocks per line, 24 colour clocks over the 12 lines, and the colour changes would cut diagonally through the lights. A check of 150 captured frames, covering six of the eight scroll phases, found every light a single colour from top to bottom.

!fig beam|The race with the beam on one scan line, drawn from the emulator trace at HSCROL 8. ANTIC's stolen cycles are marked on the line. The first four writes land before the left lights are drawn; the next four land after the left lights and before the right ones.

:::op CPX zp / CMP zp,X / ASL zp
name: three delays of different lengths
enc: E4 B1 / D5 B1 / 06 B1
cycles: 3 / 4 / 5
flags: CPX and CMP set N, Z, C; ASL changes $B1 and sets N, Z, C
body: All three are two bytes long, so any of them can be patched into the same slot without moving the code after it. Their cycle counts differ by one each, which is the step the kernel needs. CPX and CMP only read; ASL writes its result back to $B1, which is the first byte of the title's temporary storage and is not used while the kernel runs. The kernel patches only the opcode byte; the operand $B1 stays.
:::

## The rest of the screen {#hsrest}

- **The rows never move.** The top and bottom rows are single lines of mode 7 text kept in ROM. HSCROL slides each row by 0-14 colour clocks, two at a time every five frames (the title loop counts four frames, then the new phase is shown on the next one), which is up to two character cells. Each time the scroll wraps, the colours rotate one light, so the eye sees continuous motion.
- **Side columns.** Players 0 and 3, in double-line resolution, form the side columns. A display-list interrupt on every text line recolours them. They move by redrawing into a second player/missile buffer and switching PMBASE between $0400 and $1C00, which is double buffering.
- **Smaller effects.** The ten score lines get a moving rainbow from the same interrupts, "HIGH SCORES:" pulses in brightness, "START" blinks in inverse video, and a soft tone repeats.

The display list itself is in ROM ($8000). Its final JVB instruction's address bytes are also the first two characters of the bottom row of lights, so the jump target is nonsense. That is harmless, because TITLE_VBI reloads the display list pointer every frame.

# The credits and the demo {#attract}

## The credits {#credits}

After power-up the game plays station 11, a station of plain girders with no mutants, which hides the credits. The credits are drawn at the start in pixel colour 1, whose register is set to black, so they are invisible. Bob, driven by the recording DEMO_CREDITS, walks the girders. Every frame GAME_VBI looks at a one-pixel column 30 lines tall through him, starting 12 lines above his head, and repaints every colour-1 pixel there in colour 2, so the words appear behind him as he passes. When he reaches the bottom right, colour 1 is made visible, the full text appears, and a display-list interrupt (DLI_RAINBOW) runs alone, with no vertical-blank interrupt, striping the text with a scrolling rainbow while Clementine plays.

!fig creditsmovie|The opening credits, every second frame, rendered by the harness from the cartridge's own code. Bob is driven by the DEMO_CREDITS recording; the text appears where he walks, and the girders he crosses turn solid as he claims them.

## The demo recorder {#demo}

Both Bob in the credits and Bob in the station-1 demo are played from recordings in the ROM. A recording is a list of (input, frames) pairs:

|Bit|Meaning (0 = active)|
|0|stick up|
|1|stick down|
|2|stick left|
|3|stick right|
|4|button|

So $1F is "nothing", $17 is right, $1B is left, $1E up, $1D down, $0F the button alone, and $0B or $07 a jump to the left or right. The low four bits are in exactly the format of the PIA's joystick port, so a recording byte can stand in for a hardware read.

|Recording|Pairs|Frames|Length|
|DEMO_STATION1|70|2,599|43.3 s|
|DEMO_CREDITS|68|2,558|42.6 s|

Lengths over 255 frames are split into two pairs with the same input, such as `$17,$FF,$17,$21` (right for 255 frames, then right for 33).

Playback costs almost nothing. DEMO_PTR points at the current pair; its high byte doubles as the flag "a recording is playing", because no recording lives in page 0. READ_STICK and READ_BUTTON test that byte first and, if it is set, take their bits from `(DEMO_PTR),Y` instead of the hardware:

```
READ_BUTTON:  lda DEMO_PTR+1      ; demo?
              bne RB_DEMO
              sty SAVE_Y2
              ldy #$00
              lda (pTRIG0),y      ; the real button
              ldy SAVE_Y2
              rts
RB_DEMO:      jsr DEMO_INPUT      ; the current recorded byte
              and #$10            ; bit 4 = button
              lsr a
              lsr a
              lsr a
              lsr a
              rts
```

At the end of every frame VBI_TAIL counts DEMO_CNT down and, when it reaches zero, moves DEMO_PTR on two bytes and loads the next count. The rest of the game cannot tell a recording from a player: Bob's movement, the mutants, the collisions and the claiming all run exactly as in a real game. The game is deterministic apart from POKEY's RANDOM, which on station 1 affects only the colours and the points for an eaten mutant, so the same recording always produces the same walk.

!fig demo|The station-1 demo with its recording. The strip under the screen is DEMO_STATION1, one block per pair, coloured by input; the marker follows the playback. Click the strip to jump.

The run lengths have the irregular values (81, 11, 6, 9, 29 ...) of a hand on a joystick rather than a hand-written script, which suggests the recordings were captured from real play. Nothing in the cartridge records; the capture routine, if there was one, stayed on the development system.

## Other screens {#others}

!fig screens|The prepare screen (the background flashes and a siren plays while the station is drawn behind it), "Game Over" (cut into a box that fills column by column), and name entry (the missiles form the cursor; the background is a rainbow from a DLI).

## The phone-number cheat {#cheat}

During a game, typing Big Five's telephone number, 213-782-6861, then SHIFT plus a digit, warps to that station (0 means station 10). PHONE_CODE compares each digit typed with the bytes of the number as printed at the end of the credits text, "(213) 782-6861", skipping the bracket, the space and the dash. The printed text and the cheat code are the same bytes. A wrong digit starts the count again, and a held key repeating the same digit is ignored. On the 5200, the lower fire button plays the part of SHIFT.

# Sound and music {#sound}

POKEY's four voices are used for different effects:

|Voice|Used for|
|1|game-over tune melody, siren on the prepare screen, death noise, time-running-out tick, title tone|
|2|game-over tune harmony, mutant being eaten, name-entry clicks|
|3|footsteps, jumps, falls, slides, transporter buzz, lift motor, cannon|
|4|item whistle, extra-life jingle, bonus tally clicks, screen-wipe tone|

GAME_OVER_TUNE plays "Oh My Darling, Clementine" three times: on voice 1, then on voice 2, then on both together. The tune table holds the melody as POKEY dividers ($28 C, $35 the G below, $1F E, $1A G, $1D F, $23 D, $2A B) with lengths in frames. Voice 2 does not read the table; its note is calculated from the melody note as (note - $1D) x 4 + $79, which places it roughly two octaves lower, and a single special case covers note $1A. Each note starts at full volume with a pure tone and decays one step per frame, which sounds like a plucked instrument. START, the button or a digit key cuts the tune short.

The footsteps are a 14-frame pattern on voice 3: a low thud, silence, a click, silence.

# Tricks lost to time {#tricks}

Many of the techniques in this program were common knowledge among Atari programmers in 1982 and are now mostly forgotten:

- **A pointer table instead of fixed addresses** lets one binary drive chips at different addresses on two machines.
- **A diagnostic cartridge** owns the machine from the first instruction.
- **Self-modifying code for timing:** delay opcodes chosen for their cycle counts and patched into a scan-line loop to match what ANTIC leaves at each fine-scroll value.
- **Self-modifying code for portability:** the high bytes of absolute stores patched with the chip's page at run time.
- **Mid-line colour changes** go beyond the hardware's colours-per-line limit.
- **Sprite multiplexing** with display-list interrupts, and collision registers read per band.
- **Fifth-player mode,** which turns the four missiles into one more sprite.
- **Double-buffered player graphics** by flipping PMBASE.
- **The screen as the database:** the girders' claimed or unclaimed state lives only in the bitmap.
- **Input recordings played through the input routines,** so the demo and the credits are the real game.
- **A display list rewritten on the fly** to wipe the screen line by line.
- **Hidden text revealed by recolouring pixels** whose colour register is set to black.
- **Harmony calculated from the melody** instead of stored.
- **Tables that overlap their neighbours** to save bytes.
- **Analog joystick input converted to digital directions,** so one input routine serves both machines.

# Oddities and bugs {#oddities}

**A harmless pointer bug.** When Bob lands safely from a jump or fall, LAND_CHECK means to write 0 (silence) to AUDC3 with the same `STA (pAUDF3+1,X)` that START_DEATH, a few lines earlier, uses to start its death tone. START_DEATH has X = 1 at that point, which makes the pointer pAUDC3. LAND_CHECK has X = 0, so the 6502 forms an address from bytes $59 and $5A: the high byte of the AUDF3 pointer and the low byte of the AUDC3 pointer. The result is $05D2 ($05E8 on the 5200): row $D2 of player 1, which belongs to Bob's sprite only when he is at that height, and is redrawn whenever he is (on the 5200, row $E8 is below the visible screen). Voice 3 is left as it was and is set again by the footstep code a frame later, so nobody would ever notice.

**A loop that could run forever.** CLAIM_AT's search for a section's left edge scans right along a gap row until it meets girder. At a spot with no girder anywhere to the right on that row, the scan would never end. Bob's feet never stand on such a spot, so it never happens.

**Filler that does nothing.** BUILD_STATION and SETUP_ITEMS contain short sequences with no effect, such as `LDA #$4C / LDA $A546`. $4C is the JMP opcode, so these may be places kept free for a patch. COLD_START has three NOPs, and UPDATE_ITEMS starts with a sequence that compares a ROM byte with itself minus 5 and ignores the result, padded with NOPs. That looks like a check that was patched out. The evidence for either reading is only the shape of the code.

**Tables read past their ends.** The bonus for station 10 is read from one byte past the end of BONUS_BASE, which is the first byte of the next table. Station 11 reads its starting x and its transporter column from one past the end of their tables in the same way, and the jump reads two entries past the end of JUMP_ARC. The values happen to be the ones wanted.

**The poisoned goblet.** Station 5's goblet kills Bob on contact. It is a deliberate test in the code, not a side effect; whether it was meant as a trap or as a protection against something is not clear.

**The credits station's mutant pointer.** MUTANT_LISTS has an entry for station 11 that points into RAM ($1E18), because that word is really the first two bytes of the mutant shapes. The 88 bytes it points to are read, but through a mask of zero, so the credits get no mutants.

**The edible off-by-one.** The edible time is one frame shorter than the constant suggests, because the subtraction runs with the carry clear (see "Behaviour").
