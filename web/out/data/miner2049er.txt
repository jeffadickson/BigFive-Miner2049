; ============================================================================
;  MINER 2049er  -  Big Five Software, 1982.  Designed and programmed by Bill Hogue.
;
;  Commented disassembly of the 16K cartridge ROM ($8000-$BFFF).
;  Assembles with ca65 (cc65 suite) to a byte-identical image:
;      ca65 miner2049er.asm -o miner.o
;      ld65 -C cart.cfg -o miner.rom miner.o
;  with cart.cfg:
;      MEMORY   { ROM: start=$8000, size=$4000, fill=yes, fillval=$FF, file=%O; }
;      SEGMENTS { CODE: load=ROM, type=ro; }
;
;  The same ROM image runs on the Atari 400/800 and on the Atari 5200: see COLD_START.
;  All names and comments are reconstructions from reading the code; nothing of the
;  original source survives. Addresses in comments are hexadecimal.
;
;  Memory map
;    $0000-$00FF  zero page: hardware pointer table ($10-$6F), game variables ($70-$FF)
;    $0200-$0223  interrupt vectors (both machines' layouts are written)
;    $0300-$07FF  player/missile graphics (single-line; PMBASE 3 = effectively 0)
;                 $0300 missiles (mutants), $0400-$06FF Bob (players 0-2), $0700 mutants
;    $0400-$043D  (on the high-score screen) the RAM copy of TITLE_KERNEL
;    $0800-$08C7  high-score table, $08C8 text for the title screens
;    $0917-$0991  text and display list for the prepare/name screens
;    $0992-$09BF  items of the current station, $09C0-$0A17 mutant records
;    $0A19-$0A24  pulverizers (station 9)
;    $1C00-$1FFF  second P/M buffer for the high-score screen; 5200 font copy
;    $2000-$20D7  game display list; $20D8 status line (40 characters)
;    $2100-$3DBF  the playfield: 184 lines x 160 pixels, 4 colours (ANTIC mode E)
;    $3DC0-$3F2F  bitmap line address tables (LINE_LO/LINE_HI = $3DB8/$3E70, indexed from
;                 y = 8); $3F30 moving platforms
;    $8000-$BFFF  this cartridge
;
;  Coordinates: horizontal positions use the P/M coordinate system (the playfield's left
;  edge is 48 = $30); bitmap routines subtract $30 to get the pixel column (0-159).
;  Vertical positions are bitmap lines 8-191 (line y is on scan line y + 32,
;  which is also P/M row y + 32); Bob's BOB_Y is the top of
;  his sprite and his feet are at BOB_Y + $15.
;
;  Data overlaps: to save ROM, many tables share bytes with their neighbours - the end of
;  one list is the start of the next, a display list's jump address is also the first
;  two characters of a text row, the cart's wheels are a bonus value, and so on. These
;  are pointed out where they occur.
; ============================================================================

        .setcpu "6502"

LASTCHAR        = $02                   ; name entry: letter chosen with the 5200 stick / game: last cheat digit
                                        ;   typed
NAME_RPT        = $03                   ; 5200 name entry: stick auto-repeat counter
NAME_DLY        = $04                   ; 5200 name entry: keypad debounce timer
START_ZONE      = $05                   ; zone picked with the number keys on the title screens (1-10)
WARMST          = $08                   ; OS warm-start flag: non-zero after RESET, so high scores survive RESET
pHPOSP0         = $10                   ; -> GTIA HPOSP0 (write) / M0PF (read)
pHPOSP1         = $12                   ; -> HPOSP1 / M1PF
pHPOSP2         = $14                   ; -> HPOSP2 / M2PF
pHPOSP3         = $16                   ; -> HPOSP3 / M3PF
pHPOSM0         = $18                   ; -> HPOSM0 / P0PF
pHPOSM1         = $1A                   ; -> HPOSM1 / P1PF
pHPOSM2         = $1C                   ; -> HPOSM2 / P2PF
pHPOSM3         = $1E                   ; -> HPOSM3 / P3PF
pSIZEP0         = $20                   ; -> SIZEP0 / M0PL
pSIZEP1         = $22                   ; -> SIZEP1 / M1PL
pSIZEP2         = $24                   ; -> SIZEP2 / M2PL
pSIZEP3         = $26                   ; -> SIZEP3 / M3PL
pSIZEM          = $28                   ; -> SIZEM / P0PL
pGRAFP0         = $2A                   ; -> GRAFP0 / P1PL
pGRAFP1         = $2C                   ; -> GRAFP1 / P2PL
pGRAFP2         = $2E                   ; -> GRAFP2 / P3PL
pTRIG0          = $30                   ; -> GRAFP3 / TRIG0 (joystick button, 0 = pressed)
pGRAFM          = $32                   ; -> GRAFM / TRIG1
pCOLPM0         = $34                   ; -> COLPM0 (player 0 colour)
pCOLPM1         = $36                   ; -> COLPM1
pCOLPM2         = $38                   ; -> COLPM2
pCOLPM3         = $3A                   ; -> COLPM3
pCOLPF0         = $3C                   ; -> COLPF0 (playfield colour 0)
pCOLPF1         = $3E                   ; -> COLPF1
pCOLPF2         = $40                   ; -> COLPF2
pCOLPF3         = $42                   ; -> COLPF3 (also the colour of the missiles in fifth-player mode)
pCOLBK          = $44                   ; -> COLBK (background)
pPRIOR          = $46                   ; -> PRIOR
pVDELAY         = $48                   ; -> VDELAY
pGRACTL         = $4A                   ; -> GRACTL
pHITCLR         = $4C                   ; -> HITCLR
pCONSOL         = $4E                   ; -> CONSOL
pAUDF1          = $50                   ; -> POKEY AUDF1 (write) / POT0 (read)
pAUDC1          = $52                   ; -> AUDC1 / POT1
pAUDF2          = $54                   ; -> AUDF2 / POT2
pAUDC2          = $56                   ; -> AUDC2 / POT3
pAUDF3          = $58                   ; -> AUDF3 / POT4
pAUDC3          = $5A                   ; -> AUDC3 / POT5
pAUDF4          = $5C                   ; -> AUDF4 / POT6
pAUDC4          = $5E                   ; -> AUDC4 / POT7
pAUDCTL         = $60                   ; -> AUDCTL / ALLPOT
pSTIMER         = $62                   ; -> STIMER / KBCODE
pSKRES          = $64                   ; -> SKRES / RANDOM
pPOTGO          = $66                   ; -> POTGO
pPOKEY_C        = $68                   ; -> (unused POKEY register $0C)
pSEROUT         = $6A                   ; -> SEROUT / SERIN
pIRQEN          = $6C                   ; -> IRQEN / IRQST
pSKCTL          = $6E                   ; -> SKCTL / SKSTAT
TXT_DST         = $70                   ; (2) bitmap line address for the pixel being drawn
TXT_FONT        = $72                   ; (2) address of the font page holding the character
TXT_COLOR       = $74                   ; colour of the "ink": 0 = colour 1, 4 = colour 2, 8 = colour 3, 12 =
                                        ;   background
TXT_X           = $75                   ; x position (P/M horizontal coordinates: 48 = left edge of the playfield)
TXT_Y           = $76                   ; y position (scan line, 8-191)
TXT_BITS        = $77                   ; bits left in the current font byte
TXT_ROWS        = $78                   ; font rows left in the current character
TXT_VSCALE      = $79                   ; vertical magnification (1 or 2 scan lines per font row)
TXT_ROW         = $7A                   ; offset of the current font byte within the font page
TXT_LEN         = $7B                   ; characters left to draw
TXT_IDX         = $7C                   ; index of the next character in TEXT_POOL
PAUSE_DLY       = $7D                   ; ESC-key debounce for pause
SAVE_Y          = $7F                   ; scratch save of Y
PTR             = $80                   ; (2) general pointer
CNT0            = $82                   ; scratch counter
CNT1            = $83                   ; scratch counter / index
PLOT_COLOR      = $84                   ; colour for PLOT: 0 = colour 1 (COLPF0), 4 = colour 2 (COLPF1), 8 = colour
                                        ;   3 (COLPF2), 12 = background
PLOT_X          = $85                   ; x for PLOT (P/M coordinates or raw pixel, depending on routine)
PLOT_Y          = $86                   ; y for PLOT (scan line)
CNT2            = $87                   ; scratch counter
CNT3            = $88                   ; scratch counter
CNT4            = $89                   ; scratch counter / slope
COLBK_V         = $8A                   ; background colour (0 = black; flashes blue during the extra-life jingle)
COLPF0_V        = $8B                   ; station colour for pixel colour 1 (COLPF0): items, text
COLPF1_V        = $8C                   ; station colour for pixel colour 2 (COLPF1): ladders, slides
COLPF2_V        = $8D                   ; station colour for pixel colour 3 (COLPF2): girders, platforms
BLINK_TMR       = $8E                   ; frames until the status line blinks (CHACTL blank toggle)
BLINK_ON        = $8F                   ; current CHACTL value (0/1)
BOB_X           = $90                   ; Bounty Bob horizontal position (P/M coordinates)
BOB_Y           = $91                   ; Bounty Bob vertical position (top of his 21-line sprite)
BOB_FRAME       = $92                   ; animation frame 0-12 (1-3 walk right, 4-6 walk left, 7-8 climb, 9-10
                                        ;   ladder top, 11-12 jump)
BOB_FALL        = $93                   ; non-zero while Bob is falling freely
SPR_PTR         = $94                   ; (2) pointer to the current sprite or list
PIX_PTR         = $96                   ; (2) bitmap line pointer used by READ_PIXEL
JUMP_LOCK       = $98                   ; frames before the button may start another jump
PROBE_Y         = $99                   ; scan line being tested under Bob's feet
PROBE_X         = $9A                   ; P/M x being tested under Bob's feet
TMP9B           = $9B                   ; scratch
WALK_STEP       = $9C                   ; walk animation step 1-3
FRAMES          = $9D                   ; frame counter, incremented by every vertical-blank interrupt
LADDERS         = $9E                   ; (2) pointer to this station's ladder list
MOVE_A          = $A0                   ; movement state A (jump frame, ladder rung, transporter timer ...)
MOVE_B          = $A1                   ; movement state B (jump direction, ladder limit ...)
FALL_LEN        = $A2                   ; frames of falling counted by LAND_CHECK (40 or more is fatal)
SPECIAL         = $A3                   ; special state: 0 normal, 1 dying, 2 dead, 3-7 transporter phases
SND3_F          = $A4                   ; voice 3 frequency (footsteps, jump and fall effects)
SND3_VOL        = $A5                   ; voice 3 decaying volume
ALIVE           = $A6                   ; 2 while the station is being played; counts down after death; 0 ends the
                                        ;   turn
CNT5            = $A7                   ; scratch counter
SLIDES          = $A8                   ; (2) pointer to this station's slide (chute) list
SLIDE_LEN       = $AA                   ; frames left on a slide
CNT6            = $AB                   ; scratch
TRANS_LOCK      = $AC                   ; transporter lock-out after a trip / flashing colour on some stations
TRANS_DEST      = $AD                   ; transporter tube Bob asked for (1-4)
TRANS_Y         = $AE                   ; Bob's vertical position saved while he is transported
DLI_BAND        = $AF                   ; which horizontal band of mutants the next DLI handles (4..0)
TRANS_SRC       = $B0                   ; tube Bob is standing in
T_SCROLL        = $B0                   ; title: fine-scroll phase now showing (0-15)
LIFTS           = $B1                   ; (2) pointer to this station's moving-platform list
T_TMP           = $B1                   ; title: scratch (also the operand of the kernel's delay instruction)
T_NEWSCROLL     = $B2                   ; title: scroll phase the main loop wants shown next
SPECIAL_X       = $B3                   ; position of this station's special object (cannon, transporter column)
T_PTR           = $B3                   ; title: (2) pointer into the RAM kernel / PM memory
DYING           = $B4                   ; death animation counter (non-zero while Bob is dying)
PLAYER          = $B5                   ; current player (0 or 1)
T_CNT           = $B5                   ; title: scratch counter
T_CNT2          = $B6                   ; title: scratch counter
STATION         = $B7                   ; station being played (1-10; 11 = the title/credits screen)
T_LINE          = $B7                   ; title: which display-list interrupt is next
ZONE            = $B8                   ; zone (each zone is one pass through the ten stations, getting harder)
T_ROT           = $B8                   ; title: colour rotation of the chasing lights (0-9)
LIVES           = $B9                   ; lives left
T_HUE           = $B9                   ; title: start of the rainbow on the high-score lines
XLIFE           = $BA                   ; extra life: 10 = not yet earned, 9..1 = jingle playing, 0 = done
T_TEXTCOL       = $BA                   ; title: colour of "HIGH SCORES:" (pulsing)
SCORE           = $BB                   ; score: six decimal digits, one per byte, most significant first ($BB-$C0)
T_TEXTSTEP      = $BB                   ; title: +1/-1 brightness step for T_TEXTCOL
T_TIMER30       = $BC                   ; title: 30-frame timer (changes every frame)
T_TIMER14       = $BD                   ; title: 14-frame timer for the rainbow
T_INVERSE       = $BE                   ; title: CHACTL value (blinks "START" in inverse video)
T_PMPAGE        = $BF                   ; title: PM buffer being drawn ($1C or $04)
T_PMPTR         = $C0                   ; title: (2) pointer into the back PM buffer
P2_DATA         = $C1                   ; the other player's copy of STATION..SCORE ($C1-$CA)
T_NEXT          = $C2                   ; title: next scroll phase
P2_LIVES        = $C3                   ; the other player's lives (non-zero means he is still playing)
T_TIMER4        = $C3                   ; title: 4-frame timer for the text pulsing
T_COLIX         = $C4                   ; title: colour index for the rainbow DLI
T_SELDLY        = $C5                   ; title: SELECT debounce
T_STARTDLY      = $C6                   ; title: START debounce (START must be released first)
T_TIMER60       = $C7                   ; title: 60-frame timer
T_DEMOSEC       = $C8                   ; title: seconds left before the demo starts
T_TIMER11       = $C9                   ; title: 11-frame timer for the background tone
T_VOLUME        = $CA                   ; title: AUDC1 value of the fading background tone
IS5200          = $CB                   ; 0 on the Atari 400/800, 1 on the Atari 5200
FONTPAGE        = $CC                   ; high byte of the ROM font: $E0 on the 400/800, $F8 on the 5200
LINECNT         = $CD                   ; scan-line counter inside display list interrupts
CNT7            = $CE                   ; scratch counter
POT_X           = $CF                   ; 5200: analog stick X (POT0)
POT_Y           = $D0                   ; 5200: analog stick Y (POT1)
ITEM_GOT        = $D1                   ; set when an item is picked up: the mutants turn edible on the next frame
CANNON_DONE     = $D2                   ; station 10: Bob has been fired to the top and is no longer drawn as a
                                        ;   cannonball
CANNON_ST       = $D3                   ; station 10 cannon state: 0 idle, 1 Bob inside, 2 fired
CANNON_X        = $D4                   ; station 10 cannon position
TNT             = $D5                   ; station 10 TNT charge loaded (tons)
LIFT_DLY        = $D6                   ; station 8 lift: key debounce
LIFT_ON         = $D7                   ; station 8 lift: Bob is operating the lift
LIFT_ANIM       = $D8                   ; station 8 lift: scissor animation frame 0-6
ON_LIFT         = $D9                   ; zero when Bob is standing on the lift platform
LIFT_X          = $DA                   ; station 8 lift platform x
LIFT_Y          = $DB                   ; station 8 lift platform y
CHEAT_IDX       = $DD                   ; how many digits of the phone-number code have been typed (13 = all)
SAVE_Y2         = $DE                   ; scratch save of Y
DEMO_CNT        = $DF                   ; frames left for the current demo input
KEYCODE         = $E0                   ; last key read from POKEY ($FF = none)
DEMO_PTR        = $E1                   ; (2) pointer into the recorded demo; high byte 0 = a real player is playing
START_DLY       = $E3                   ; START/fire debounce
PAUSED          = $E4                   ; non-zero while the game is paused (ESC key)
MUT_SCORE       = $E5                   ; hundreds to add for an eaten mutant (8 or 9)
HIT_M           = $E6                   ; missile-to-player collisions, one byte per mutant band ($E6-$E9)
HIT_P3          = $EA                   ; player 3 (mutant) to player collisions, one byte per band ($EA-$ED)
TMPEF           = $EF                   ; scratch
MUT_PM          = $F0                   ; (2) pointer into player-3 memory when a mutant's shape is drawn
MUT_LOOP        = $F2                   ; mutants left to process in this DLI
MUTANTS         = $F3                   ; (2) pointer to this station's mutant definitions
MUT_IDX         = $F5                   ; offset of the current mutant record (multiples of 11)
SECTIONS        = $F6                   ; floor sections still to be claimed (0 = station complete)
TICK_SND        = $F7                   ; bonus-timer tick sound counter
WIPE_LINE       = $F8                   ; screen wipe: display-list line being removed (0 = finished)
TWO_PLAYER      = $F9                   ; 0 = one-player game, 1 = two-player game
LIFE_USED       = $FA                   ; set once a life has been taken for this turn
BCD_100         = $FB                   ; scratch digit / DLI timer
SEC_TMR         = $FC                   ; 60-frame timer
BONUS_TMR       = $FD                   ; frames until the bonus timer drops by 100
MOVE_OK         = $FE                   ; 0 while the station is starting, then 7 (Bob may move)
KILLED          = $FF                   ; non-zero: Bob has touched a mutant or run out of time
VDSLST          = $0200                 ; 400/800 OS: display-list-interrupt vector
VVBLKI5         = $0202                 ; 5200 BIOS: immediate vertical-blank vector
VVBLKD5         = $0204                 ; 5200 BIOS: deferred vertical-blank vector
VDSLST5         = $0206                 ; 5200 BIOS: display-list-interrupt vector
VVBLKI          = $0222                 ; 400/800 OS: immediate vertical-blank vector
PM_MISSILES     = $0300                 ; player/missile memory (single-line resolution, PMBASE effectively 0):
                                        ;   missiles
PM_P0           = $0400                 ; player 0: Bob's outline colour
PM_P1           = $0500                 ; player 1: Bob's second colour
PM_P2           = $0600                 ; player 2: Bob's third colour
PM_P3           = $0700                 ; player 3: the mutants (re-used five times down the screen)
HISCORES        = $0800                 ; high-score table: 10 lines of 20 screen-code characters
TEXT_RAM        = $08C8                 ; text lines for the title, high-score and "prepare" screens
ITEMS           = $0992                 ; this station's items, 3 bytes each: shape number (bit 7 = still there), y,
                                        ;   x
MUT_TAB         = $09C0                 ; mutant records, 11 bytes each (8 mutants)
PULV_TAB        = $0A19                 ; station 9 pulverizers: 3 bytes each (timer, direction, height)
FONT5200        = $1C00                 ; 5200: RAM copy of the BIOS font with a few changed characters
DLIST           = $2000                 ; game display list
STATUS          = $20D8                 ; status line (40 characters of ANTIC mode 2)
BITMAP          = $2100                 ; the playfield: 184 lines x 40 bytes, 4 pixels per byte (ANTIC mode E)
LINE_LO         = $3DB8                 ; low byte of the address of each bitmap line, indexed by y (8-191)
LINE_HI         = $3E70                 ; high byte of the address of each bitmap line
LIFT_TAB        = $3F30                 ; moving-platform records, 6 bytes each
CONSOL          = $D01F                 ; GTIA: console keys START/SELECT/OPTION (bits 0-2, 0 = pressed)
PORTA           = $D300                 ; PIA: joystick 0/1 directions (bits 0-3 stick 0: up,down,left,right; 0 =
                                        ;   pushed)
PACTL           = $D302                 ; PIA: port A control (bit 2 selects data register / direction register)
DMACTL          = $D400                 ; ANTIC: DMA control (playfield width, P/M DMA, P/M resolution)
CHACTL          = $D401                 ; ANTIC: character control (bit 0 = blank bit-7 characters, bit 1 = inverse)
DLISTL          = $D402                 ; ANTIC: display list address, low byte
DLISTH          = $D403                 ; ANTIC: display list address, high byte
HSCROL          = $D404                 ; ANTIC: horizontal fine scroll (0-15 colour clocks)
PMBASE          = $D407                 ; ANTIC: player/missile base page
CHBASE          = $D409                 ; ANTIC: character set base page
WSYNC           = $D40A                 ; ANTIC: any write halts the CPU until the end of the scan line
VCOUNT          = $D40B                 ; ANTIC: current scan line / 2
NMIEN           = $D40E                 ; ANTIC: NMI enable (bit 7 = DLI, bit 6 = VBI)
NMIRES          = $D40F                 ; ANTIC: write = reset NMI status (read = NMIST)
FONT_800        = $E000                 ; OS ROM character set on the 400/800 (the game draws text from it)
FONT_5200       = $F800                 ; 5200 BIOS character set

        .org $8000


;-----------------------------------------------------------------------------
;  TITLE_DLIST - display list of the high-score screen. The JVB's address bytes ($801F)
;  are also the first two characters of the bottom row of lights (LMS $801F), so its
;  target ($1500) is nonsense - harmless, because TITLE_VBI reloads DLIST every frame.
;-----------------------------------------------------------------------------
TITLE_DLIST:    .byte $70               ; 8 blank lines
                .byte $70               ; 8 blank lines
                .byte $F0               ; 8 blank lines +DLI
                .byte $D7,$59,$80       ; top row of lights: the "5"s at $8059, fine-scrolled  mode 7 LMS $8059
                                        ;   +HSCROL +DLI
                .byte $70               ; 8 blank lines
                .byte $86               ; "HIGH SCORES:" (continues from the top row)  mode 6 +DLI
                .byte $70               ; 8 blank lines
                .byte $F0               ; 8 blank lines +DLI
                .byte $C7,$00,$08       ; the best score, in big letters  mode 7 LMS $0800 +DLI
                .byte $F0               ; 8 blank lines +DLI
                .byte $86               ; high scores 2-10  mode 6 +DLI
                .byte $86               ; mode 6 +DLI
                .byte $86               ; mode 6 +DLI
                .byte $86               ; mode 6 +DLI
                .byte $86               ; mode 6 +DLI
                .byte $86               ; mode 6 +DLI
                .byte $86               ; mode 6 +DLI
                .byte $86               ; mode 6 +DLI
                .byte $86               ; mode 6 +DLI
                .byte $70               ; 8 blank lines
                .byte $82               ; "Press START For a 1 Miner Game"  mode 2 +DLI
                .byte $70               ; 8 blank lines
                .byte $F0               ; 8 blank lines +DLI
                .byte $57,$1F,$80       ; bottom row of lights (its data begins at $801F)  mode 7 LMS $801F +HSCROL
                .byte $41,$00,$15       ; JVB $1500
                .byte $00,$55,$00,$95,$00,$D5,$00,$00,$00,$00,$00,$15,$00,$55,$00,$95; rest of the bottom row of
                                                                                     ;   lights: '5' ($15) with colour
                                                                                     ;   bits $40/$80/$C0
                .byte $00,$D5

;-----------------------------------------------------------------------------
;  TITLE_TEXT - "Press START For a 1 Miner Game" (40 characters, copied to TEXT_RAM).
;  Its first bytes are also the end of the bottom row of lights.
;-----------------------------------------------------------------------------
TITLE_TEXT:     .byte $00,$00,$00,$00,$00,$30,$72,$65,$73,$73; "     Press"
                .byte $00,$B3,$B4,$A1,$B2,$B4,$00,$26,$6F,$72; " START For"
                .byte $00,$61,$00,$11,$00,$2D,$69,$6E,$65,$72; " a 1 Miner"
                .byte $00,$27,$61,$6D,$65,$00,$00,$00,$00,$00; " Game     "

;-----------------------------------------------------------------------------
;  TOP_ROW - the top row of lights. ANTIC fetches 24 bytes from $8059 (the last two
;  characters of TITLE_TEXT are its first two), then "HIGH SCORES:" at $8071.
;-----------------------------------------------------------------------------
TOP_ROW:        .byte $15,$00,$55,$00,$95,$00,$D5,$00,$00,$00,$00
                .byte $00,$15,$00,$55,$00,$95,$00,$D5,$00,$00,$00
                .byte $00,$00,$00,$00,$28,$29,$27,$28,$00,$33; "    HIGH S"
                .byte $23,$2F,$32,$25,$33,$1A,$00,$00,$00,$00; "CORES:    "

;-----------------------------------------------------------------------------
;  TEXT_POOL - strings drawn into the bitmap by DRAW_STRING (screen codes; TXT_IDX offsets):
;    $00 DANGER  $06 Radioactive  $11 Waste  $16 MINER 2049er  $22 By  $24 Bill Hogue
;    $2E Starring  $36 "Bounty Bob"  $42 Copyright (C)  $4F 1982 By  $56 Big Five Software
;    $67 P.O. Box 9078-185  $78 Van Nuys Ca 91409  $89 (213) 782-6861  $97 Game Over
;    $A0 Miner  $A5 TNT Charge=   0 Tons
;  The phone number at $810E is also the cheat code (CHEAT_CODE, see PHONE_CODE).
;-----------------------------------------------------------------------------
TEXT_POOL:      .byte $24,$21,$2E,$27,$25,$32,$32,$61,$64,$69,$6F,$61,$63,$74,$69,$76; "DANGERRadioactiv"
                .byte $65,$37,$61,$73,$74,$65,$2D,$29,$2E,$25,$32,$00,$12,$10,$14,$19; "eWasteMINER 2049"
                .byte $65,$72,$22,$79,$22,$69,$6C,$6C,$00,$28,$6F,$67,$75,$65,$33,$74; "erByBill HogueSt"
                .byte $61,$72,$72,$69,$6E,$67,$02,$22,$6F,$75,$6E,$74,$79,$00,$22,$6F; "arring"Bounty Bo"
                .byte $62,$02,$23,$6F,$70,$79,$72,$69,$67,$68,$74,$00,$08,$23,$09,$11; "b"Copyright (C)1"
                .byte $19,$18,$12,$00,$22,$79,$22,$69,$67,$00,$26,$69,$76,$65,$00,$33; "982 ByBig Five S"
                .byte $6F,$66,$74,$77,$61,$72,$65,$30,$0E,$2F,$0E,$00,$22,$6F,$78,$00; "oftwareP.O. Box "
                .byte $19,$10,$17,$18,$0D,$11,$18,$15,$36,$61,$6E,$00,$2E,$75,$79,$73; "9078-185Van Nuys"
                .byte $00,$23,$61,$00,$19,$11,$14,$10,$19; " Ca 91409"
PHONE_TEXT:     .byte $08               ; "("
CHEAT_CODE:     .byte $12,$11,$13,$09,$00,$17,$18,$12,$0D,$16,$18,$16,$11; "213) 782-6861"
                .byte $27,$61,$6D,$65,$00,$2F,$76,$65,$72,$2D,$69,$6E,$65,$72,$34,$2E; "Game OverMinerTN"
                .byte $34,$00,$23,$68,$61,$72,$67,$65,$1D,$00,$00,$00,$10,$00,$34,$6F; "T Charge=   0 To"
                .byte $6E,$73           ; "ns"

;-----------------------------------------------------------------------------
;  NAME_TEXT - the name-entry screen (copied to $0918): a 24-byte mode 7 line (fine
;  scrolled), then three 20-byte lines. Upper case with colour bits set = coloured text.
;-----------------------------------------------------------------------------
NAME_TEXT:      .byte $00,$00,$00,$00,$00,$00,$00,$00,$AD,$A9,$AE,$A5; "        MINE"
                .byte $B2,$00,$91,$00,$00,$00,$00,$00,$00,$00,$00,$00; "R 1         "
                .byte $00,$00,$00,$00,$67,$72,$65,$61,$74,$00; "    great "
                .byte $73,$63,$6F,$72,$65,$41,$00,$00,$00,$00; "score.    "
                .byte $00,$00,$E5,$EE,$F4,$E5,$F2,$00,$F9,$EF; "  enter yo"
                .byte $F5,$F2,$00,$EE,$E1,$ED,$E5,$C1,$00,$00; "ur name.  "
                .byte $00,$00,$00,$9E,$9E,$00,$00,$00,$00,$00; "   >>     "
                .byte $00,$00,$00,$00,$00,$9C,$9C,$00,$00,$00; "     <<   "

;-----------------------------------------------------------------------------
;  PREP_TEXT - "MINER 1" / "prepare for" lines of the prepare screen (48 bytes copied to
;  $0918, starting one byte earlier at $8191), then the "STATION n" lines (from $81C2, or
;  $81C3 for station 10 so that the two digits stay centred) and "Zone" at $81F1.
;-----------------------------------------------------------------------------
PREP_TEXT:      .byte $00,$00,$00,$00,$00,$00,$00,$2D,$29,$2E,$25,$32,$00,$11,$00,$00; "       MINER 1  "
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$70,$72,$65; "             pre"
                .byte $70,$61,$72,$65,$00,$66,$6F,$72,$00,$00,$00,$00,$00,$00,$00,$00; "pare for        "
                .byte $00,$00,$00,$00,$00,$00,$B3,$B4,$A1,$B4,$A9,$AF,$AE,$00,$91,$00; "      STATION 1 "
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00; "                "
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00; "               "
ZONE_TEXT:      .byte $FA,$EF,$EE,$E5   ; "zone"

;-----------------------------------------------------------------------------
;  KEY_TO_SCREEN - 400/800 keyboard code (KBCODE and $3F) -> screen code; 0 = no character
;  (RETURN, DELETE, TAB ... are handled by code).
;-----------------------------------------------------------------------------
KEY_TO_SCREEN:  .byte $2C,$2A,$1B,$00,$00,$2B,$0B,$0A,$2F,$00,$30,$35,$00,$29,$0D,$1D
                .byte $36,$00,$23,$00,$00,$22,$38,$3A,$14,$00,$13,$16,$00,$15,$12,$11
                .byte $0C,$00,$0E,$2E,$00,$2D,$0F,$00,$32,$00,$25,$39,$00,$34,$37,$31
                .byte $19,$00,$10,$17,$00,$18,$1C

;-----------------------------------------------------------------------------
;  SHIFT_MAP - for screen codes 1-27 (digits and punctuation, as SHIFT_MAP-1 indexed by
;  the code): the character SHIFT gives on that key ('1' -> '!', '2' -> '"' ...).
;  It starts inside KEY_TO_SCREEN.
;-----------------------------------------------------------------------------
SHIFT_MAP:      .byte $1E,$26,$28,$24,$00,$00,$27,$33,$21,$3E,$3C,$3B,$3F,$3D,$1F,$09
                .byte $01,$02,$03,$04,$05,$06,$07,$20,$08,$1A,$1A

;-----------------------------------------------------------------------------
;  BOB_FRAME_LO / BOB_FRAME_HI - addresses of Bob's 13 animation frames.
;   0 standing (same as 1)  1-3 walking right  4-6 walking left  7-8 climbing
;   9-10 at the top of a ladder  11 jumping/sliding right  12 left
;-----------------------------------------------------------------------------
BOB_FRAME_LO:   .byte $60,$60,$93,$C6,$F9,$2C,$5F,$92,$C5,$F8,$2B,$5F,$92
BOB_FRAME_HI:   .byte $82,$82,$82,$82,$82,$83,$83,$83,$83,$83,$84,$84,$84

;-----------------------------------------------------------------------------
;  Bob frame 0 (standing): player 0 (20 lines), player 1 (17), player 2 (17), drawn from the
;  last byte upwards; each layer's first line is the previous layer's last.
;-----------------------------------------------------------------------------
BOB_0:          .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $6E               ; .##.###.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $6E               ; .##.###.
                .byte $7E               ; .######.
                .byte $3C               ; ..####..
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $3C               ; ..####..
                .byte $34               ; ..##.#..
                .byte $3E               ; ..#####.
                .byte $34               ; ..##.#..
                .byte $38               ; ..###...
                .byte $1C               ; ...###..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $6E               ; .##.###.
                .byte $6E               ; .##.###.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $10               ; ...#....
                .byte $10               ; ...#....
                .byte $10               ; ...#....
                .byte $10               ; ...#....
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $1C

;-----------------------------------------------------------------------------
;  Bob frame 2 (walk right 2): player 0 (20 lines), player 1 (17), player 2 (17), drawn from the
;  last byte upwards; each layer's first line is the previous layer's last.
;-----------------------------------------------------------------------------
BOB_2:          .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $6E               ; .##.###.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7A               ; .####.#.
                .byte $7E               ; .######.
                .byte $3C               ; ..####..
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $3C               ; ..####..
                .byte $34               ; ..##.#..
                .byte $3E               ; ..#####.
                .byte $34               ; ..##.#..
                .byte $38               ; ..###...
                .byte $1C               ; ...###..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $6E               ; .##.###.
                .byte $76               ; .###.##.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $10               ; ...#....
                .byte $10               ; ...#....
                .byte $08               ; ....#...
                .byte $04               ; .....#..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $14               ; ...#.#..
                .byte $14               ; ...#.#..
                .byte $1E

;-----------------------------------------------------------------------------
;  Bob frame 3 (walk right 3): player 0 (20 lines), player 1 (17), player 2 (17), drawn from the
;  last byte upwards; each layer's first line is the previous layer's last.
;-----------------------------------------------------------------------------
BOB_3:          .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $6E               ; .##.###.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $3E               ; ..#####.
                .byte $7E               ; .######.
                .byte $3C               ; ..####..
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $3C               ; ..####..
                .byte $34               ; ..##.#..
                .byte $3E               ; ..#####.
                .byte $34               ; ..##.#..
                .byte $38               ; ..###...
                .byte $1C               ; ...###..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $6E               ; .##.###.
                .byte $5E               ; .#.####.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $10               ; ...#....
                .byte $10               ; ...#....
                .byte $20               ; ..#.....
                .byte $40               ; .#......
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $24               ; ..#..#..
                .byte $24               ; ..#..#..
                .byte $36

;-----------------------------------------------------------------------------
;  Bob frame 4 (walk left 1): player 0 (20 lines), player 1 (17), player 2 (17), drawn from the
;  last byte upwards; each layer's first line is the previous layer's last.
;-----------------------------------------------------------------------------
BOB_4:          .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $76               ; .###.##.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $76               ; .###.##.
                .byte $7E               ; .######.
                .byte $3C               ; ..####..
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $3C               ; ..####..
                .byte $2C               ; ..#.##..
                .byte $7C               ; .#####..
                .byte $2C               ; ..#.##..
                .byte $1C               ; ...###..
                .byte $38               ; ..###...
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $76               ; .###.##.
                .byte $76               ; .###.##.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $08               ; ....#...
                .byte $08               ; ....#...
                .byte $08               ; ....#...
                .byte $08               ; ....#...
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $38

;-----------------------------------------------------------------------------
;  Bob frame 5 (walk left 2): player 0 (20 lines), player 1 (17), player 2 (17), drawn from the
;  last byte upwards; each layer's first line is the previous layer's last.
;-----------------------------------------------------------------------------
BOB_5:          .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $76               ; .###.##.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $5E               ; .#.####.
                .byte $7E               ; .######.
                .byte $3C               ; ..####..
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $3C               ; ..####..
                .byte $2C               ; ..#.##..
                .byte $7C               ; .#####..
                .byte $2C               ; ..#.##..
                .byte $1C               ; ...###..
                .byte $38               ; ..###...
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $76               ; .###.##.
                .byte $6E               ; .##.###.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $08               ; ....#...
                .byte $08               ; ....#...
                .byte $10               ; ...#....
                .byte $20               ; ..#.....
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $28               ; ..#.#...
                .byte $28               ; ..#.#...
                .byte $78

;-----------------------------------------------------------------------------
;  Bob frame 6 (walk left 3): player 0 (20 lines), player 1 (17), player 2 (17), drawn from the
;  last byte upwards; each layer's first line is the previous layer's last.
;-----------------------------------------------------------------------------
BOB_6:          .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $76               ; .###.##.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7C               ; .#####..
                .byte $7E               ; .######.
                .byte $3C               ; ..####..
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $3C               ; ..####..
                .byte $2C               ; ..#.##..
                .byte $7C               ; .#####..
                .byte $2C               ; ..#.##..
                .byte $1C               ; ...###..
                .byte $38               ; ..###...
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $76               ; .###.##.
                .byte $7A               ; .####.#.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $08               ; ....#...
                .byte $08               ; ....#...
                .byte $04               ; .....#..
                .byte $02               ; ......#.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $24               ; ..#..#..
                .byte $24               ; ..#..#..
                .byte $6C

;-----------------------------------------------------------------------------
;  Bob frame 7 (climb 1): player 0 (20 lines), player 1 (17), player 2 (17), drawn from the
;  last byte upwards; each layer's first line is the previous layer's last.
;-----------------------------------------------------------------------------
BOB_7:          .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $7E               ; .######.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7E               ; .######.
                .byte $7E               ; .######.
                .byte $3C               ; ..####..
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $3C               ; ..####..
                .byte $7E               ; .######.
                .byte $7E               ; .######.
                .byte $7E               ; .######.
                .byte $3C               ; ..####..
                .byte $3C               ; ..####..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7E               ; .######.
                .byte $7E               ; .######.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $C0               ; ##......
                .byte $80               ; #.......
                .byte $83               ; #.....##
                .byte $81               ; #......#
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $24               ; ..#..#..
                .byte $26               ; ..#..##.
                .byte $60

;-----------------------------------------------------------------------------
;  Bob frame 8 (climb 2): player 0 (20 lines), player 1 (17), player 2 (17), drawn from the
;  last byte upwards; each layer's first line is the previous layer's last.
;-----------------------------------------------------------------------------
BOB_8:          .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $7E               ; .######.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7E               ; .######.
                .byte $7E               ; .######.
                .byte $3C               ; ..####..
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $3C               ; ..####..
                .byte $7E               ; .######.
                .byte $7E               ; .######.
                .byte $7E               ; .######.
                .byte $3C               ; ..####..
                .byte $3C               ; ..####..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7E               ; .######.
                .byte $7E               ; .######.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $03               ; ......##
                .byte $01               ; .......#
                .byte $C1               ; ##.....#
                .byte $81               ; #......#
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $24               ; ..#..#..
                .byte $64               ; .##..#..
                .byte $06

;-----------------------------------------------------------------------------
;  Bob frame 9 (ladder top 1): player 0 (20 lines), player 1 (17), player 2 (17), drawn from the
;  last byte upwards; each layer's first line is the previous layer's last.
;-----------------------------------------------------------------------------
BOB_9:          .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $3E               ; ..#####.
                .byte $3E               ; ..#####.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7E               ; .######.
                .byte $7F               ; .#######
                .byte $7F               ; .#######
                .byte $7E               ; .######.
                .byte $66               ; .##..##.
                .byte $66               ; .##..##.
                .byte $60               ; .##.....
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $7E               ; .######.
                .byte $3C               ; ..####..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7E               ; .######.
                .byte $7E               ; .######.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $01               ; .......#
                .byte $41               ; .#.....#
                .byte $C0               ; ##......
                .byte $80               ; #.......
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $04               ; .....#..
                .byte $26               ; ..#..##.
                .byte $20               ; ..#.....
                .byte $60

;-----------------------------------------------------------------------------
;  Bob frame 10 (ladder top 2): player 0 (20 lines), player 1 (17), player 2 (17), drawn from the
;  last byte upwards; each layer's first line is the previous layer's last.
;-----------------------------------------------------------------------------
BOB_10:         .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7C               ; .#####..
                .byte $7C               ; .#####..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7E               ; .######.
                .byte $FE               ; #######.
                .byte $FE               ; #######.
                .byte $7E               ; .######.
                .byte $66               ; .##..##.
                .byte $66               ; .##..##.
                .byte $06               ; .....##.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $7E               ; .######.
                .byte $3C               ; ..####..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7E               ; .######.
                .byte $7E               ; .######.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $80               ; #.......
                .byte $82               ; #.....#.
                .byte $03               ; ......##
                .byte $01               ; .......#
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $20               ; ..#.....
                .byte $64               ; .##..#..
                .byte $04               ; .....#..
                .byte $06,$00

;-----------------------------------------------------------------------------
;  Bob frame 11 (jump right): player 0 (20 lines), player 1 (17), player 2 (17), drawn from the
;  last byte upwards; each layer's first line is the previous layer's last.
;-----------------------------------------------------------------------------
BOB_11:         .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $6E               ; .##.###.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7E               ; .######.
                .byte $7E               ; .######.
                .byte $38               ; ..###...
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $3C               ; ..####..
                .byte $34               ; ..##.#..
                .byte $3E               ; ..#####.
                .byte $3C               ; ..####..
                .byte $30               ; ..##....
                .byte $1C               ; ...###..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $5E               ; .#.####.
                .byte $3E               ; ..#####.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $01               ; .......#
                .byte $01               ; .......#
                .byte $02               ; ......#.
                .byte $10               ; ...#....
                .byte $20               ; ..#.....
                .byte $40               ; .#......
                .byte $80               ; #.......
                .byte $80               ; #.......
                .byte $05               ; .....#.#
                .byte $57               ; .#.#.###
                .byte $72               ; .###..#.
                .byte $20

;-----------------------------------------------------------------------------
;  Bob frame 12 (jump left): player 0 (20 lines), player 1 (17), player 2 (17), drawn from the
;  last byte upwards; each layer's first line is the previous layer's last.
;-----------------------------------------------------------------------------
BOB_12:         .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $76               ; .###.##.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7E               ; .######.
                .byte $7E               ; .######.
                .byte $1C               ; ...###..
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $FF               ; ########
                .byte $3C               ; ..####..
                .byte $2C               ; ..#.##..
                .byte $7C               ; .#####..
                .byte $3C               ; ..####..
                .byte $0C               ; ....##..
                .byte $38               ; ..###...
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $7A               ; .####.#.
                .byte $7C               ; .#####..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $80               ; #.......
                .byte $80               ; #.......
                .byte $40               ; .#......
                .byte $08               ; ....#...
                .byte $04               ; .....#..
                .byte $02               ; ......#.
                .byte $01               ; .......#
                .byte $01               ; .......#
                .byte $A0               ; #.#.....
                .byte $EA               ; ###.#.#.
                .byte $4E               ; .#..###.

;-----------------------------------------------------------------------------
;  ITEM_SHAPES - addresses of the 37 item pictures (index = item shape number). Entries
;  33-36 (the goblet and the three TNT bundles) are the first 8 bytes of STATION_TABLE,
;  whose entry 0 is never used as a station: the two tables overlap.
;    1-5   the points numbers "100" .. "500"       11  "1100"      26  the "BF" logo
;-----------------------------------------------------------------------------
ITEM_SHAPES:    .word $0004,ITEM_1,ITEM_2,ITEM_3
                .word ITEM_4,ITEM_5,ITEM_6,ITEM_7
                .word ITEM_8,ITEM_9,ITEM_10,ITEM_11
                .word ITEM_12,ITEM_13,ITEM_14,ITEM_15
                .word ITEM_16,ITEM_17,ITEM_18,ITEM_19
                .word ITEM_20,ITEM_21,ITEM_22,ITEM_23
                .word ITEM_24,ITEM_25,ITEM_26,ITEM_27
                .word ITEM_28,ITEM_29,ITEM_30,ITEM_31
                .word ITEM_32

;-----------------------------------------------------------------------------
;  STATION_TABLE - per station (1-11), the addresses of its ladder, slide, moving-platform
;  and girder lists. Entry 0 is ITEM_SHAPES 33-36. The last entry's girder address is
;  also the first word of ITEM_LISTS.
;-----------------------------------------------------------------------------
STATION_TABLE:  .word ITEM_33,ITEM_34,ITEM_35,ITEM_36
                .word LADDERS_1,EMPTY_LIST,EMPTY_LIST,GIRDERS_1
                .word LADDERS_2,SLIDES_2,EMPTY_LIST,GIRDERS_2
                .word LADDERS_3,EMPTY_LIST,EMPTY_LIST,GIRDERS_3
                .word LADDERS_4,EMPTY_LIST,EMPTY_LIST,GIRDERS_4
                .word EMPTY_LIST,SLIDES_5,LIFTS_5,GIRDERS_5
                .word LADDERS_6,EMPTY_LIST,LIFTS_6,GIRDERS_6
                .word EMPTY_LIST,SLIDES_7,LIFTS_7,GIRDERS_7
                .word LADDERS_8,SLIDES_8,LIFTS_8,GIRDERS_8
                .word LADDERS_9,SLIDES_9,LIFTS_9,GIRDERS_9
                .word LADDERS_10,SLIDES_10,EMPTY_LIST,GIRDERS_10
                .word LADDERS_11,EMPTY_LIST,EMPTY_LIST

;-----------------------------------------------------------------------------
;  ITEM_LISTS - per station, the address of its item list.
;-----------------------------------------------------------------------------
ITEM_LISTS:     .word GIRDERS_11,ITEMLIST_1,ITEMLIST_2,ITEMLIST_3,ITEMLIST_4,ITEMLIST_5
                .word ITEMLIST_6,ITEMLIST_7,ITEMLIST_8,ITEMLIST_9,ITEMLIST_10

;-----------------------------------------------------------------------------
;  MUTANT_LISTS - per station, the address of its 8 mutant records. Entry 11 (the credits)
;  is the first two bytes of MUTANT_SHAPES ($1E18): the 88 bytes there are read, but through
;  a mask of 0, so the credits get no mutants.
;-----------------------------------------------------------------------------
MUTANT_LISTS:   .word EMPTY_LIST,MUTANTS_1,MUTANTS_2,MUTANTS_3,MUTANTS_4,MUTANTS_5
                .word MUTANTS_6,MUTANTS_7,MUTANTS_8,MUTANTS_9,MUTANTS_10,$1E18

;-----------------------------------------------------------------------------
;  MUTANT_SHAPES - 10 shapes of 12 bytes (only 10 lines are copied), indexed by the
;  mutant's state: 0-1 facing right, 2-3 facing left, 4-7 the same when edible,
;  8-9 eaten (the numbers "80" and "90", the points scored). The table really starts at $8591 (state 0 = $8591), so
;  its first two
;  bytes are also the last word of MUTANT_LISTS, and its last two overlap the item list
;  of station 1.
;-----------------------------------------------------------------------------
MUTANT_SHAPES:  .byte $3E               ; ..#####.
                .byte $39               ; ..###..#
                .byte $4F               ; .#..####
                .byte $74               ; .###.#..
                .byte $3C               ; ..####..
                .byte $18               ; ...##...
                .byte $36               ; ..##.##.
                .byte $33               ; ..##..##
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $1E               ; ...####.
                .byte $3E               ; ..#####.
                .byte $39               ; ..###..#
                .byte $4F               ; .#..####
                .byte $74               ; .###.#..
                .byte $3C               ; ..####..
                .byte $18               ; ...##...
                .byte $6C               ; .##.##..
                .byte $CC               ; ##..##..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $78               ; .####...
                .byte $7C               ; .#####..
                .byte $9C               ; #..###..
                .byte $F2               ; ####..#.
                .byte $2E               ; ..#.###.
                .byte $3C               ; ..####..
                .byte $18               ; ...##...
                .byte $6C               ; .##.##..
                .byte $CC               ; ##..##..
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $78               ; .####...
                .byte $7C               ; .#####..
                .byte $9C               ; #..###..
                .byte $F2               ; ####..#.
                .byte $2E               ; ..#.###.
                .byte $3C               ; ..####..
                .byte $18               ; ...##...
                .byte $36               ; ..##.##.
                .byte $33               ; ..##..##
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $42               ; .#....#.
                .byte $7E               ; .######.
                .byte $5A               ; .#.##.#.
                .byte $66               ; .##..##.
                .byte $3C               ; ..####..
                .byte $18               ; ...##...
                .byte $66               ; .##..##.
                .byte $C3               ; ##....##
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $42               ; .#....#.
                .byte $7E               ; .######.
                .byte $5A               ; .#.##.#.
                .byte $66               ; .##..##.
                .byte $3C               ; ..####..
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $66               ; .##..##.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $42               ; .#....#.
                .byte $7E               ; .######.
                .byte $5A               ; .#.##.#.
                .byte $66               ; .##..##.
                .byte $3C               ; ..####..
                .byte $18               ; ...##...
                .byte $66               ; .##..##.
                .byte $C3               ; ##....##
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $18               ; ...##...
                .byte $3C               ; ..####..
                .byte $42               ; .#....#.
                .byte $7E               ; .######.
                .byte $5A               ; .#.##.#.
                .byte $66               ; .##..##.
                .byte $3C               ; ..####..
                .byte $18               ; ...##...
                .byte $18               ; ...##...
                .byte $66               ; .##..##.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $EE               ; ###.###.
                .byte $AA               ; #.#.#.#.
                .byte $EA               ; ###.#.#.
                .byte $AA               ; #.#.#.#.
                .byte $EE               ; ###.###.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $EE               ; ###.###.
                .byte $AA               ; #.#.#.#.
                .byte $EA               ; ###.#.#.
                .byte $2A               ; ..#.#.#.
                .byte $2E               ; ..#.###.
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........
                .byte $00               ; ........

;-----------------------------------------------------------------------------
;  station 1 (The Mine Shaft) items: shape (+$80), y, x
;-----------------------------------------------------------------------------
ITEMLIST_1:     .byte $8D,$74,$08
                .byte $86,$48,$40
                .byte $88,$40,$8C
                .byte $95,$19,$18
                .byte $8F,$59,$90
                .byte $96,$92,$85

;-----------------------------------------------------------------------------
;  EMPTY_LIST - the 0 that ends station 1's item list doubles as "no ladders / slides /
;  platforms" for the stations that have none.
;-----------------------------------------------------------------------------
EMPTY_LIST:     .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 2 (The Slides) items: shape (+$80), y, x
;-----------------------------------------------------------------------------
ITEMLIST_2:     .byte $8A,$11,$44
                .byte $91,$0C,$94
                .byte $9B,$26,$78
                .byte $90,$25,$3C
                .byte $8C,$59,$1C
                .byte $8D,$5A,$6E
                .byte $8E,$AC,$36
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 3 (The Transporters) items: shape (+$80), y, x
;-----------------------------------------------------------------------------
ITEMLIST_3:     .byte $91,$3A,$04
                .byte $94,$6C,$80
                .byte $9F,$22,$20
                .byte $93,$AA,$54
                .byte $9E,$3D,$8C
                .byte $9C,$42,$60
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 4 (The Lillipads) items: shape (+$80), y, x
;-----------------------------------------------------------------------------
ITEMLIST_4:     .byte $9B,$0A,$34
                .byte $88,$57,$10
                .byte $8C,$23,$4C
                .byte $A1,$3C,$54
                .byte $97,$46,$90
                .byte $89,$8D,$90
                .byte $A0,$A9,$20
                .byte $98,$63,$50
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 5 (Advanced Lillipads) items: shape (+$80), y, x
;-----------------------------------------------------------------------------
ITEMLIST_5:     .byte $99,$88,$30
                .byte $A1,$9E,$04
                .byte $90,$0B,$30
                .byte $92,$0A,$68
                .byte $9D,$3A,$78
                .byte $89,$3D,$18
                .byte $A0,$0D,$4C
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 6 (Radioactive Waste) items: shape (+$80), y, x
;-----------------------------------------------------------------------------
ITEMLIST_6:     .byte $8C,$87,$88
                .byte $8A,$08,$78
                .byte $99,$25,$3C
                .byte $A1,$0B,$10
                .byte $8D,$30,$1E
                .byte $86,$7D,$74
                .byte $9B,$75,$10
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 7 (Advanced Transporters) items: shape (+$80), y, x
;-----------------------------------------------------------------------------
ITEMLIST_7:     .byte $9E,$79,$28
                .byte $93,$95,$60
                .byte $9C,$3E,$38
                .byte $9A,$0A,$5C
                .byte $91,$46,$00
                .byte $94,$6E,$68
                .byte $9F,$A0,$84
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 8 (The Lift) items: shape (+$80), y, x
;-----------------------------------------------------------------------------
ITEMLIST_8:     .byte $9B,$09,$29
                .byte $A1,$08,$72
                .byte $98,$42,$32
                .byte $89,$61,$02
                .byte $8A,$5E,$34
                .byte $91,$34,$8B
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 9 (The Pulverizers) items: shape (+$80), y, x
;-----------------------------------------------------------------------------
ITEMLIST_9:     .byte $93,$A9,$88
                .byte $91,$A4,$11
                .byte $88,$86,$2C
                .byte $86,$12,$2C
                .byte $8E,$27,$2C
                .byte $90,$3D,$2C
                .byte $99,$55,$2C
                .byte $8C,$70,$2C
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 10 (The Cannon) items: shape (+$80), y, x
;-----------------------------------------------------------------------------
ITEMLIST_10:    .byte $A2,$6C,$04
                .byte $A2,$6C,$10
                .byte $A2,$6C,$1C
                .byte $A2,$82,$04
                .byte $A2,$82,$10
                .byte $A2,$82,$1C
                .byte $A3,$9C,$04
                .byte $A3,$9C,$10
                .byte $A3,$9C,$1C
                .byte $A4,$B3,$04
                .byte $A4,$B3,$10
                .byte $A4,$B3,$1C
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  item shape 1 - "100": 11 x 5 pixels, worth 100 points
;-----------------------------------------------------------------------------
ITEM_1:         .byte $0B,$05,$01       ; width, height, points (also the shape number of the points picture)
                .byte $08,$A8,$A8       ; ..2. 222. 222.
                .byte $08,$88,$88       ; ..2. 2.2. 2.2.
                .byte $08,$88,$88       ; ..2. 2.2. 2.2.
                .byte $08,$88,$88       ; ..2. 2.2. 2.2.
                .byte $08,$A8,$A8       ; ..2. 222. 222.

;-----------------------------------------------------------------------------
;  item shape 2 - "200": 11 x 5 pixels, worth 100 points
;-----------------------------------------------------------------------------
ITEM_2:         .byte $0B,$05,$01       ; width, height, points (also the shape number of the points picture)
                .byte $A8,$A8,$A8       ; 222. 222. 222.
                .byte $08,$88,$88       ; ..2. 2.2. 2.2.
                .byte $A8,$88,$88       ; 222. 2.2. 2.2.
                .byte $80,$88,$88       ; 2... 2.2. 2.2.
                .byte $A8,$A8,$A8       ; 222. 222. 222.

;-----------------------------------------------------------------------------
;  item shape 3 - "300": 11 x 5 pixels, worth 100 points
;-----------------------------------------------------------------------------
ITEM_3:         .byte $0B,$05,$01       ; width, height, points (also the shape number of the points picture)
                .byte $A8,$A8,$A8       ; 222. 222. 222.
                .byte $08,$88,$88       ; ..2. 2.2. 2.2.
                .byte $A8,$88,$88       ; 222. 2.2. 2.2.
                .byte $08,$88,$88       ; ..2. 2.2. 2.2.
                .byte $A8,$A8,$A8       ; 222. 222. 222.

;-----------------------------------------------------------------------------
;  item shape 4 - "400": 11 x 5 pixels, worth 100 points
;-----------------------------------------------------------------------------
ITEM_4:         .byte $0B,$05,$01       ; width, height, points (also the shape number of the points picture)
                .byte $88,$A8,$A8       ; 2.2. 222. 222.
                .byte $88,$88,$88       ; 2.2. 2.2. 2.2.
                .byte $A8,$88,$88       ; 222. 2.2. 2.2.
                .byte $08,$88,$88       ; ..2. 2.2. 2.2.
                .byte $08,$A8,$A8       ; ..2. 222. 222.

;-----------------------------------------------------------------------------
;  item shape 5 - "500": 11 x 5 pixels, worth 100 points
;-----------------------------------------------------------------------------
ITEM_5:         .byte $0B,$05,$01       ; width, height, points (also the shape number of the points picture)
                .byte $A8,$A8,$A8       ; 222. 222. 222.
                .byte $80,$88,$88       ; 2... 2.2. 2.2.
                .byte $A8,$88,$88       ; 222. 2.2. 2.2.
                .byte $08,$88,$88       ; ..2. 2.2. 2.2.
                .byte $A8,$A8,$A8       ; 222. 222. 222.

;-----------------------------------------------------------------------------
;  item shape 6: 7 x 6 pixels, worth 100 points
;-----------------------------------------------------------------------------
ITEM_6:         .byte $07,$06,$01       ; width, height, points (also the shape number of the points picture)
                .byte $55,$20           ; 1111 .2..
                .byte $AA,$88           ; 2222 2.2.
                .byte $55,$08           ; 1111 ..2.
                .byte $55,$20           ; 1111 .2..
                .byte $AA,$80           ; 2222 2...
                .byte $14,$00           ; .11. ....

;-----------------------------------------------------------------------------
;  item shape 7: 4 x 11 pixels, worth 200 points
;-----------------------------------------------------------------------------
ITEM_7:         .byte $04,$0B,$02       ; width, height, points (also the shape number of the points picture)
                .byte $28               ; .22.
                .byte $28               ; .22.
                .byte $AA               ; 2222
                .byte $AA               ; 2222
                .byte $AA               ; 2222
                .byte $AA               ; 2222
                .byte $AA               ; 2222
                .byte $AA               ; 2222
                .byte $AA               ; 2222
                .byte $AA               ; 2222
                .byte $AA               ; 2222

;-----------------------------------------------------------------------------
;  item shape 8: 7 x 5 pixels, worth 100 points
;-----------------------------------------------------------------------------
ITEM_8:         .byte $07,$05,$01       ; width, height, points (also the shape number of the points picture)
                .byte $2A,$A0           ; .222 22..
                .byte $AA,$A8           ; 2222 222.
                .byte $66,$64           ; 1212 121.
                .byte $55,$54           ; 1111 111.
                .byte $15,$50           ; .111 11..

;-----------------------------------------------------------------------------
;  item shape 9: 8 x 9 pixels, worth 500 points
;-----------------------------------------------------------------------------
ITEM_9:         .byte $08,$09,$05       ; width, height, points (also the shape number of the points picture)
                .byte $08,$00           ; ..2. ....
                .byte $08,$00           ; ..2. ....
                .byte $08,$01           ; ..2. ...1
                .byte $08,$01           ; ..2. ...1
                .byte $08,$04           ; ..2. ..1.
                .byte $48,$01           ; 1.2. ...1
                .byte $AA,$81           ; 2222 2..1
                .byte $AA,$94           ; 2222 211.
                .byte $AA,$80           ; 2222 2...

;-----------------------------------------------------------------------------
;  item shape 10: 8 x 6 pixels, worth 100 points
;-----------------------------------------------------------------------------
ITEM_10:        .byte $08,$06,$01       ; width, height, points (also the shape number of the points picture)
                .byte $00,$50           ; .... 11..
                .byte $01,$40           ; ...1 1...
                .byte $05,$00           ; ..11 ....
                .byte $AA,$AA           ; 2222 2222
                .byte $AA,$AA           ; 2222 2222
                .byte $2A,$A8           ; .222 222.

;-----------------------------------------------------------------------------
;  item shape 11 - "1100": 12 x 5 pixels, worth 000 points
;-----------------------------------------------------------------------------
ITEM_11:        .byte $0C,$05,$00       ; width, height, points (also the shape number of the points picture)
                .byte $88,$A8,$A8       ; 2.2. 222. 222.
                .byte $88,$88,$88       ; 2.2. 2.2. 2.2.
                .byte $88,$88,$88       ; 2.2. 2.2. 2.2.
                .byte $88,$88,$88       ; 2.2. 2.2. 2.2.
                .byte $88,$A8,$A8       ; 2.2. 222. 222.

;-----------------------------------------------------------------------------
;  item shape 12: 8 x 6 pixels, worth 300 points
;-----------------------------------------------------------------------------
ITEM_12:        .byte $08,$06,$03       ; width, height, points (also the shape number of the points picture)
                .byte $2A,$A8           ; .222 222.
                .byte $AA,$AA           ; 2222 2222
                .byte $15,$54           ; .111 111.
                .byte $15,$54           ; .111 111.
                .byte $AA,$AA           ; 2222 2222
                .byte $2A,$A8           ; .222 222.

;-----------------------------------------------------------------------------
;  item shape 13: 4 x 9 pixels, worth 100 points
;-----------------------------------------------------------------------------
ITEM_13:        .byte $04,$09,$01       ; width, height, points (also the shape number of the points picture)
                .byte $28               ; .22.
                .byte $28               ; .22.
                .byte $AA               ; 2222
                .byte $AA               ; 2222
                .byte $55               ; 1111
                .byte $55               ; 1111
                .byte $55               ; 1111
                .byte $55               ; 1111
                .byte $55               ; 1111

;-----------------------------------------------------------------------------
;  item shape 14: 8 x 12 pixels, worth 400 points
;-----------------------------------------------------------------------------
ITEM_14:        .byte $08,$0C,$04       ; width, height, points (also the shape number of the points picture)
                .byte $5A,$A5           ; 1122 2211
                .byte $16,$94           ; .112 211.
                .byte $05,$50           ; ..11 11..
                .byte $01,$40           ; ...1 1...
                .byte $01,$40           ; ...1 1...
                .byte $02,$A8           ; ...2 222.
                .byte $02,$80           ; ...2 2...
                .byte $01,$40           ; ...1 1...
                .byte $01,$40           ; ...1 1...
                .byte $01,$40           ; ...1 1...
                .byte $01,$40           ; ...1 1...
                .byte $01,$40           ; ...1 1...

;-----------------------------------------------------------------------------
;  item shape 15: 5 x 21 pixels, worth 200 points
;-----------------------------------------------------------------------------
ITEM_15:        .byte $05,$15,$02       ; width, height, points (also the shape number of the points picture)
                .byte $2A,$00           ; .222 ....
                .byte $80,$80           ; 2... 2...
                .byte $22,$00           ; .2.2 ....
                .byte $08,$00           ; ..2. ....
                .byte $04,$00           ; ..1. ....
                .byte $04,$00           ; ..1. ....
                .byte $04,$00           ; ..1. ....
                .byte $04,$00           ; ..1. ....
                .byte $04,$00           ; ..1. ....
                .byte $04,$00           ; ..1. ....
                .byte $04,$00           ; ..1. ....
                .byte $04,$00           ; ..1. ....
                .byte $04,$00           ; ..1. ....
                .byte $04,$00           ; ..1. ....
                .byte $04,$00           ; ..1. ....
                .byte $15,$00           ; .111 ....
                .byte $55,$40           ; 1111 1...
                .byte $55,$40           ; 1111 1...
                .byte $55,$40           ; 1111 1...
                .byte $15,$00           ; .111 ....
                .byte $04,$00           ; ..1. ....

;-----------------------------------------------------------------------------
;  item shape 16: 10 x 14 pixels, worth 200 points
;-----------------------------------------------------------------------------
ITEM_16:        .byte $0A,$0E,$02       ; width, height, points (also the shape number of the points picture)
                .byte $00,$A0,$00       ; .... 22.. ....
                .byte $2A,$AA,$80       ; .222 2222 2...
                .byte $28,$A2,$80       ; .22. 22.2 2...
                .byte $80,$50,$20       ; 2... 11.. .2..
                .byte $00,$50,$00       ; .... 11.. ....
                .byte $00,$50,$00       ; .... 11.. ....
                .byte $00,$50,$00       ; .... 11.. ....
                .byte $00,$50,$00       ; .... 11.. ....
                .byte $00,$50,$00       ; .... 11.. ....
                .byte $00,$50,$00       ; .... 11.. ....
                .byte $00,$50,$00       ; .... 11.. ....
                .byte $00,$50,$00       ; .... 11.. ....
                .byte $00,$50,$00       ; .... 11.. ....
                .byte $00,$50,$00       ; .... 11.. ....

;-----------------------------------------------------------------------------
;  item shape 17: 6 x 13 pixels, worth 200 points
;-----------------------------------------------------------------------------
ITEM_17:        .byte $06,$0D,$02       ; width, height, points (also the shape number of the points picture)
                .byte $20,$80           ; .2.. 2...
                .byte $A0,$A0           ; 22.. 22..
                .byte $80,$20           ; 2... .2..
                .byte $80,$20           ; 2... .2..
                .byte $2A,$80           ; .222 2...
                .byte $0A,$00           ; ..22 ....
                .byte $20,$80           ; .2.. 2...
                .byte $80,$20           ; 2... .2..
                .byte $80,$20           ; 2... .2..
                .byte $80,$20           ; 2... .2..
                .byte $80,$20           ; 2... .2..
                .byte $80,$20           ; 2... .2..
                .byte $80,$20           ; 2... .2..

;-----------------------------------------------------------------------------
;  item shape 18: 8 x 12 pixels, worth 300 points
;-----------------------------------------------------------------------------
ITEM_18:        .byte $08,$0C,$03       ; width, height, points (also the shape number of the points picture)
                .byte $02,$AA           ; ...2 2222
                .byte $0A,$AA           ; ..22 2222
                .byte $28,$5A           ; .22. 1122
                .byte $A0,$50           ; 22.. 11..
                .byte $00,$50           ; .... 11..
                .byte $00,$50           ; .... 11..
                .byte $00,$50           ; .... 11..
                .byte $00,$50           ; .... 11..
                .byte $00,$50           ; .... 11..
                .byte $00,$50           ; .... 11..
                .byte $00,$50           ; .... 11..
                .byte $00,$50           ; .... 11..

;-----------------------------------------------------------------------------
;  item shape 19: 8 x 6 pixels, worth 100 points
;-----------------------------------------------------------------------------
ITEM_19:        .byte $08,$06,$01       ; width, height, points (also the shape number of the points picture)
                .byte $2A,$80           ; .222 2...
                .byte $80,$20           ; 2... .2..
                .byte $80,$20           ; 2... .2..
                .byte $20,$80           ; .2.. 2...
                .byte $AA,$A8           ; 2222 222.
                .byte $AA,$AA           ; 2222 2222

;-----------------------------------------------------------------------------
;  item shape 20: 8 x 4 pixels, worth 100 points
;-----------------------------------------------------------------------------
ITEM_20:        .byte $08,$04,$01       ; width, height, points (also the shape number of the points picture)
                .byte $2A,$A8           ; .222 222.
                .byte $82,$82           ; 2..2 2..2
                .byte $82,$82           ; 2..2 2..2
                .byte $28,$28           ; .22. .22.

;-----------------------------------------------------------------------------
;  item shape 21: 8 x 17 pixels, worth 400 points
;-----------------------------------------------------------------------------
ITEM_21:        .byte $08,$11,$04       ; width, height, points (also the shape number of the points picture)
                .byte $00,$20           ; .... .2..
                .byte $00,$A8           ; .... 222.
                .byte $16,$AA           ; .112 2222
                .byte $AA,$AA           ; 2222 2222
                .byte $AA,$AA           ; 2222 2222
                .byte $AA,$AA           ; 2222 2222
                .byte $AA,$A8           ; 2222 222.
                .byte $14,$20           ; .11. .2..
                .byte $14,$00           ; .11. ....
                .byte $14,$00           ; .11. ....
                .byte $14,$00           ; .11. ....
                .byte $14,$00           ; .11. ....
                .byte $14,$00           ; .11. ....
                .byte $14,$00           ; .11. ....
                .byte $14,$00           ; .11. ....
                .byte $14,$00           ; .11. ....
                .byte $14,$00           ; .11. ....

;-----------------------------------------------------------------------------
;  item shape 22: 8 x 4 pixels, worth 200 points
;-----------------------------------------------------------------------------
ITEM_22:        .byte $08,$04,$02       ; width, height, points (also the shape number of the points picture)
                .byte $0A,$A0           ; ..22 22..
                .byte $5A,$A5           ; 1122 2211
                .byte $5A,$A5           ; 1122 2211
                .byte $0A,$A0           ; ..22 22..

;-----------------------------------------------------------------------------
;  item shape 23: 8 x 12 pixels, worth 300 points
;-----------------------------------------------------------------------------
ITEM_23:        .byte $08,$0C,$03       ; width, height, points (also the shape number of the points picture)
                .byte $02,$80           ; ...2 2...
                .byte $22,$88           ; .2.2 2.2.
                .byte $22,$88           ; .2.2 2.2.
                .byte $22,$88           ; .2.2 2.2.
                .byte $55,$55           ; 1111 1111
                .byte $55,$55           ; 1111 1111
                .byte $AA,$AA           ; 2222 2222
                .byte $55,$55           ; 1111 1111
                .byte $55,$55           ; 1111 1111
                .byte $AA,$AA           ; 2222 2222
                .byte $55,$55           ; 1111 1111
                .byte $55,$55           ; 1111 1111

;-----------------------------------------------------------------------------
;  item shape 24: 10 x 12 pixels, worth 300 points
;-----------------------------------------------------------------------------
ITEM_24:        .byte $0A,$0C,$03       ; width, height, points (also the shape number of the points picture)
                .byte $00,$02,$00       ; .... ...2 ....
                .byte $08,$0A,$80       ; ..2. ..22 2...
                .byte $2A,$29,$A0       ; .222 .221 22..
                .byte $A6,$0A,$80       ; 2212 ..22 2...
                .byte $29,$12,$00       ; .221 .1.2 ....
                .byte $09,$40,$00       ; ..21 1... ....
                .byte $01,$40,$00       ; ...1 1... ....
                .byte $2A,$A8,$00       ; .222 222. ....
                .byte $2A,$A8,$00       ; .222 222. ....
                .byte $0A,$A0,$00       ; ..22 22.. ....
                .byte $0A,$A0,$00       ; ..22 22.. ....
                .byte $0A,$A0,$00       ; ..22 22.. ....

;-----------------------------------------------------------------------------
;  item shape 25: 11 x 8 pixels, worth 200 points
;-----------------------------------------------------------------------------
ITEM_25:        .byte $0B,$08,$02       ; width, height, points (also the shape number of the points picture)
                .byte $05,$50,$00       ; ..11 11.. ....
                .byte $04,$10,$00       ; ..1. .1.. ....
                .byte $10,$04,$28       ; .1.. ..1. .22.
                .byte $2A,$A8,$A0       ; .222 222. 22..
                .byte $AA,$AA,$80       ; 2222 2222 2...
                .byte $AA,$AA,$00       ; 2222 2222 ....
                .byte $AA,$AA,$00       ; 2222 2222 ....
                .byte $2A,$A8,$00       ; .222 222. ....

;-----------------------------------------------------------------------------
;  item shape 26 - the "BF" (Big Five) logo: 9 x 7 pixels, worth 1100 points
;-----------------------------------------------------------------------------
ITEM_26:        .byte $09,$07,$0B       ; width, height, points (also the shape number of the points picture)
                .byte $A8,$3F,$C0       ; 222. .333 3...
                .byte $82,$30,$00       ; 2..2 .3.. ....
                .byte $A8,$30,$00       ; 222. .3.. ....
                .byte $82,$3F,$00       ; 2..2 .333 ....
                .byte $82,$30,$00       ; 2..2 .3.. ....
                .byte $82,$30,$00       ; 2..2 .3.. ....
                .byte $A8,$30,$00       ; 222. .3.. ....

;-----------------------------------------------------------------------------
;  item shape 27: 9 x 9 pixels, worth 200 points
;-----------------------------------------------------------------------------
ITEM_27:        .byte $09,$09,$02       ; width, height, points (also the shape number of the points picture)
                .byte $00,$01,$00       ; .... ...1 ....
                .byte $00,$08,$00       ; .... ..2. ....
                .byte $00,$08,$00       ; .... ..2. ....
                .byte $00,$08,$00       ; .... ..2. ....
                .byte $00,$08,$00       ; .... ..2. ....
                .byte $10,$08,$00       ; .1.. ..2. ....
                .byte $44,$08,$00       ; 1.1. ..2. ....
                .byte $41,$04,$00       ; 1..1 ..1. ....
                .byte $15,$55,$40       ; .111 1111 1...

;-----------------------------------------------------------------------------
;  item shape 28: 11 x 10 pixels, worth 300 points
;-----------------------------------------------------------------------------
ITEM_28:        .byte $0B,$0A,$03       ; width, height, points (also the shape number of the points picture)
                .byte $AA,$AA,$A8       ; 2222 2222 222.
                .byte $AA,$AA,$A0       ; 2222 2222 22..
                .byte $AA,$AA,$80       ; 2222 2222 2...
                .byte $AA,$A0,$00       ; 2222 22.. ....
                .byte $A2,$A0,$00       ; 22.2 22.. ....
                .byte $02,$A0,$00       ; ...2 22.. ....
                .byte $02,$A0,$00       ; ...2 22.. ....
                .byte $02,$A0,$00       ; ...2 22.. ....
                .byte $2A,$AA,$A0       ; .222 2222 22..
                .byte $AA,$AA,$A8       ; 2222 2222 222.

;-----------------------------------------------------------------------------
;  item shape 29: 9 x 20 pixels, worth 500 points
;-----------------------------------------------------------------------------
ITEM_29:        .byte $09,$14,$05       ; width, height, points (also the shape number of the points picture)
                .byte $10,$01,$00       ; .1.. ...1 ....
                .byte $10,$01,$00       ; .1.. ...1 ....
                .byte $10,$41,$00       ; .1.. 1..1 ....
                .byte $10,$41,$00       ; .1.. 1..1 ....
                .byte $10,$41,$00       ; .1.. 1..1 ....
                .byte $10,$41,$00       ; .1.. 1..1 ....
                .byte $A8,$4A,$80       ; 222. 1.22 2...
                .byte $20,$42,$00       ; .2.. 1..2 ....
                .byte $22,$A2,$00       ; .2.2 22.2 ....
                .byte $20,$82,$00       ; .2.. 2..2 ....
                .byte $20,$82,$00       ; .2.. 2..2 ....
                .byte $20,$82,$00       ; .2.. 2..2 ....
                .byte $0A,$A8,$00       ; ..22 222. ....
                .byte $02,$A0,$00       ; ...2 22.. ....
                .byte $00,$80,$00       ; .... 2... ....
                .byte $00,$80,$00       ; .... 2... ....
                .byte $00,$80,$00       ; .... 2... ....
                .byte $00,$80,$00       ; .... 2... ....
                .byte $02,$A0,$00       ; ...2 22.. ....
                .byte $0A,$A8,$00       ; ..22 222. ....

;-----------------------------------------------------------------------------
;  item shape 30: 9 x 11 pixels, worth 200 points
;-----------------------------------------------------------------------------
ITEM_30:        .byte $09,$0B,$02       ; width, height, points (also the shape number of the points picture)
                .byte $2A,$AA,$00       ; .222 2222 ....
                .byte $88,$88,$80       ; 2.2. 2.2. 2...
                .byte $20,$82,$00       ; .2.. 2..2 ....
                .byte $02,$A0,$00       ; ...2 22.. ....
                .byte $02,$A0,$00       ; ...2 22.. ....
                .byte $02,$A0,$00       ; ...2 22.. ....
                .byte $02,$A0,$00       ; ...2 22.. ....
                .byte $00,$80,$00       ; .... 2... ....
                .byte $00,$80,$00       ; .... 2... ....
                .byte $00,$80,$00       ; .... 2... ....
                .byte $00,$80,$00       ; .... 2... ....

;-----------------------------------------------------------------------------
;  item shape 31: 7 x 11 pixels, worth 300 points
;-----------------------------------------------------------------------------
ITEM_31:        .byte $07,$0B,$03       ; width, height, points (also the shape number of the points picture)
                .byte $2A,$A0           ; .222 22..
                .byte $02,$00           ; ...2 ....
                .byte $02,$00           ; ...2 ....
                .byte $22,$20           ; .2.2 .2..
                .byte $22,$20           ; .2.2 .2..
                .byte $AA,$A8           ; 2222 222.
                .byte $AA,$A8           ; 2222 222.
                .byte $AA,$A8           ; 2222 222.
                .byte $AA,$A8           ; 2222 222.
                .byte $AA,$A8           ; 2222 222.
                .byte $AA,$A8           ; 2222 222.

;-----------------------------------------------------------------------------
;  item shape 32: 11 x 11 pixels, worth 500 points
;-----------------------------------------------------------------------------
ITEM_32:        .byte $0B,$0B,$05       ; width, height, points (also the shape number of the points picture)
                .byte $AA,$AA,$A8       ; 2222 2222 222.
                .byte $AA,$9A,$A8       ; 2222 2122 222.
                .byte $AA,$56,$A8       ; 2222 1112 222.
                .byte $A9,$99,$A8       ; 2221 2121 222.
                .byte $A9,$9A,$A8       ; 2221 2122 222.
                .byte $AA,$56,$A8       ; 2222 1112 222.
                .byte $AA,$99,$A8       ; 2222 2121 222.
                .byte $A9,$99,$A8       ; 2221 2121 222.
                .byte $AA,$56,$A8       ; 2222 1112 222.
                .byte $AA,$9A,$A8       ; 2222 2122 222.
                .byte $AA,$AA,$A8       ; 2222 2222 222.

;-----------------------------------------------------------------------------
;  item shape 33 - goblet (poisoned on station 5): 7 x 9 pixels, worth 200 points
;-----------------------------------------------------------------------------
ITEM_33:        .byte $07,$09,$02       ; width, height, points (also the shape number of the points picture)
                .byte $95,$58           ; 2111 112.
                .byte $25,$60           ; .211 12..
                .byte $0A,$80           ; ..22 2...
                .byte $02,$00           ; ...2 ....
                .byte $02,$00           ; ...2 ....
                .byte $02,$00           ; ...2 ....
                .byte $02,$00           ; ...2 ....
                .byte $0A,$80           ; ..22 2...
                .byte $2A,$A0           ; .222 22..

;-----------------------------------------------------------------------------
;  item shape 34 - TNT, 3 tons: 7 x 15 pixels, worth 300 points
;-----------------------------------------------------------------------------
ITEM_34:        .byte $07,$0F,$03       ; width, height, points (also the shape number of the points picture)
                .byte $02,$00           ; ...2 ....
                .byte $02,$00           ; ...2 ....
                .byte $0A,$80           ; ..22 2...
                .byte $0A,$80           ; ..22 2...
                .byte $0A,$80           ; ..22 2...
                .byte $0A,$80           ; ..22 2...
                .byte $0A,$80           ; ..22 2...
                .byte $00,$00           ; .... ....
                .byte $20,$20           ; .2.. .2..
                .byte $20,$20           ; .2.. .2..
                .byte $A8,$A8           ; 222. 222.
                .byte $A8,$A8           ; 222. 222.
                .byte $A8,$A8           ; 222. 222.
                .byte $A8,$A8           ; 222. 222.
                .byte $A8,$A8           ; 222. 222.

;-----------------------------------------------------------------------------
;  item shape 35 - TNT, 2 tons: 7 x 7 pixels, worth 200 points
;-----------------------------------------------------------------------------
ITEM_35:        .byte $07,$07,$02       ; width, height, points (also the shape number of the points picture)
                .byte $20,$20           ; .2.. .2..
                .byte $20,$20           ; .2.. .2..
                .byte $A8,$A8           ; 222. 222.
                .byte $A8,$A8           ; 222. 222.
                .byte $A8,$A8           ; 222. 222.
                .byte $A8,$A8           ; 222. 222.
                .byte $A8,$A8           ; 222. 222.

;-----------------------------------------------------------------------------
;  item shape 36 - TNT, 1 ton: 5 x 7 pixels, worth 100 points
;-----------------------------------------------------------------------------
ITEM_36:        .byte $05,$07,$01       ; width, height, points (also the shape number of the points picture)
                .byte $02,$00           ; ...2 ....
                .byte $02,$00           ; ...2 ....
                .byte $0A,$80           ; ..22 2...
                .byte $0A,$80           ; ..22 2...
                .byte $0A,$80           ; ..22 2...
                .byte $0A,$80           ; ..22 2...
                .byte $0A,$80           ; ..22 2...

;-----------------------------------------------------------------------------
;  station 1 (The Mine Shaft) mutants: 8 records of 11 bytes in the MUT_TAB layout; the y, step
;  timer, patrol length and colour timer are re-read from here while playing.
;-----------------------------------------------------------------------------
MUTANTS_1:      .byte $3D,$26,$01,$00,$04,$02,$32,$01,$07,$32,$00
                .byte $99,$26,$03,$00,$03,$02,$22,$FF,$05,$3C,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $41,$8A,$00,$00,$02,$FE,$34,$01,$08,$28,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $AF,$B5,$03,$00,$03,$02,$7F,$FF,$05,$46,$00

;-----------------------------------------------------------------------------
;  station 2 (The Slides) mutants: 8 records of 11 bytes in the MUT_TAB layout; the y, step
;  timer, patrol length and colour timer are re-read from here while playing.
;-----------------------------------------------------------------------------
MUTANTS_2:      .byte $41,$11,$02,$00,$02,$02,$2B,$01,$05,$1E,$00
                .byte $A7,$11,$01,$00,$04,$FE,$24,$FF,$06,$14,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $AA,$48,$00,$00,$02,$02,$04,$01,$06,$38,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $4B,$B5,$03,$00,$04,$02,$13,$01,$07,$2C,$00
                .byte $C3,$B5,$00,$00,$03,$FE,$45,$FF,$05,$54,$00

;-----------------------------------------------------------------------------
;  station 3 (The Transporters) mutants: 8 records of 11 bytes in the MUT_TAB layout; the y, step
;  timer, patrol length and colour timer are re-read from here while playing.
;-----------------------------------------------------------------------------
MUTANTS_3:      .byte $4B,$28,$01,$00,$04,$FE,$20,$01,$05,$1E,$00
                .byte $96,$28,$03,$00,$02,$02,$12,$FF,$08,$1E,$00
                .byte $36,$43,$00,$00,$03,$FE,$1F,$01,$06,$46,$00
                .byte $A4,$45,$02,$00,$02,$FE,$20,$01,$05,$5A,$00
                .byte $51,$77,$00,$00,$04,$02,$11,$01,$08,$1E,$00
                .byte $91,$73,$03,$00,$02,$FE,$2D,$01,$06,$50,$00
                .byte $45,$B5,$01,$00,$03,$02,$84,$01,$07,$0A,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00

;-----------------------------------------------------------------------------
;  station 4 (The Lillipads) mutants: 8 records of 11 bytes in the MUT_TAB layout; the y, step
;  timer, patrol length and colour timer are re-read from here while playing.
;-----------------------------------------------------------------------------
MUTANTS_4:      .byte $3C,$11,$00,$00,$04,$FE,$3C,$01,$05,$28,$00
                .byte $BB,$11,$03,$00,$03,$02,$3B,$FF,$08,$05,$00
                .byte $6F,$50,$01,$00,$02,$FE,$0B,$01,$07,$46,$00
                .byte $A7,$48,$02,$00,$03,$02,$08,$FF,$06,$64,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $B5,$86,$01,$00,$03,$FE,$07,$FF,$05,$82,$00
                .byte $62,$A3,$01,$00,$03,$02,$10,$01,$07,$1E,$00
                .byte $C7,$B5,$02,$00,$04,$FE,$97,$FF,$05,$3C,$00

;-----------------------------------------------------------------------------
;  station 5 (Advanced Lillipads) mutants: 8 records of 11 bytes in the MUT_TAB layout; the y, step
;  timer, patrol length and colour timer are re-read from here while playing.
;-----------------------------------------------------------------------------
MUTANTS_5:      .byte $38,$13,$01,$00,$02,$FE,$40,$01,$05,$28,$00
                .byte $C4,$13,$03,$00,$03,$02,$44,$FF,$07,$50,$00
                .byte $36,$4E,$00,$00,$03,$02,$08,$01,$06,$3C,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $40,$B5,$01,$00,$04,$FE,$40,$01,$05,$14,$00
                .byte $81,$B5,$03,$00,$03,$02,$47,$01,$07,$1E,$00

;-----------------------------------------------------------------------------
;  station 6 (Radioactive Waste) mutants: 8 records of 11 bytes in the MUT_TAB layout; the y, step
;  timer, patrol length and colour timer are re-read from here while playing.
;-----------------------------------------------------------------------------
MUTANTS_6:      .byte $34,$13,$01,$00,$03,$FE,$10,$01,$05,$3C,$00
                .byte $B8,$13,$03,$00,$02,$02,$10,$01,$07,$1E,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $65,$71,$00,$00,$04,$FE,$04,$01,$06,$0A,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $C6,$9B,$01,$00,$05,$02,$05,$01,$06,$FE,$00

;-----------------------------------------------------------------------------
;  station 7 (Advanced Transporters) mutants: 8 records of 11 bytes in the MUT_TAB layout; the y, step
;  timer, patrol length and colour timer are re-read from here while playing.
;-----------------------------------------------------------------------------
MUTANTS_7:      .byte $80,$28,$00,$00,$03,$FE,$0D,$01,$06,$05,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $4C,$86,$02,$00,$02,$02,$14,$FF,$06,$1E,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $4F,$B5,$01,$00,$04,$FE,$31,$01,$05,$5A,$00
                .byte $38,$B5,$02,$00,$03,$02,$47,$01,$08,$C8,$00

;-----------------------------------------------------------------------------
;  station 8 (The Lift) mutants: 8 records of 11 bytes in the MUT_TAB layout; the y, step
;  timer, patrol length and colour timer are re-read from here while playing.
;-----------------------------------------------------------------------------
MUTANTS_8:      .byte $33,$14,$00,$00,$03,$02,$57,$01,$03,$1E,$00
                .byte $C6,$14,$02,$00,$04,$FE,$46,$FF,$02,$3C,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $32,$50,$00,$00,$02,$02,$2A,$01,$04,$5A,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $38,$6E,$00,$00,$04,$02,$20,$01,$05,$78,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $50,$9C,$02,$00,$05,$FE,$19,$FF,$01,$96,$00

;-----------------------------------------------------------------------------
;  station 9 (The Pulverizers) mutants: 8 records of 11 bytes in the MUT_TAB layout; the y, step
;  timer, patrol length and colour timer are re-read from here while playing.
;-----------------------------------------------------------------------------
MUTANTS_9:      .byte $32,$10,$00,$00,$02,$02,$12,$01,$03,$01,$00
                .byte $44,$28,$02,$00,$03,$FE,$12,$FF,$03,$02,$00
                .byte $32,$40,$00,$00,$04,$02,$12,$01,$03,$03,$00
                .byte $44,$58,$02,$00,$02,$FE,$12,$FF,$03,$04,$00
                .byte $32,$70,$00,$00,$03,$02,$12,$01,$03,$05,$00
                .byte $44,$88,$02,$00,$04,$FE,$12,$FF,$03,$06,$00
                .byte $34,$B5,$00,$00,$03,$02,$11,$01,$06,$04,$00
                .byte $BC,$B5,$02,$00,$03,$FE,$60,$FF,$08,$04,$00

;-----------------------------------------------------------------------------
;  station 10 (The Cannon) mutants: 8 records of 11 bytes in the MUT_TAB layout; the y, step
;  timer, patrol length and colour timer are re-read from here while playing.
;-----------------------------------------------------------------------------
MUTANTS_10:     .byte $31,$18,$00,$00,$02,$02,$4B,$01,$07,$03,$00
                .byte $C4,$18,$02,$00,$04,$FE,$28,$FF,$06,$02,$00
                .byte $7D,$42,$02,$00,$02,$02,$4B,$FF,$08,$03,$00
                .byte $9D,$42,$00,$00,$04,$FE,$2C,$01,$07,$03,$00
                .byte $7E,$6C,$02,$00,$02,$02,$16,$FF,$0A,$05,$00
                .byte $9C,$6C,$00,$00,$04,$FE,$2A,$01,$09,$06,$00
                .byte $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00
                .byte $00

;-----------------------------------------------------------------------------
;  station 1 (The Mine Shaft) girders: sections, x, y - three lists: sloping down, sloping up, flat
;-----------------------------------------------------------------------------
GIRDERS_1:      .byte $12,$0C,$48
                .byte $11,$50,$70
                .byte $12,$48,$95
                .byte $00               ; end of the down-sloping girders
                .byte $10,$54,$58
                .byte $0D,$1C,$7D
                .byte $08,$4C,$B4
                .byte $04,$0C,$B8
                .byte $00               ; end of the up-sloping girders
                .byte $24,$08,$30
                .byte $12,$00,$94
                .byte $0C,$1C,$B5
                .byte $0D,$6C,$AD
                .byte $02,$08,$82
                .byte $00               ; end of the flat girders

;-----------------------------------------------------------------------------
;  station 1 (The Mine Shaft) ladders: height, x, y, style
;-----------------------------------------------------------------------------
LADDERS_1:      .byte $1C,$5C,$35,$04
                .byte $18,$B0,$35,$04
                .byte $14,$7E,$5D,$04
                .byte $19,$64,$7B,$03
                .byte $23,$A8,$7F,$02
                .byte $1C,$52,$99,$04
                .byte $0D,$9E,$B2,$03

;-----------------------------------------------------------------------------
;  station 2 (The Slides) girders: sections, x, y - three lists: sloping down, sloping up, flat
;-----------------------------------------------------------------------------
GIRDERS_2:      .byte $00               ; end of list; end of the down-sloping girders
                .byte $00               ; end of the up-sloping girders
                .byte $28,$00,$1B
                .byte $07,$00,$35
                .byte $07,$28,$35
                .byte $14,$50,$35
                .byte $08,$00,$67
                .byte $0A,$2C,$6A
                .byte $10,$60,$69
                .byte $09,$0E,$9E
                .byte $19,$3B,$9C
                .byte $02,$7D,$52
                .byte $00               ; end of the flat girders

;-----------------------------------------------------------------------------
;  station 2 (The Slides) ladders: height, x, y, style
;-----------------------------------------------------------------------------
LADDERS_2:      .byte $15,$3A,$20,$01
                .byte $15,$62,$20,$01
                .byte $15,$89,$20,$01
                .byte $15,$BA,$20,$01
                .byte $2D,$32,$3A,$01
                .byte $32,$3E,$6C,$02
                .byte $2E,$AA,$6E,$02
                .byte $1E,$75,$A1,$02
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 2 (The Slides) slides: rows, x, y, step
;-----------------------------------------------------------------------------
SLIDES_2:       .byte $35,$A8,$20,$FF
                .byte $32,$5F,$55,$01
                .byte $1A,$C8,$06,$00
                .byte $1D,$C8,$20,$FF
                .byte $17,$AD,$3D,$01
                .byte $33,$C2,$54,$00
                .byte $23,$C2,$87,$FF

;-----------------------------------------------------------------------------
;  station 3 (The Transporters) girders: sections, x, y - three lists: sloping down, sloping up, flat
;-----------------------------------------------------------------------------
GIRDERS_3:      .byte $00               ; end of list; end of the down-sloping girders
                .byte $00               ; end of the up-sloping girders
                .byte $24,$08,$32
                .byte $0A,$04,$4D
                .byte $0C,$37,$61
                .byte $0A,$74,$4F
                .byte $0B,$0D,$81
                .byte $06,$3F,$90
                .byte $0D,$62,$7D
                .byte $07,$04,$9D
                .byte $06,$24,$A2
                .byte $07,$57,$A2
                .byte $06,$7D,$A1
                .byte $00               ; end of the flat girders

;-----------------------------------------------------------------------------
;  station 3 (The Transporters) ladders: height, x, y, style
;-----------------------------------------------------------------------------
LADDERS_3:      .byte $16,$52,$37,$03
                .byte $2F,$42,$52,$03
                .byte $1C,$5F,$86,$03
                .byte $1D,$36,$A2,$01
                .byte $29,$A6,$54,$01
                .byte $1F,$B4,$82,$03
                .byte $18,$99,$A7,$01
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 4 (The Lillipads) girders: sections, x, y - three lists: sloping down, sloping up, flat
;-----------------------------------------------------------------------------
GIRDERS_4:      .byte $00               ; end of the down-sloping girders
                .byte $00               ; end of the up-sloping girders
                .byte $22,$0C,$1B
                .byte $0A,$00,$3C
                .byte $07,$00,$4E
                .byte $02,$0C,$85
                .byte $03,$10,$6A
                .byte $05,$15,$9F
                .byte $04,$2F,$3D
                .byte $04,$35,$67
                .byte $04,$28,$74
                .byte $05,$34,$81
                .byte $05,$30,$93
                .byte $06,$32,$AD
                .byte $02,$4E,$32
                .byte $05,$3E,$5A
                .byte $04,$4F,$86
                .byte $03,$54,$B4
                .byte $04,$64,$40
                .byte $05,$55,$4D
                .byte $07,$79,$3C
                .byte $04,$6F,$52
                .byte $04,$85,$5B
                .byte $04,$79,$68
                .byte $04,$63,$73
                .byte $03,$79,$7C
                .byte $03,$6B,$8B
                .byte $04,$7E,$90
                .byte $05,$83,$9D
                .byte $04,$68,$A9
                .byte $00               ; end of the flat girders

;-----------------------------------------------------------------------------
;  station 4 (The Lillipads) ladders: height, x, y, style
;-----------------------------------------------------------------------------
LADDERS_4:      .byte $1C,$46,$20,$04
                .byte $1C,$B6,$20,$04
                .byte $6C,$32,$53,$03

;-----------------------------------------------------------------------------
;  station 5 (Advanced Lillipads) girders: sections, x, y - three lists: sloping down, sloping up, flat
;-----------------------------------------------------------------------------
GIRDERS_5:      .byte $00               ; end of list; end of the down-sloping girders
                .byte $00               ; end of the up-sloping girders
                .byte $24,$08,$1D
                .byte $02,$08,$29
                .byte $02,$08,$35
                .byte $02,$08,$41
                .byte $02,$08,$4E
                .byte $04,$06,$58
                .byte $03,$16,$6D
                .byte $03,$07,$78
                .byte $02,$07,$85
                .byte $03,$11,$91
                .byte $02,$10,$A7
                .byte $02,$21,$54
                .byte $03,$25,$61
                .byte $03,$31,$7A
                .byte $03,$22,$87
                .byte $04,$26,$9E
                .byte $02,$26,$AA
                .byte $04,$49,$59
                .byte $02,$39,$69
                .byte $03,$4D,$79
                .byte $02,$4F,$87
                .byte $02,$4F,$94
                .byte $02,$3E,$A0
                .byte $03,$4B,$AA
                .byte $03,$39,$B5
                .byte $02,$65,$99
                .byte $02,$80,$71
                .byte $02,$7B,$9F
                .byte $02,$98,$29
                .byte $02,$8F,$3F
                .byte $02,$8E,$4B
                .byte $03,$8E,$58
                .byte $02,$90,$67
                .byte $02,$8C,$7B
                .byte $02,$94,$88
                .byte $03,$88,$96
                .byte $02,$91,$A4
                .byte $02,$86,$B0
                .byte $02,$4D,$32
                .byte $02,$4D,$44
                .byte $00               ; end of the flat girders

;-----------------------------------------------------------------------------
;  station 5 (Advanced Lillipads) slides: rows, x, y, step
;-----------------------------------------------------------------------------
SLIDES_5:       .byte $3C,$43,$08,$01
                .byte $27,$58,$08,$01
                .byte $15,$6A,$08,$01
                .byte $15,$7D,$08,$00
                .byte $15,$90,$08,$FF
                .byte $27,$A2,$08,$FF
                .byte $3C,$B7,$08,$FF
                .byte $12,$7D,$1D,$00
                .byte $15,$7D,$2F,$00
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 5 (Advanced Lillipads) moving platforms: timer, width, x, y, travel, speed
;-----------------------------------------------------------------------------
LIFTS_5:        .byte $02,$0E,$59,$65,$25,$01
                .byte $03,$08,$98,$34,$13,$FF
                .byte $01,$0C,$53,$B4,$22,$01

;-----------------------------------------------------------------------------
;  station 6 (Radioactive Waste) girders: sections, x, y - three lists: sloping down, sloping up, flat
;-----------------------------------------------------------------------------
GIRDERS_6:      .byte $00               ; end of list; end of the down-sloping girders
                .byte $00               ; end of the up-sloping girders
                .byte $06,$04,$1D
                .byte $04,$0C,$49
                .byte $02,$11,$98
                .byte $02,$00,$A5
                .byte $02,$00,$B3
                .byte $02,$21,$89
                .byte $03,$35,$7B
                .byte $04,$49,$6C
                .byte $02,$53,$5D
                .byte $02,$55,$4F
                .byte $02,$57,$40
                .byte $03,$3C,$3B
                .byte $02,$54,$26
                .byte $05,$3F,$1D
                .byte $04,$69,$1D
                .byte $03,$68,$34
                .byte $03,$6F,$4E
                .byte $02,$79,$5E
                .byte $03,$68,$70
                .byte $02,$55,$8C
                .byte $02,$6D,$8C
                .byte $03,$87,$98
                .byte $02,$98,$A5
                .byte $02,$98,$B5
                .byte $05,$84,$77
                .byte $05,$8C,$2E
                .byte $06,$88,$1D
                .byte $00               ; end of the flat girders

;-----------------------------------------------------------------------------
;  station 6 (Radioactive Waste) ladders: height, x, y, style
;-----------------------------------------------------------------------------
LADDERS_6:      .byte $27,$3E,$22,$02
                .byte $44,$BE,$33,$04
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 6 (Radioactive Waste) moving platforms: timer, width, x, y, travel, speed
;-----------------------------------------------------------------------------
LIFTS_6:        .byte $04,$06,$1A,$57,$6C,$01
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 7 (Advanced Transporters) girders: sections, x, y - three lists: sloping down, sloping up, flat
;-----------------------------------------------------------------------------
GIRDERS_7:      .byte $03,$4F,$93
                .byte $00               ; end of the down-sloping girders
                .byte $03,$4F,$A7
                .byte $00               ; end of the up-sloping girders
                .byte $07,$08,$32
                .byte $07,$04,$61
                .byte $07,$08,$90
                .byte $05,$50,$32
                .byte $02,$47,$41
                .byte $04,$57,$51
                .byte $05,$39,$5F
                .byte $03,$39,$8E
                .byte $02,$3E,$AC
                .byte $03,$75,$A9
                .byte $04,$90,$A6
                .byte $04,$68,$8D
                .byte $04,$6C,$7F
                .byte $04,$8C,$84
                .byte $02,$96,$75
                .byte $02,$8D,$69
                .byte $02,$81,$5D
                .byte $02,$94,$59
                .byte $02,$81,$4E
                .byte $02,$74,$45
                .byte $02,$94,$33
                .byte $09,$7C,$1E
                .byte $00               ; end of the flat girders

;-----------------------------------------------------------------------------
;  station 7 (Advanced Transporters) moving platforms: timer, width, x, y, travel, speed
;-----------------------------------------------------------------------------
LIFTS_7:        .byte $03,$04,$20,$28,$50,$01
                .byte $04,$05,$1F,$68,$15,$01
                .byte $03,$05,$21,$97,$13,$01
                .byte $04,$05,$27,$B8,$4B,$01
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 7 (Advanced Transporters) slides: rows, x, y, step
;-----------------------------------------------------------------------------
SLIDES_7:       .byte $2D,$40,$1D,$01
                .byte $2E,$6B,$4A,$01
                .byte $33,$BF,$09,$FF
                .byte $33,$8E,$3C,$01
                .byte $15,$B1,$09,$01
                .byte $26,$C4,$1E,$00
                .byte $26,$C4,$44,$FF
                .byte $27,$A0,$6A,$01
                .byte $19,$C5,$91

;-----------------------------------------------------------------------------
;  station 8 (The Lift) girders: sections, x, y - three lists: sloping down, sloping up, flat
;-----------------------------------------------------------------------------
GIRDERS_8:      .byte $00               ; end of the down-sloping girders
                .byte $00               ; end of list; end of the up-sloping girders
                .byte $28,$00,$1E
                .byte $05,$00,$3C
                .byte $0F,$38,$3C
                .byte $0D,$00,$5A
                .byte $05,$8C,$5A
                .byte $0D,$00,$78
                .byte $03,$80,$6C
                .byte $0A,$00,$A6
                .byte $02,$7E,$5A
                .byte $08,$80,$A0
                .byte $00               ; end of the flat girders

;-----------------------------------------------------------------------------
;  station 8 (The Lift) ladders: height, x, y, style
;-----------------------------------------------------------------------------
LADDERS_8:      .byte $19,$3A,$23,$03
                .byte $19,$6A,$23,$03
                .byte $19,$7A,$41,$03
                .byte $0D,$C6,$23,$03
                .byte $22,$C6,$38,$81
                .byte $41,$BE,$5F,$03
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 8 (The Lift) moving platforms: timer, width, x, y, travel, speed
;-----------------------------------------------------------------------------
LIFTS_8:        .byte $01,$33,$02,$AE,$69,$01
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 8 (The Lift) slides: rows, x, y, step
;-----------------------------------------------------------------------------
SLIDES_8:       .byte $1E,$8C,$09,$00
                .byte $1E,$34,$27,$00
                .byte $1E,$98,$27,$01
                .byte $12,$B4,$45,$00
                .byte $2E,$34,$63

;-----------------------------------------------------------------------------
;  station 9 (The Pulverizers) girders: sections, x, y - three lists: sloping down, sloping up, flat
;-----------------------------------------------------------------------------
GIRDERS_9:      .byte $00               ; end of the down-sloping girders
                .byte $00               ; end of list; end of the up-sloping girders
                .byte $07,$00,$1A
                .byte $07,$00,$32
                .byte $07,$00,$4A
                .byte $07,$00,$62
                .byte $07,$00,$7A
                .byte $07,$00,$92
                .byte $07,$84,$1A
                .byte $06,$82,$32
                .byte $05,$82,$4A
                .byte $05,$81,$62
                .byte $06,$84,$7A
                .byte $07,$84,$92
                .byte $00               ; end of the flat girders

;-----------------------------------------------------------------------------
;  station 9 (The Pulverizers) ladders: height, x, y, style
;-----------------------------------------------------------------------------
LADDERS_9:      .byte $13,$C2,$1F,$03
                .byte $13,$BC,$37,$01
                .byte $13,$B8,$4F,$03
                .byte $13,$BB,$67,$01
                .byte $13,$C2,$7F,$03
                .byte $28,$C6,$97,$02
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 9 (The Pulverizers) moving platforms: timer, width, x, y, travel, speed
;-----------------------------------------------------------------------------
LIFTS_9:        .byte $01,$04,$81,$21,$66,$FF
                .byte $01,$04,$7F,$39,$64,$FF
                .byte $01,$04,$7F,$51,$64,$FF
                .byte $01,$04,$7E,$69,$63,$FF
                .byte $01,$04,$81,$81,$66,$FF
                .byte $01,$04,$81,$99,$66,$FF
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 9 (The Pulverizers) slides: rows, x, y, step
;-----------------------------------------------------------------------------
SLIDES_9:       .byte $9E,$4E,$0C,$00
                .byte $86,$4E,$24,$00
                .byte $6E,$4E,$3C,$00
                .byte $56,$4E,$54,$00
                .byte $3E,$4E,$6C,$00
                .byte $26,$4E,$84

;-----------------------------------------------------------------------------
;  station 10 (The Cannon) girders: sections, x, y - three lists: sloping down, sloping up, flat
;-----------------------------------------------------------------------------
GIRDERS_10:     .byte $00               ; end of the down-sloping girders
                .byte $00               ; end of list; end of the up-sloping girders
                .byte $15,$00,$22
                .byte $15,$00,$4C
                .byte $0B,$02,$7C
                .byte $0B,$02,$92
                .byte $0B,$02,$A8
                .byte $02,$2C,$87
                .byte $02,$2C,$9D
                .byte $02,$2B,$B4
                .byte $07,$38,$76
                .byte $0D,$6C,$22
                .byte $0D,$6C,$4C
                .byte $0D,$6C,$76
                .byte $07,$7A,$8E
                .byte $00               ; end of the flat girders

;-----------------------------------------------------------------------------
;  station 10 (The Cannon) ladders: height, x, y, style
;-----------------------------------------------------------------------------
LADDERS_10:     .byte $2C,$BC,$93,$02
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  station 10 (The Cannon) slides: rows, x, y, step
;-----------------------------------------------------------------------------
SLIDES_10:      .byte $2A,$3E,$0D,$01
                .byte $73,$66,$37,$00
                .byte $49,$66,$61,$00
                .byte $6C,$BC,$0D,$00
                .byte $42,$BC,$37,$00
                .byte $18,$BC,$61

;-----------------------------------------------------------------------------
;  station 11 (the credits) girders: sections, x, y - three lists: sloping down, sloping up, flat
;-----------------------------------------------------------------------------
GIRDERS_11:     .byte $00               ; end of the down-sloping girders
                .byte $00               ; end of list; end of the up-sloping girders
                .byte $28,$00,$24
                .byte $05,$00,$45
                .byte $1E,$24,$45
                .byte $04,$00,$76
                .byte $1F,$19,$70
                .byte $08,$75,$94
                .byte $1A,$00,$94
                .byte $02,$00,$94
                .byte $00               ; end of the flat girders

;-----------------------------------------------------------------------------
;  station 11 (the credits) ladders: height, x, y, style
;-----------------------------------------------------------------------------
LADDERS_11:     .byte $1C,$C2,$29,$02
                .byte $2C,$32,$4A,$04
                .byte $1F,$BB,$75,$03
                .byte $26,$32,$99,$02
                .byte $00               ; end of list

;-----------------------------------------------------------------------------
;  SET_VBI - install a vertical-blank interrupt handler.            In: Y/X = handler lo/hi
;
;  The same cartridge runs on the Atari 400/800 and on the Atari 5200, and the two
;  machines dispatch the VBI differently:
;    * 400/800 OS: its NMI routine pushes A, X and Y, then jumps through VVBLKI ($0222).
;    * 5200 BIOS:  jumps through its own VVBLKI ($0202) with nothing saved; Miner points that
;                  at VBI_5200 below, which saves the registers and jumps through VVBLKD
;                  ($0204), the 5200's deferred vector.
;  Writing the handler into both $0222 and $0204 means every handler can end with the same
;  PLA/TAY/PLA/TAX/PLA/RTI sequence (NMI_EXIT) on either machine.
;-----------------------------------------------------------------------------
SET_VBI:        lda #$00                ; disable all NMIs while the vectors are half-written
                sta NMIEN               ; NMIEN = 0
                sty VVBLKD5             ; 5200: deferred VBI vector = handler
                stx VVBLKD5+1
                sty VVBLKI              ; 400/800: VBI vector = handler
                stx VVBLKI+1
                lda #$10                ; 5200: immediate VBI vector -> VBI_5200 ($9210)
                sta VVBLKI5
                lda #$92                ; VVBLKI5+1 = $92
                sta VVBLKI5+1
                sta NMIRES              ; clear any pending NMI status (the value written is irrelevant)
                rts

;-----------------------------------------------------------------------------
;  VBI_5200 - 5200 only: make the BIOS's bare VBI look like the 400/800 OS's.
;  Push A, X, Y exactly as the 400/800 OS does, then continue at the game's handler.
;-----------------------------------------------------------------------------
VBI_5200:       pha                     ; save A
                txa                     ; save X
                pha
                tya                     ; save Y
                pha
                jmp (VVBLKD5)           ; continue at the handler stored by SET_VBI

;-----------------------------------------------------------------------------
;  POLL_KEYS - called at the start of every VBI handler. Reads a key if one was pressed.
;
;  The game never enables POKEY interrupts. Instead it polls the keyboard bit (6) of IRQST
;  each frame: 0 there means a key has been latched in KBCODE. The key is stored in KEYCODE
;  and the IRQ status bit is re-armed by writing IRQEN 0 then $40.
;    400/800: KEYCODE = raw KBCODE (keyboard matrix code, bit 6 = SHIFT, bit 7 = CTRL).
;    5200:    the keypad code (bits 1-4) is translated through KEYPAD_MAP into the 400/800
;             code of the same key, so the rest of the game sees a single keyboard. The
;             keypad's RESET key maps to 0 and restarts the cartridge.
;-----------------------------------------------------------------------------
POLL_KEYS:      ldy #$00                ; Y = 0 for the (pointer),Y register accesses
                lda (pIRQEN),y          ; read IRQST
                and #$40                ; bit 6 = keyboard interrupt status (0 = key pressed)
                bne POLL_DONE           ; no key: return
                lda (pSTIMER),y         ; read the key code
                ldx IS5200              ; which machine?
                beq STORE_KEY           ; 400/800: keep the code as it is
                lsr a                   ; 5200 keypad code is in bits 1-4
                and #$0F
                tax
                lda KEYPAD_MAP,x        ; translate to a 400/800 key code
                beq RESET_5200          ; 0 = RESET key: restart the cartridge
STORE_KEY:      sta KEYCODE             ; remember the key
                tya                     ; IRQEN = 0 then $40: clears the keyboard status bit, ready for the next key
                sta (pIRQEN),y          ; IRQEN = A
                lda #$40                ; IRQEN = $40
                sta (pIRQEN),y          ; IRQEN = A
POLL_DONE:      rts
RESET_5200:     jmp (CART_TRAILER)      ; restart through the cartridge's start vector (= RESTART: the high scores
                                        ;   are kept)

;-----------------------------------------------------------------------------
;  NMI_EXIT - common tail of every interrupt handler: restore Y, X, A and return.
;-----------------------------------------------------------------------------
NMI_EXIT:       pla
                tay                     ; restore Y
                pla
                tax                     ; restore X
                pla                     ; restore A
                rti

;-----------------------------------------------------------------------------
;  KEYPAD_MAP - 5200 keypad code (0-15) -> the 400/800 KBCODE the game expects.
;    code:  0    1    2    3    4     5    6    7    8     9    A    B    C     D    E    F
;    key:   -    #    0    *    RESET 9    8    7    PAUSE 6    5    4    START 3    2    1
;    ->     $FF  $21  $32  $02  $00   $30  $35  $33  $1C   $1B  $1D  $18  $03   $1A  $1E  $1F
;  Digits map to the computer's digit keys, # to the space bar (runs the lift in station 8),
;  PAUSE to ESC (pause), * to $02 and START to $03 (the 5200 stand-ins for SELECT/OPTION and
;  START, see TITLE_LOOP). RESET maps to 0, which POLL_KEYS treats as "restart".
;-----------------------------------------------------------------------------
KEYPAD_MAP:     .byte $FF,$21,$32,$02,$00,$30,$35,$33,$1C,$1B,$1D,$18,$03,$1A,$1E,$1F

;-----------------------------------------------------------------------------
;  SET_DLI - install a display-list-interrupt handler.             In: Y/X = handler lo/hi
;  Written to both the 400/800 vector (VDSLST) and the 5200 one ($0206).
;-----------------------------------------------------------------------------
SET_DLI:        sty VDSLST5             ; 5200 DLI vector
                stx VDSLST5+1
                sty VDSLST              ; 400/800 DLI vector
                stx VDSLST+1
                rts

;-----------------------------------------------------------------------------
;  READ_DIGIT - was a digit key (1-9, 0) pressed?
;  Out: Z clear and A = Y = 1-10 if so ('0' counts as 10), and the key is consumed;
;       Z set and Y = 0 if no key, or a key that is not a digit.
;  KEY_TO_SCREEN converts the key code to a screen code; digits are $10-$19.
;-----------------------------------------------------------------------------
READ_DIGIT:     lda KEYCODE             ; any key waiting?
                cmp #$FF                ; if A == $FF goto NO_DIGIT
                beq NO_DIGIT            ; no
                and #$3F                ; drop SHIFT and CTRL
                tay
                lda KEY_TO_SCREEN,y     ; key code -> screen code
                sec                     ; screen code - $10 = digit value
                sbc #$10
                bne READ_DIGIT_CHK      ; '0'
                lda #$0A                ; counts as 10
READ_DIGIT_CHK: cmp #$0B                ; not a digit at all?
                bcs NO_DIGIT
                ldy #$FF                ; consume the key
                sty KEYCODE
                tay                     ; Y = digit, Z clear
                rts
NO_DIGIT:       ldy #$00                ; Y = 0, Z set
RD_RTS:         rts

;-----------------------------------------------------------------------------
;  CHECK_ZONE_KEY - on the title screens a digit key starts a one-player game at that zone.
;  If a digit was pressed it is saved in START_ZONE and the game starts (via START_GAME_A
;  with A = 0, i.e. not a demo). Otherwise it simply returns.
;-----------------------------------------------------------------------------
CHECK_ZONE_KEY: jsr READ_DIGIT          ; was a digit key (1-9, 0) pressed?
                beq RD_RTS              ; no digit: return
                sty START_ZONE          ; zone to start in
                lda #$00                ; A = 0: DEMO_PTR+1 = 0 = a real game
                jmp START_GAME_A        ; start the game

;-----------------------------------------------------------------------------
;  HW_RESET - silence and blank everything.
;  Writes 0 to every GTIA, POKEY and ANTIC register (256 times over, through the mirrors),
;  turns the POKEY keyboard status back on, forgets any key, selects the ROM font and sets
;  up the serial/keyboard control.
;-----------------------------------------------------------------------------
HW_RESET:       lda #$00                ; no NMIs
                sta NMIEN
                tay                     ; Y = 0
HW_RESET_LOOP:  sta (pHPOSP0),y         ; GTIA register Y (mirrored every 32 bytes)
                sta (pAUDF1),y          ; POKEY register Y (mirrored every 16 bytes)
                sta DMACTL,y            ; ANTIC register Y: DMA off, display list, scroll, NMIEN ...
                iny
                bne HW_RESET_LOOP       ; 256 bytes
                lda #$40                ; IRQEN = $40: allow the keyboard status bit
                sta (pIRQEN),y          ; IRQEN = A
                lda #$FF                ; KEYCODE = none
                sta KEYCODE
                lda FONTPAGE            ; character set = the machine's ROM font
                sta CHBASE
                lda IS5200              ; if IS5200 == 0 goto HW_RESET_800
                beq HW_RESET_800        ; 400/800:
                lda #$04                ; 5200: CONSOL bit 2 enables the controller ports' pot scanning
                sta (pCONSOL),y         ; CONSOL = A
                lda #$02                ; 5200: SKCTL = 2 (keyboard debounce off)
                bne HW_RESET_SKCTL
HW_RESET_800:   lda #$03                ; 400/800: SKCTL = 3 (keyboard scan + debounce enabled)
HW_RESET_SKCTL: sta (pSKCTL),y          ; SKCTL = A
                rts

;-----------------------------------------------------------------------------
;  TITLE_SCREEN - the high-score screen with its ring of "chasing lights".
;
;  Reached after a game ends, after the game-over tune, or by pressing OPTION. It shows the
;  ten best scores inside a frame of 36 '5' characters (taken from the ROM font) whose
;  colours march round the frame. The tricks that make it work:
;
;   * Top and bottom rows: one ANTIC mode 7 line each (20 big characters), held in ROM at
;     $8059 and $801F. The text never moves. HSCROL slides the row by 0-15 colour clocks
;     (two character cells), and each time the scroll wraps the colours rotate one step, so
;     the eye sees a continuous march.
;   * Ten colours on one line: mode 7 gives only four colours (COLPF0-3). A display list
;     interrupt jumps into TITLE_KERNEL, a cycle-counted loop copied to RAM at $0400 that
;     rewrites all four colour registers twice on every scan line: once for the left four
;     '5's and once, half-way across, for the right four. The middle two '5's are players
;     1 and 2, which have their own colour registers. 4 + 2 + 4 = 10 colours.
;   * The kernel must follow the fine scroll, so the two delay instructions (KERNEL_DELAY1
;     before the loop, KERNEL_DELAY2 in it) are patched to a 3-, 4- or 5-cycle opcode (CPX zp / CMP zp,X / ASL zp)
;     to move the colour changes
;     by 6-10 colour clocks. Its STA instructions also get their high bytes (by
;     KERNEL_COLS_TOP only, since both halves share the kernel) patched to the
;     GTIA's page, because GTIA is at $D0xx on the 400/800 but at $C0xx on the 5200.
;   * Left and right columns: players 0 and 3 in double-line resolution. A DLI on every text
;     line recolours them. They move by redrawing into a second P/M buffer and flipping
;     PMBASE between $0400 and $1C00 (double buffering), so no half-drawn frame is seen.
;   * The ten high-score lines get a moving rainbow (one DLI per line), "HIGH SCORES:"
;     pulses in brightness, and "START" blinks in inverse video.
;
;  While it runs it watches for START or the joystick button (start a game), SELECT (one or
;  two players), a digit key (start in that zone), and after 30 seconds starts the demo.
;-----------------------------------------------------------------------------
TITLE_SCREEN:   jsr HW_RESET            ; everything off and silent
                lda TWO_PLAYER          ; number of players shown in "Press START For a 1 Miner Game":
                clc                     ; '1' + TWO_PLAYER
                adc #$11
                sta TEXT_RAM+23         ; the digit sits at TEXT_RAM+23
                ldx #$1B                ; copy the 27 title variables T_SCROLL..T_VOLUME from TITLE_INIT
TS_INIT_LOOP:   lda TITLE_INIT-1,x      ; T_SCROLL-1[X] = TITLE_INIT-1[X]
                sta T_SCROLL-1,x
                dex                     ; loop until X = 0
                bne TS_INIT_LOOP
                jsr CLEAR_PM_BUFS       ; clear both P/M buffers
                jsr DRAW_MID_FIVES      ; put the middle top/bottom '5's into players 1 and 2
                jsr DRAW_COLUMNS        ; draw the side columns into the first buffer
                ldx #$1C                ; next buffer to draw into is $1C00
                stx T_PMPAGE
                ldx #$3E                ; copy the 62-byte colour kernel to RAM at $0400 (it is self-modified)
TS_COPY_KERNEL: lda DTR_GO+7,x          ; $03FF[X] = DTR_GO+7[X]
                sta $03FF,x
                dex                     ; loop until X = 0
                bne TS_COPY_KERNEL
                ldx #>DLI_TOP_ROW       ; first DLI = DLI_TOP_ROW
                ldy #<DLI_TOP_ROW
                jsr SET_DLI             ; install a display-list-interrupt handler
                ldx #$04                ; show P/M buffer $0400 (double-line players: base+$200..$3FF)
                stx PMBASE
                ldy #$00
                lda #$30                ; left column (player 0) at x = $30
                sta (pHPOSP0),y         ; HPOSP0 = A
                lda #$C8                ; right column (player 3) at x = $C8
                sta (pHPOSP3),y         ; HPOSP3 = A
                ldy #<TITLE_VBI         ; VBI = TITLE_VBI
                ldx #>TITLE_VBI
                jsr SET_VBI             ; install a vertical-blank interrupt handler
                lda #$C0                ; enable DLI and VBI
                sta NMIEN
TITLE_LOOP:     lda T_SCROLL            ; wait until the VBI has shown the scroll phase asked for last time
                cmp T_NEWSCROLL         ; if A <> T_NEWSCROLL goto TITLE_LOOP
                bne TITLE_LOOP
                ldx #$04                ; 4 frames per scroll step
TS_FRAME:       lda T_TIMER30           ; T_TIMER30 changes every frame: remember it to spot the next frame
TS_POLL:        pha
                jsr CHECK_ZONE_KEY      ; a digit key starts a game in that zone
                lda T_VOLUME+1          ; START: 5200 keypad START arrives as key code 3
                beq TS_START_800
                lda KEYCODE
                cmp #$03
                jmp TS_START_CHK
TS_START_800:   lda CONSOL              ; 400/800: START key (CONSOL bit 0, 0 = pressed)
                and #$01                ; test bits $01
                beq TS_START_PRESSED    ; pressed
                ldy #$00                ; ... or the joystick button
                lda (pTRIG0),y          ; A = TRIG0
                and #$01
TS_START_CHK:   bne TS_NO_START         ; not pressed
                lda #$FF                ; forget any key
                sta KEYCODE
TS_START_PRESSED:
                lda T_STARTDLY          ; START must have been released for a few frames first
                beq START_GAME_A        ; it was: start a game (A = 0 = not a demo)
                lda #$05                ; still held from before: keep waiting
                sta T_STARTDLY
                bne TS_CHECK_DEMO
TS_DEMO:        lda #$01                ; A = 1: run the demo instead

;-----------------------------------------------------------------------------
;  START_GAME_A - start a game. A = 0 for a real game, A <> 0 for the demo (it becomes
;  DEMO_PTR+1 and is replaced by the real pointer in START_GAME).
;-----------------------------------------------------------------------------
START_GAME_A:   sta DEMO_PTR+1
                jmp START_GAME          ; start a game (DEMO_PTR+1 = 0) or the demo (DEMO_PTR+1 <> 0)
TS_NO_START:    lda T_STARTDLY          ; count the START debounce down while START is up
                beq TS_CHECK_DEMO
                dec T_STARTDLY
TS_CHECK_DEMO:  lda T_DEMOSEC           ; 30 seconds gone? then show the demo
                beq TS_DEMO
                lda T_VOLUME+1          ; SELECT: on the 5200 the * key (code 2)
                beq TS_SELECT_800
                lda KEYCODE
                cmp #$02
                jmp TS_SELECT_CHK
TS_SELECT_800:  lda CONSOL              ; 400/800: SELECT key
                and #$02
TS_SELECT_CHK:  bne TS_SELECT_UP        ; not pressed
                lda #$FF                ; forget any key
                sta KEYCODE
                lda T_SELDLY            ; only act on a new press
                bne TS_SELECT_HELD
                lda #$01                ; TWO_PLAYER = 1 - TWO_PLAYER
                sec
                sbc TWO_PLAYER
                sta TWO_PLAYER
                clc                     ; and update the digit on screen
                adc #$11
                sta TEXT_RAM+23
TS_SELECT_HELD: lda #$FF                ; hold-off while SELECT stays down
                sta T_SELDLY
TS_SELECT_UP:   lda T_SELDLY            ; if T_SELDLY == 0 goto TS_NEXT_FRAME
                beq TS_NEXT_FRAME
                dec T_SELDLY
TS_NEXT_FRAME:  pla                     ; has a frame gone by?
                cmp T_TIMER30           ; if A == T_TIMER30 goto TS_POLL_J
                beq TS_POLL_J           ; no: keep polling
                dex                     ; 4 frames?
                bne TS_FRAME_J
                lda T_SCROLL            ; next scroll phase = (T_SCROLL + 2) and 15
                clc
                adc #$02
                and #$0F
                sta T_NEXT
                jsr DRAW_COLUMNS        ; draw the side columns for it in the hidden buffer
                lda #$20                ; flip buffers: $1C <-> $04
                sec
                sbc T_PMPAGE
                sta T_PMPAGE
                lda T_NEXT              ; ask the VBI to show it
                sta T_NEWSCROLL
                jmp TITLE_LOOP
TS_POLL_J:      jmp TS_POLL
TS_FRAME_J:     jmp TS_FRAME

;-----------------------------------------------------------------------------
;  SET_FINE_SCROLL - set HSCROL and patch the kernel's delay to match.     In: A = 0-15
;  A/2 = 0     -> $E4 CPX zp      (3 cycles)
;  A/2 = 1-4   -> $D5 CMP zp,X    (4 cycles)
;  A/2 = 5-7   -> $06 ASL zp      (5 cycles; shifts T_TMP, which is harmless)
;  The opcode goes into both delay slots of TITLE_KERNEL.
;-----------------------------------------------------------------------------
SET_FINE_SCROLL:
                sta HSCROL              ; fine scroll
                ldx #$E4
                lsr a
                beq SFS_PATCH
                ldx #$D5
                cmp #$05                ; if A < 5 goto SFS_PATCH
                bcc SFS_PATCH
                ldx #$06
SFS_PATCH:      stx KERNEL_DELAY2       ; patch the delay opcode inside the loop
                stx KERNEL_DELAY1       ; ... and the one before the first line
                rts

;-----------------------------------------------------------------------------
;  CLEAR_PM_BUFS - zero 1K at $0400 and 1K at $1C00 (the two P/M buffers).
;-----------------------------------------------------------------------------
CLEAR_PM_BUFS:  ldx #$04                ; $0400
                stx T_PTR+1
                ldx #$00
                stx T_PTR
                ldx #$FC                ; count $FC00 up to $10000 = 1024 bytes
                ldy #$00
                jsr CLEAR_MEM           ; zero memory from (T_PTR) for -(T_CNT) bytes
                ldx #$1C                ; $1C00
                stx T_PTR+1
                ldx #$00
                stx T_PTR
                ldx #$FC
                ldy #$00

;-----------------------------------------------------------------------------
;  CLEAR_MEM - zero memory from (T_PTR) for -(T_CNT) bytes.     In: X/Y = negative count hi/lo
;-----------------------------------------------------------------------------
CLEAR_MEM:      stx T_CNT2
                sty T_CNT
                lda #$00
                tay
CLEAR_MEM_LOOP: sta (T_PTR),y
                inc T_PTR               ; advance the pointer
                bne CLEAR_MEM_CNT
                inc T_PTR+1
CLEAR_MEM_CNT:  inc T_CNT               ; count up to zero
                bne CLEAR_MEM_LOOP
                inc T_CNT2              ; T_CNT2 += 1, until 0
                bne CLEAR_MEM_LOOP
                rts

;-----------------------------------------------------------------------------
;  DRAW_MID_FIVES - copy the '5' glyph from the ROM font into players 1 and 2 of both P/M
;  buffers, at the heights of the top and bottom rows. These are the two middle lights of
;  each row (they need colours of their own; see TITLE_SCREEN).
;-----------------------------------------------------------------------------
DRAW_MID_FIVES: lda FONTPAGE            ; T_PTR = font + 8 * $15 = the '5' glyph
                sta T_PTR+1
                lda #$A8                ; T_PTR = $A8
                sta T_PTR
                ldx #$16                ; player 1, top row
                jsr COPY_GLYPH          ; copy 6 rows of the '5' glyph into both P/M buffers at row X
                ldx #$6E                ; player 1, bottom row
                jsr COPY_GLYPH          ; copy 6 rows of the '5' glyph into both P/M buffers at row X
                ldx #$96                ; player 2, top row
                jsr COPY_GLYPH          ; copy 6 rows of the '5' glyph into both P/M buffers at row X
                ldx #$EE                ; player 2, bottom row
COPY_GLYPH:     ldy #$06                ; 6 rows (glyph rows 1-6)
COPY_GLYPH_LOOP:
                lda (T_PTR),y           ; $0680[X] = (T_PTR)[Y]
                sta $0680,x             ; buffer at $0400 (players at $0600-$07FF)
                sta $1E80,x             ; buffer at $1C00
                dex
                dey                     ; loop until Y = 0
                bne COPY_GLYPH_LOOP
                rts

;-----------------------------------------------------------------------------
;  DRAW_COLUMNS - draw the left and right columns of '5's into the hidden P/M buffer for
;  scroll phase T_NEXT. The right column (player 3) is drawn from the bottom up shifted one
;  way, the left column (player 0) shifted the other way, so the lights run round the frame.
;  Each column is: a blank gap, then glyphs separated by 8-line gaps.
;-----------------------------------------------------------------------------
DRAW_COLUMNS:   ldx #$80                ; T_PMPTR = hidden buffer + $380 = player 3 (right column)
                stx T_PMPTR
                ldx T_PMPAGE
                inx
                inx
                inx
                stx T_PMPTR+1
                ldy #$7F                ; start at the bottom line of the player
                lda #$0F                ; blank gap of 15 - phase lines
                sec
                sbc T_NEXT
                tax
                jsr DC_GAP              ; X blank lines in the column being drawn
                lda T_NEXT              ; phase 0: glyph first
                beq DC_GLYPH1
                jsr DC_GAP8             ; 8 blank lines in the column being drawn
                beq DC_REST1
DC_GLYPH1:      jsr DC_GLYPH            ; the 8 lines of the '5' glyph in the column being drawn
DC_REST1:       jsr DC_GAP8             ; 8 blank lines in the column being drawn
                jsr DC_FIVE_PAIRS       ; five more glyph+gap pairs
                lda T_NEXT              ; phase >= 8: one more glyph else a gap
                cmp #$08                ; if A < 8 goto DC_GAP1
                bcc DC_GAP1
                jsr DC_GLYPH            ; the 8 lines of the '5' glyph in the column being drawn
                beq DC_LEFT
DC_GAP1:        jsr DC_GAP8             ; 8 blank lines in the column being drawn
DC_LEFT:        jsr DC_GAP8             ; 8 blank lines in the column being drawn
                dec T_PMPTR+1           ; T_PMPTR = hidden buffer + $200 = player 0 (left column)
                ldx #$00
                stx T_PMPTR
                ldy #$79
                ldx T_NEXT              ; blank gap of phase+1 lines
                inx
                jsr DC_GAP              ; X blank lines in the column being drawn
                lda T_NEXT              ; phase >= 10: glyph else gap
                cmp #$0A                ; if A < $0A goto DC_GAP2
                bcc DC_GAP2
                jsr DC_GLYPH            ; the 8 lines of the '5' glyph in the column being drawn
                beq DC_REST2
DC_GAP2:        jsr DC_GAP8             ; 8 blank lines in the column being drawn
DC_REST2:       jsr DC_GAP8             ; 8 blank lines in the column being drawn
                jsr DC_FIVE_PAIRS       ; five glyph+gap pairs
                ldx #$10                ; and a final 16-line gap
                bne DC_GAP
DC_FIVE_PAIRS:  ldx #$05                ; 5 times: glyph then gap
                stx T_TMP
DC_PAIR:        jsr DC_GLYPH            ; the 8 lines of the '5' glyph in the column being drawn
                jsr DC_GAP8             ; 8 blank lines in the column being drawn
                dec T_TMP               ; T_TMP -= 1, until 0
                bne DC_PAIR
                rts
DC_GAP8:        ldx #$08                ; 8 blank lines
DC_GAP:         lda #$00                ; X blank lines, going up
DC_GAP_LOOP:    sta (T_PMPTR),y
                dey
                dex                     ; loop until X = 0
                bne DC_GAP_LOOP
                rts
DC_GLYPH:       ldx #$08                ; 8 lines of the '5' glyph from the machine's ROM font
                lda T_VOLUME+1          ; if T_VOLUME+1 <> 0 goto DC_GLYPH_5200
                bne DC_GLYPH_5200
DC_GLYPH_800:   lda $E0A8,x             ; 400/800 font at $E000
                sta (T_PMPTR),y
                dey
                dex                     ; loop until X = 0
                bne DC_GLYPH_800
                rts
DC_GLYPH_5200:  lda $F8A8,x             ; 5200 font at $F800
                sta (T_PMPTR),y
                dey
                dex                     ; loop until X = 0
                bne DC_GLYPH_5200
                rts

;-----------------------------------------------------------------------------
;  TITLE_VBI - vertical blank on the high-score screen.
;  Shows the scroll phase / P/M buffer the main loop prepared, rotates the colours when the
;  scroll wraps, pulses "HIGH SCORES:", moves the rainbow, blinks "START", counts down to
;  the demo and plays a soft repeating tone.
;-----------------------------------------------------------------------------
TITLE_VBI:      jsr POLL_KEYS           ; read the keyboard
                lda #$80                ; display list at $8000 (in ROM)
                sta DLISTH
                lda #$00                ; DLISTL = 0
                sta DLISTL
                lda #$2A                ; DMACTL: normal playfield, players on, double-line, display list on
                sta DMACTL
                lda #$02                ; GRACTL: player DMA on
                sta (pGRACTL),y         ; GRACTL = A
                lda T_NEWSCROLL         ; new scroll phase requested?
                cmp T_SCROLL            ; if A == T_SCROLL goto TV_SCROLL
                beq TV_SCROLL
                sta T_SCROLL            ; yes: take it
                lda #$20                ; show the buffer just drawn (the other one of $1C/$04)
                sec
                sbc T_PMPAGE
                sta PMBASE
                ldx T_SCROLL            ; if T_SCROLL <> 0 goto TV_SCROLL
                bne TV_SCROLL
                dec T_ROT               ; rotate the colours one light along
                bpl TV_RECOLOUR
                ldx #$09
                stx T_ROT
TV_RECOLOUR:    jsr KERNEL_COLS_TOP     ; load the new colours into the kernel for the top row
TV_SCROLL:      lda T_SCROLL            ; fine scroll (and kernel delay) for the top row
                jsr SET_FINE_SCROLL     ; set HSCROL and patch the kernel's delay to match
                dec T_TIMER4            ; every 4 frames step the brightness of "HIGH SCORES:"
                bne TV_RAINBOW
                lda #$04                ; T_TIMER4 = 4
                sta T_TIMER4
                lda T_TEXTCOL           ; brightness 2 or 12 ends a sweep
                and #$0F
                cmp #$02                ; if A == 2 goto TV_NEXT_HUE
                beq TV_NEXT_HUE
                cmp #$0C                ; if A <> $0C goto TV_STEP
                bne TV_STEP
                beq TV_TURN
TV_NEXT_HUE:    lda T_TEXTCOL           ; at the dark end move to the next hue
                clc
                adc #$10
                sta T_TEXTCOL
TV_TURN:        lda #$00                ; reverse the brightness step
                sec
                sbc T_TEXTSTEP
                sta T_TEXTSTEP
TV_STEP:        lda T_TEXTCOL           ; T_TEXTCOL = T_TEXTCOL + T_TEXTSTEP
                clc
                adc T_TEXTSTEP
                sta T_TEXTCOL
TV_RAINBOW:     lda T_HUE               ; every 14 frames move the rainbow start (15 colours)
                dec T_TIMER14           ; T_TIMER14 -= 1, until 0
                bne TV_RAIN_SET
                ldx #$0E
                stx T_TIMER14
                sec
                sbc #$01
                bcs TV_RAIN_STORE
                lda #$0E
TV_RAIN_STORE:  sta T_HUE
TV_RAIN_SET:    sta T_COLIX             ; the DLIs count T_COLIX down from here, line by line
                dec T_TIMER30           ; every 30 frames toggle inverse video ("START" blinks)
                bne TV_SECONDS
                ldx #$1E
                stx T_TIMER30
                lda #$02                ; T_INVERSE = 2 - T_INVERSE
                sec
                sbc T_INVERSE
                sta T_INVERSE
                sta CHACTL
TV_SECONDS:     dec T_TIMER60           ; every 60 frames count a second off the demo timer
                bne TV_TONE
                lda #$3C                ; T_TIMER60 = $3C
                sta T_TIMER60
                dec T_DEMOSEC
TV_TONE:        dec T_TIMER11           ; every 11 frames lower the tone's volume one step
                bne TV_EXIT
                lda #$0B                ; T_TIMER11 = $0B
                sta T_TIMER11
                ldx T_VOLUME
                dex
                cpx #$5F                ; volume wraps from 0 back to 15 (distortion 6)
                bne TV_TONE_SET
                ldx #$6F
TV_TONE_SET:    txa
                ldy #$00
                sta T_VOLUME
                sta (pAUDC1),y          ; AUDC1 = A
                lda #$C8                ; AUDF1 = $C8
                sta (pAUDF1),y          ; AUDF1 = A
TV_EXIT:        jmp NMI_EXIT            ; common tail of every interrupt handler

;-----------------------------------------------------------------------------
;  SET_MIDDLE_PLAYERS - put players 1 and 2 (the two middle lights) at A and A+16, and
;  point T_PTR at the kernel's first colour operand. Returns T_CNT = 8 colours to load.
;-----------------------------------------------------------------------------
SET_MIDDLE_PLAYERS:
                ldy #$00
                sta (pHPOSP1),y         ; HPOSP1 = A
                clc
                adc #$10
                sta (pHPOSP2),y         ; HPOSP2 = A
                ldx #$04                ; T_PTR = $0406 = first "LDA #" operand in the RAM kernel
                stx T_PTR+1
                ldx #$06
                stx T_PTR
                ldx #$08                ; 8 colour writes per line
                stx T_CNT
                clc
                rts

;-----------------------------------------------------------------------------
;  KERNEL_COLS_TOP - load the top row's colours into the RAM kernel.
;  The eight "LDA #colour" operands get eight consecutive colours from the ten-colour ring
;  CHASE_COLOURS (starting at T_ROT); the two middle players get the other two. The high
;  byte of each "STA COLPFn" is rewritten with the GTIA page taken from the pointer table
;  (pHPOSP0+1 = $D0 or $C0), so the same kernel works on the 400/800 and the 5200.
;-----------------------------------------------------------------------------
KERNEL_COLS_TOP:
                lda #$70                ; middle players follow the scroll
                clc
                adc T_SCROLL
                jsr SET_MIDDLE_PLAYERS  ; put players 1 and 2 (the two middle lights) at A and A+16, and
                lda #$09                ; colour index = 9 + rotation
                adc T_ROT
                tax
                ldy #$23                ; operands at +$23, +$1E ... +$00 (5 bytes per LDA/STA pair)
                lda T_SCROLL            ; phase 8-15 shifts a light into the gap: blank it
                cmp #$08                ; if A < 8 goto KCT_LOOP
                bcc KCT_LOOP
                lda #$00
                beq KCT_STORE
KCT_LOOP:       lda CHASE_COLOURS,x     ; next colour of the ring
KCT_STORE:      sta (T_PTR),y           ; patch "LDA #colour"
                lda pHPOSP0+1           ; GTIA page ($D0 or $C0)
                iny
                iny
                iny
                sta (T_PTR),y           ; patch the high byte of "STA COLPFn"
                dey
                dey
                dey
                tya                     ; previous LDA/STA pair
                sec
                sbc #$05
                tay
                dex
                cpy #$0F                ; at the half-way point skip the two players' colours
                bne KCT_NEXT
                dex
                dex
KCT_NEXT:       dec T_CNT               ; T_CNT -= 1, until 0
                bne KCT_LOOP
                ldx T_ROT               ; the two middle players
                lda CHASE_COLOURS+4,x
                ldy #$00
                sta (pCOLPM1),y         ; COLPM1 = A
                lda CHASE_COLOURS+5,x   ; COLPM2 = CHASE_COLOURS+5[X]
                sta (pCOLPM2),y         ; COLPM2 = A
                lda CHASE_COLOURS+9,x   ; and the colour shared by the two side columns
                sta (pCOLPM0),y         ; COLPM0 = A
                sta (pCOLPM3),y         ; COLPM3 = A
                rts

;-----------------------------------------------------------------------------
;  KERNEL_COLS_BOTTOM - as KERNEL_COLS_TOP but for the bottom row, which scrolls the other
;  way: players at $68 + (16 - phase), colours taken in the opposite order.
;-----------------------------------------------------------------------------
KERNEL_COLS_BOTTOM:
                lda #$10
                sec
                sbc T_SCROLL
                and #$0F
                clc
                adc #$68
                jsr SET_MIDDLE_PLAYERS  ; put players 1 and 2 (the two middle lights) at A and A+16, and
                lda #$0E
                adc T_ROT
                tax
                lda T_SCROLL            ; if T_SCROLL <> 0 goto KCB_START
                bne KCB_START
                inx
KCB_START:      ldy #$00
                cmp #$0A                ; if A < $0A goto KCB_LOOP
                bcc KCB_LOOP
                lda #$00
                beq KCB_STORE
KCB_LOOP:       lda CHASE_COLOURS,x
KCB_STORE:      sta (T_PTR),y           ; patch "LDA #colour"
                tya                     ; next pair, going forwards this time
                clc
                adc #$05
                tay
                dex
                cpy #$14                ; if Y <> $14 goto KCB_NEXT
                bne KCB_NEXT
                dex
                dex
KCB_NEXT:       dec T_CNT               ; T_CNT -= 1, until 0
                bne KCB_LOOP
                txa                     ; the two middle players
                clc
                adc #$06
                tax
                lda CHASE_COLOURS,x
                ldy #$00
                sta (pCOLPM1),y         ; COLPM1 = A
                lda CHASE_COLOURS-1,x   ; COLPM2 = CHASE_COLOURS-1[X]
                sta (pCOLPM2),y         ; COLPM2 = A
                rts

;-----------------------------------------------------------------------------
;  DLI_TOP_ROW - display list interrupt just above the top (and the bottom) row of lights.
;  Runs the colour kernel for the 12 scan lines of the mode 7 row.
;-----------------------------------------------------------------------------
DLI_TOP_ROW:    pha                     ; save A, X, Y
                txa
                pha
                tya
                pha
                ldy #$00
                sta WSYNC
                lda T_LINE              ; bottom row at phase 0: give player 3 its colour
                beq DTR_GO
                lda T_SCROLL            ; if T_SCROLL <> 0 goto DTR_GO
                bne DTR_GO
                ldx T_ROT
                lda CHASE_COLOURS+5,x   ; COLPM3 = CHASE_COLOURS+5[X]
                sta (pCOLPM3),y         ; COLPM3 = A
DTR_GO:         sta WSYNC               ; start on a fresh line
                ldx #$0C                ; 12 scan lines
                jmp TITLE_KERNEL        ; into the RAM kernel

        .org $0400                      ; --- block runs in RAM at $0400 (copied there from ROM $9630) ---

;-----------------------------------------------------------------------------
;  TITLE_KERNEL - copied to RAM at $0400 and run there (the code below is assembled for
;  $0400). Cycle-counted: after the first WSYNC each pass, plus the cycles ANTIC
;  steals for DMA, is meant to fill one scan line; the delays tune it to the fine scroll.
;  The "LDA #" operands are patched by KERNEL_COLS_TOP/BOTTOM (the STA high bytes by
;  KERNEL_COLS_TOP alone), and
;  the two delay opcodes by SET_FINE_SCROLL.
;-----------------------------------------------------------------------------
TITLE_KERNEL:   .byte $8D,$0A,$D4       ; wait for the start of the next line
KERNEL_DELAY1:  .byte $E4,$B1           ; delay: CPX/CMP,X/ASL = 3/4/5 cycles (patched)
KERNEL_LINE:    .byte $A9,$00,$8D,$16,$D0,$A9,$00,$8D,$17,$D0,$A9,$00,$8D,$18,$D0,$A9; colours for the left group of
                                                                                     ;   lights
                .byte $00,$8D,$19,$D0,$A9,$00,$8D,$16,$D0,$A9,$00,$8D,$17,$D0,$A9,$00
                .byte $8D,$18,$D0,$A9,$00,$8D,$19,$D0,$01,$B1,$01,$B1,$01,$B1
KERNEL_DELAY2:  .byte $E4,$B1,$CA,$F0,$03,$4C,$05,$04; delay (patched like KERNEL_DELAY1)
KERNEL_DONE:    .byte $4C,$6E,$96       ; back to the cartridge
        .org $966E                      ; --- back to cartridge addresses ---


;-----------------------------------------------------------------------------
;  DLI_AFTER_ROW - continues after the kernel. After the top row: colour the
;  "HIGH SCORES:" line and arm DLI_TEXT_LINES. After the bottom row: prepare the top row's
;  colours for the next frame.
;-----------------------------------------------------------------------------
DLI_AFTER_ROW:  ldx T_LINE              ; top row or bottom row?
                bne DAR_BOTTOM
                lda T_TEXTCOL           ; top row done: "HIGH SCORES:" colour
                sta (pCOLPF1),y         ; COLPF1 = A
                ldx #>DLI_TEXT_LINES    ; next DLI = DLI_TEXT_LINES
                ldy #<DLI_TEXT_LINES
                jsr SET_DLI             ; install a display-list-interrupt handler
                inc T_LINE
                lda #$00
                tay
                sta (pCOLPF2),y         ; COLPF2 = A
                beq DAR_EXIT
DAR_BOTTOM:     ldx #$00                ; bottom row done: start over
                stx T_LINE
                jsr KERNEL_COLS_TOP     ; colours for next frame's top row
DAR_EXIT:       jmp NMI_EXIT            ; common tail of every interrupt handler

;-----------------------------------------------------------------------------
;  DLI_TEXT_LINES - one DLI per text line between the two rows. It colours the two '5's of
;  the side columns that share this band (COLPM0 left, COLPM3 right) and gives each
;  high-score line the next rainbow colour. After the 16th it switches back to
;  DLI_TOP_ROW for the bottom row and prepares the kernel for it.
;-----------------------------------------------------------------------------
DLI_TEXT_LINES: pha                     ; save A, X, Y
                txa
                pha
                tya
                pha
                ldy #$00
                ldx T_LINE              ; which light (if any) is level with this line?
                lda LIGHT_ROW,x         ; WSYNC = LIGHT_ROW[X]
                sta WSYNC
                beq DTL_RAINBOW         ; none
                ldx T_SCROLL            ; phase 10-15: lights have moved a slot
                cpx #$0A                ; if X < $0A goto DTL_LOW
                bcc DTL_LOW
                cmp #$0A                ; if A < $0A goto DTL_RAINBOW
                bcc DTL_RAINBOW
                ldx #$00
                stx T_CNT2
                sbc #$0A
                bcs DTL_COLOUR
DTL_LOW:        cmp #$0A                ; if A >= $0A goto DTL_RAINBOW
                bcs DTL_RAINBOW
                ldx #$01
                stx T_CNT2
DTL_COLOUR:     sta T_CNT               ; colour of the left light
                clc
                adc T_ROT
                tax
                lda CHASE_COLOURS+4,x   ; COLPM0 = CHASE_COLOURS+4[X]
                sta (pCOLPM0),y         ; COLPM0 = A
                lda #$05                ; colour of the right light (the ring runs the other way)
                sec
                sbc T_CNT
                clc
                adc T_CNT2
                adc T_ROT
                tax
                lda CHASE_COLOURS-1,x   ; COLPM3 = CHASE_COLOURS-1[X]
                sta (pCOLPM3),y         ; COLPM3 = A
DTL_RAINBOW:    lda T_LINE              ; the "HIGH SCORES:" line is not rainbowed
                cmp #$02                ; if A == 2 goto DTL_NEXT
                beq DTL_NEXT
                lda T_COLIX             ; next rainbow colour (index counts down, 15 colours)
                sec
                sbc #$01
                bcs DTL_RAIN_SET
                lda #$0E
DTL_RAIN_SET:   sta T_COLIX
                tax
                lda RAINBOW,x           ; COLPF0 = RAINBOW[X]
                sta (pCOLPF0),y         ; COLPF0 = A
DTL_NEXT:       ldx T_LINE              ; the "Press START" line is white
                cpx #$0E                ; if X <> $0E goto DTL_COUNT
                bne DTL_COUNT
                lda #$0F                ; COLPF1 = $0F
                sta (pCOLPF1),y         ; COLPF1 = A
DTL_COUNT:      inc T_LINE
                ldx #$10                ; 16 lines done?
                cpx T_LINE              ; if X <> T_LINE goto DTL_EXIT
                bne DTL_EXIT
                ldy #<DLI_TOP_ROW       ; yes: next DLI is DLI_TOP_ROW again, for the bottom row
                ldx #>DLI_TOP_ROW
                jsr SET_DLI             ; install a display-list-interrupt handler
                lda #$10                ; the bottom row scrolls the other way: 16 - phase
                sec
                sbc T_SCROLL
                and #$0F
                jsr SET_FINE_SCROLL     ; set HSCROL and patch the kernel's delay to match
                jsr KERNEL_COLS_BOTTOM  ; colours for the bottom row
DTL_EXIT:       jmp NMI_EXIT            ; common tail of every interrupt handler

;-----------------------------------------------------------------------------
;  CHASE_COLOURS - the ten colours of the chasing lights, repeated so that any run of ten
;  can be read from any start. Each value is hue (high nibble) and brightness (low nibble).
;-----------------------------------------------------------------------------
CHASE_COLOURS:  .byte $0E,$84,$C6,$48,$BA,$E4,$56,$32,$6A,$16
                .byte $0E,$84,$C6,$48,$BA,$E4,$56,$32,$6A,$16
                .byte $0E,$84,$C6,$48

;-----------------------------------------------------------------------------
;  LIGHT_ROW - for each title DLI line: which light of the side columns sits in it
;  (0 = none). Values above 10 belong to the second half of the scroll.
;-----------------------------------------------------------------------------
LIGHT_ROW:      .byte $BA,$05,$0E,$04,$0D,$00,$03,$00,$0C,$00,$02,$00,$0B,$00,$01,$0A

;-----------------------------------------------------------------------------
;  RAINBOW - 15 colours for the high-score lines.
;-----------------------------------------------------------------------------
RAINBOW:        .byte $1A,$EA,$2A,$FA,$3A,$4A,$5A,$6A,$7A,$8A,$9A,$AA,$BA,$CA,$DA

;-----------------------------------------------------------------------------
;  TITLE_INIT - starting values for T_SCROLL ($B0) .. T_VOLUME ($CA).
;-----------------------------------------------------------------------------
TITLE_INIT:     .byte $00,$00,$00,$00,$D0,$E1,$FF,$00,$00,$00,$36,$02,$03,$02
                .byte $02,$04,$00,$00,$00,$02,$00,$FF,$28,$3C,$1E,$01,$60

;-----------------------------------------------------------------------------
;  START_GAME - start a game (DEMO_PTR+1 = 0) or the demo (DEMO_PTR+1 <> 0).
;  A real game starts in station 1 of the zone chosen on the title screen (START_ZONE,
;  1 unless a digit key was used). The demo plays station 1 from a recording.
;-----------------------------------------------------------------------------
START_GAME:     lda #$00                ; screen and NMIs off
                sta NMIEN
                sta DMACTL
                jsr INIT_PLAYERS        ; fresh player variables for both players
                ldy DEMO_PTR+1          ; demo?
                bne START_DEMO
                ldy START_ZONE          ; real game: both players start in START_ZONE
                sty ZONE
                sty P2_DATA+1           ; (player 2's copy)
                jmp PLAY_STATION        ; build the station and play
START_DEMO:     ldx #$01                ; demo: station 1, recording 0
                stx STATION
                dex
                jmp SET_DEMO

;-----------------------------------------------------------------------------
;  DEMO_TABLE - addresses of the recorded demos: 0 = station 1 (after the high-score
;  screen), 2 = the opening credits on station 11.
;-----------------------------------------------------------------------------
DEMO_TABLE:     .word DEMO_STATION1,DEMO_CREDITS

;-----------------------------------------------------------------------------
;  Recorded demo input. Each pair is (stick+button, frames): bits 0-3 are the joystick
;  (PORTA format, 0 = pushed: 1 up, 2 down, 4 left, 8 right), bit 4 is the button
;  (0 = pressed). $1F = nothing, $17 = right, $1B = left, $1E = up, $1D = down,
;  $0F = jump on the spot, $0B/$07 = jump left/right.
;-----------------------------------------------------------------------------
DEMO_STATION1:  .byte $1F,$51,$17,$0B,$1F,$06,$0F,$09,$1F,$1D,$17,$FF,$17,$26,$1F,$16
                .byte $0B,$05,$0F,$04,$1F,$1E,$17,$08,$1F,$02,$1B,$AD,$1A,$08,$1E,$36
                .byte $1F,$01,$16,$02,$17,$27,$1F,$03,$1B,$5E,$1F,$02,$17,$0B,$1F,$11
                .byte $0B,$05,$0F,$04,$1F,$28,$17,$06,$1F,$04,$1B,$25,$1F,$02,$17,$63
                .byte $16,$02,$1E,$3E,$16,$02,$17,$B3,$1F,$02,$1B,$7F,$1A,$05,$1B,$01
                .byte $1A,$0B,$1E,$23,$16,$01,$17,$7C,$1F,$04,$1A,$01,$1B,$0E,$1A,$09
                .byte $1E,$3A,$16,$03,$17,$20,$1F,$02,$1B,$BE,$1F,$58,$1B,$22,$0B,$0A
                .byte $1B,$01,$1F,$26,$1B,$08,$1F,$03,$17,$47,$1F,$01,$1D,$08,$19,$02
                .byte $1D,$3C,$19,$02,$1B,$3F,$1F,$02,$17,$9C,$1F,$57
DEMO_CREDITS:   .byte $1F,$5E,$17,$FF,$17,$21,$1F,$0D,$1B,$05,$1F,$19,$0F,$12,$1F,$25
                .byte $17,$16,$1F,$03,$1B,$0A,$19,$09,$1D,$3D,$19,$11,$1B,$CC,$1F,$1F
                .byte $17,$03,$1F,$1A,$0F,$16,$1F,$2C,$0F,$10,$1F,$2A,$0B,$0B,$0F,$03
                .byte $1F,$28,$1B,$23,$1F,$03,$17,$07,$1D,$6C,$15,$02,$17,$0C,$1F,$12
                .byte $1B,$01,$1F,$1E,$07,$0A,$0F,$03,$1F,$2D,$17,$DE,$1F,$03,$1B,$05
                .byte $1F,$19,$0F,$11,$1F,$27,$0F,$19,$1F,$1F,$0F,$12,$1F,$1E,$17,$0D
                .byte $1F,$06,$1B,$01,$19,$09,$1D,$45,$19,$2C,$1B,$02,$1F,$08,$17,$05
                .byte $1F,$15,$0B,$07,$0F,$07,$1F,$22,$1B,$C5,$1F,$03,$17,$04,$15,$03
                .byte $1D,$5C,$15,$02,$17,$FF,$17,$2B

;-----------------------------------------------------------------------------
;  DRAW_SLIDES - draw the station's slides (chutes) from the list at SLIDES.
;  Entry: rows, x (P/M), y (Bob's y at the top), step (signed x shift per row).
;  Each row is 8 pixels of colour 2 (PLOT_COLOR left at 4 by DRAW_LADDERS); the band moves "step" pixels
;  sideways per row, so it slants. The same entries tell MOVE_BOB where slides start.
;-----------------------------------------------------------------------------
DRAW_SLIDES:    ldy #$00
                sty CNT1
DS_NEXT:        ldy CNT1
                lda (SLIDES),y          ; rows (0 = end of list)
                bne DS_ENTRY
                rts
DS_ENTRY:       sta SLIDE_LEN
                iny                     ; x: P/M coordinates -> pixel column
                lda (SLIDES),y          ; PLOT_X = (SLIDES)[Y] - $30
                sec
                sbc #$30
                sta PLOT_X
                iny                     ; y: Bob's top -> the line under his feet
                lda (SLIDES),y          ; PLOT_Y = (SLIDES)[Y] + $15
                clc
                adc #$15
                sta PLOT_Y
                iny                     ; step per row
                lda (SLIDES),y          ; CNT3 = (SLIDES)[Y]
                sta CNT3
                iny
                sty CNT1
DS_ROW:         lda #$08                ; 8 pixels per row
                sta CNT2
DS_PIXEL:       ldy PLOT_X
                ldx PLOT_Y
                jsr PLOT_IF_EMPTY       ; set pixel (Y = pixel x 0-159, X = line y 8-191) to colour PLOT_COLOR,
                inc PLOT_X
                dec CNT2                ; CNT2 -= 1, until 0
                bne DS_PIXEL
                inc PLOT_Y              ; next line down
                lda PLOT_X              ; x = x + 8 - 9 + step + 1 (carry set) = x + step
                sec
                sbc #$09
                adc CNT3
                sta PLOT_X
                dec SLIDE_LEN           ; SLIDE_LEN -= 1, until 0
                bne DS_ROW
                beq DS_NEXT

;-----------------------------------------------------------------------------
;  INIT_LIFTS - copy the moving platforms (6-byte records, list at LIFTS) to LIFT_TAB and
;  draw them. Record: 0 timer, 1 width, 2 x, 3 y, 4 travel, 5 speed (signed).
;  Each platform is "width" columns of 3 pixels in colour 3, like a girder (colour 1 on
;  station 8, where it is the lift).
;-----------------------------------------------------------------------------
INIT_LIFTS:     ldy #$FF                ; Y = -1: CP_BYTE pre-increments
                sty CNT1
                ldy #$08                ; colour 3 ...
                lda STATION
                cmp #$08                ; if A <> 8 goto IL_SET
                bne IL_SET
                ldy #$00                ; ... except station 8 (colour 1)
IL_SET:         sty PLOT_COLOR
IL_NEXT:        ldy CNT1
                jsr CP_BYTE             ; timer (0 = end of list)
                beq CP_RTS
                jsr CP_BYTE             ; width
                sta CNT0
                jsr CP_BYTE             ; x
                sta PLOT_X
                jsr CP_BYTE             ; y
                sta PLOT_Y
                jsr CP_BYTE             ; travel (copied only)
                jsr CP_BYTE             ; speed (copied only)
                sty CNT1
IL_COLUMN:      ldy #$03                ; 3 pixels down
                sty CNT3
IL_PIXEL:       ldx PLOT_Y
                ldy PLOT_X
                jsr PLOT_XY             ; set pixel (x = Y, line = X) to PLOT_COLOR
                inc PLOT_Y
                dec CNT3                ; CNT3 -= 1, until 0
                bne IL_PIXEL
                lda PLOT_Y              ; back up and one column right
                sec
                sbc #$03
                sta PLOT_Y
                inc PLOT_X
                dec CNT0                ; CNT0 -= 1, until 0
                bne IL_COLUMN
                beq IL_NEXT
CP_BYTE:        iny                     ; copy the next byte of the list into LIFT_TAB
                lda (LIFTS),y           ; LIFT_TAB[Y] = (LIFTS)[Y]
                sta LIFT_TAB,y
CP_RTS:         rts

;-----------------------------------------------------------------------------
;  DRAW_LADDERS - draw the station's ladders (list at LADDERS) in colour 2.
;  Entry: height, x (P/M), y, style. A ladder is 8 pixels wide: a 2-pixel rail, a
;  4-pixel rung or gap, a 2-pixel rail, with a rung every 4 lines. Style bit 7 makes a
;  "ladder top" that starts 5 lines higher; the low bits set the rung phase.
;-----------------------------------------------------------------------------
DRAW_LADDERS:   lda #$04                ; colour 2
                sta PLOT_COLOR
                ldy #$00
                sty CNT1
DL_NEXT:        ldy CNT1
                lda (LADDERS),y         ; height (0 = end of list)
                bne DL_ENTRY
                rts
DL_ENTRY:       sta CNT0
                iny                     ; x -> pixel column
                lda (LADDERS),y         ; PLOT_X = (LADDERS)[Y] - $30
                sec
                sbc #$30
                sta PLOT_X
                iny                     ; y
                lda (LADDERS),y         ; PLOT_Y = (LADDERS)[Y]
                sta PLOT_Y
                iny                     ; style
                lda (LADDERS),y         ; if (LADDERS)[Y] bit 7 clear goto DL_PHASE
                bpl DL_PHASE
                and #$7F                ; bit 7: extend 5 lines upwards
                pha
                lda PLOT_Y              ; PLOT_Y = PLOT_Y - 5
                sec
                sbc #$05
                sta PLOT_Y
                lda CNT0                ; CNT0 = CNT0 + 5
                clc
                adc #$05
                sta CNT0
                pla
DL_PHASE:       sta CNT4                ; rung counter
                iny
                sty CNT1
DL_LINE:        jsr PLOT2               ; left rail
                lda CNT4                ; rung on this line?
                bne DL_GAP
                jsr PLOT4               ; yes: 4 pixels
                jmp DL_RAIL
DL_GAP:         lda PLOT_X              ; no: skip 4 pixels
                clc
                adc #$04
                sta PLOT_X
DL_RAIL:        jsr PLOT2               ; right rail
                lda PLOT_X              ; back to the left edge, next line
                sec
                sbc #$08
                sta PLOT_X
                inc PLOT_Y
                dec CNT4                ; a rung every 4th line
                bpl DL_COUNT
                ldx #$03
                stx CNT4
DL_COUNT:       dec CNT0                ; CNT0 -= 1, goto DL_NEXT if 0
                beq DL_NEXT
                bne DL_LINE
PLOT4:          ldx #$04                ; 4 pixels in a row
                bne PLOT_RUN
PLOT2:          ldx #$02                ; 2 pixels in a row
PLOT_RUN:       stx CNT2
PLOT_RUN_LOOP:  ldx PLOT_Y
                ldy PLOT_X
                jsr PLOT_IF_EMPTY       ; set pixel (Y = pixel x 0-159, X = line y 8-191) to colour PLOT_COLOR,
                inc PLOT_X
                dec CNT2                ; CNT2 -= 1, until 0
                bne PLOT_RUN_LOOP
                rts

;-----------------------------------------------------------------------------
;  DRAW_HLINE - horizontal line of A pixels: line y = X, from pixel x = Y rightwards.
;  (DRAW_HLINE_A takes the line in PLOT_X.) Pixels already drawn are left alone.
;  Note the swapped use of PLOT_X (here the line) and PLOT_Y (here the x position).
;-----------------------------------------------------------------------------
DRAW_HLINE:     stx PLOT_X              ; line y
DRAW_HLINE_A:   sta CNT1                ; length
                sty PLOT_Y              ; first x
DH_LOOP:        ldx PLOT_X
                ldy PLOT_Y
                jsr PLOT_IF_EMPTY       ; set pixel (Y = pixel x 0-159, X = line y 8-191) to colour PLOT_COLOR,
                inc PLOT_Y              ; next pixel to the right
                dec CNT1                ; CNT1 -= 1, until 0
                bne DH_LOOP
                rts

;-----------------------------------------------------------------------------
;  DRAW_GIRDERS - draw the station's girders (floors) and count their sections.
;  In: Y/X = list address, A = slope. The list holds three sub-lists, each ended by 0:
;  sloping down (A = 3), sloping up (DRAW_GIRDERS_MORE with A = 5) and flat (A = 0).
;  Entry: sections, x (pixel), y. A section is 4 pixels wide and is the unit Bob
;  claims; every section drawn is added to SECTIONS. A girder is drawn as three thin
;  stripes in colour 3; claiming fills the gaps so the section turns solid. Flat girders alternate two stripe
;  patterns so they
;  look like brickwork, sloped ones move one line per section (y + 4 - slope).
;-----------------------------------------------------------------------------
DRAW_GIRDERS:   stx SPR_PTR+1           ; list address
                sty SPR_PTR
                ldy #$00
                sty CNT1
                sty SECTIONS            ; no sections counted yet
                ldy #$08                ; colour 3
                sty PLOT_COLOR
DRAW_GIRDERS_MORE:
                sta CNT4                ; slope for this sub-list
DG_NEXT:        ldy CNT1
                lda (SPR_PTR),y         ; sections (0 = end of this sub-list)
                bne DG_ENTRY
                iny                     ; step past the 0 for the next call
                sty CNT1
                rts
DG_ENTRY:       sta CNT0
                clc                     ; count the sections to be claimed
                adc SECTIONS
                sta SECTIONS
                iny                     ; x
                lda (SPR_PTR),y         ; PLOT_X = (SPR_PTR)[Y]
                sta PLOT_X
                iny                     ; y
                lda (SPR_PTR),y         ; PLOT_Y = (SPR_PTR)[Y]
                sta PLOT_Y
                iny
                sty CNT1
DG_SECTION:     lda CNT4                ; flat or sloped?
                bne DG_SLOPED
                jsr DG_THICK            ; flat: a section with a thick top stripe ...
                lda PLOT_Y              ; PLOT_Y = PLOT_Y - 5
                sec
                sbc #$05
                sta PLOT_Y
                dec CNT0                ; CNT0 -= 1, goto DG_NEXT if 0
                beq DG_NEXT
                jsr DG_STRIPES          ; ... then one with thin stripes
                ldy #$04
                bne DG_RISE
DG_SLOPED:      jsr DG_STRIPES          ; sloped: one section, then move y by (slope - 4)
                ldy CNT4
DG_RISE:        dec PLOT_Y
                dey                     ; loop until Y = 0
                bne DG_RISE
                dec CNT0                ; CNT0 -= 1, until 0
                bne DG_SECTION
                beq DG_NEXT
DG_THICK:       jsr DG_ROW4             ; an extra stripe line, then the three normal stripes
                jsr DG_BACK             ; x back 4 pixels, one line down
DG_STRIPES:     ldx #$03                ; three stripes, two lines apart
                stx CNT3
DG_STRIPE:      jsr DG_ROW4             ; 4 pixels at (PLOT_X, PLOT_Y), moving right
                dec CNT3                ; CNT3 -= 1, goto PIE_RTS if 0
                beq PIE_RTS
                jsr DG_BACK             ; x back 4 pixels, one line down
                inc PLOT_Y              ; PLOT_Y += 1, until 0
                bne DG_STRIPE
DG_ROW4:        ldx #$04                ; 4 pixels from (PLOT_X, PLOT_Y), PLOT_X advances
                stx CNT2
DG_ROW4_LOOP:   ldy PLOT_X
                ldx PLOT_Y
                jsr PLOT_IF_EMPTY       ; set pixel (Y = pixel x 0-159, X = line y 8-191) to colour PLOT_COLOR,
                inc PLOT_X
                dec CNT2                ; CNT2 -= 1, until 0
                bne DG_ROW4_LOOP
                rts
DG_BACK:        lda PLOT_X              ; x back 4 pixels, one line down
                sec
                sbc #$04
                sta PLOT_X
                inc PLOT_Y
                rts

;-----------------------------------------------------------------------------
;  PLOT_IF_EMPTY - set pixel (Y = pixel x 0-159, X = line y 8-191) to colour PLOT_COLOR,
;  but only if it is still background. Mode E packs 4 pixels per byte, 2 bits each,
;  leftmost pixel in bits 7-6:
;    byte = LINE_LO/HI[y] + x/4,  bit pair = x and 3.
;  PIXEL_MASK[x and 3] isolates the pair; PIXEL_SET[colour + (x and 3)] supplies it.
;-----------------------------------------------------------------------------
PLOT_IF_EMPTY:  lda LINE_LO,x           ; address of line y
                sta PTR
                lda LINE_HI,x           ; PTR+1 = LINE_HI[X]
                sta PTR+1
                tya                     ; X = x and 3 (pixel within the byte)
                and #$03
                tax
                tya                     ; Y = x / 4 (byte within the line)
                lsr a
                lsr a
                tay
                lda PIXEL_MASK,x        ; already drawn?
                and (PTR),y
                bne PIE_RTS             ; yes: leave it
                txa                     ; pick the bit pattern for this colour and position
                clc
                adc PLOT_COLOR
                tax
                lda PIXEL_SET,x
                ora (PTR),y
                sta (PTR),y
PIE_RTS:        rts

;-----------------------------------------------------------------------------
;  PLOT - set pixel (PLOT_X, PLOT_Y) to colour PLOT_COLOR, replacing what was there.
;  Entry points: PLOT (from PLOT_X/PLOT_Y), PLOT_YX_Y (x already in Y),
;  PLOT_XY (Y = x, X = y), PLOT_PTR (line address already in PTR).
;-----------------------------------------------------------------------------
PLOT:           ldy PLOT_X
PLOT_YX_Y:      ldx PLOT_Y
PLOT_XY:        lda LINE_LO,x           ; address of line y
                sta PTR
                lda LINE_HI,x           ; PTR+1 = LINE_HI[X]
                sta PTR+1
PLOT_PTR:       tya                     ; X = x and 3
                and #$03
                tax
                tya                     ; Y = x / 4
                lsr a
                lsr a
                tay
                lda PIXEL_CLEAR,x       ; clear the old pixel
                and (PTR),y
                pha
                txa
                clc
                adc PLOT_COLOR
                tax
                pla
                ora PIXEL_SET,x         ; and set the new colour
                sta (PTR),y
                rts

;-----------------------------------------------------------------------------
;  READ_PIXEL - colour of the pixel at P/M x = PLOT_X, line y = PLOT_Y (0 = background,
;  1 = items and text, 2 = ladders and slides, 3 = girders and platforms).
;  Out: A = colour, Z set if it is colour 3. Lines outside 8-191 read as line 8.
;  READ_PIXEL_XY takes X = y, Y = x; READ_PIXEL_PTR uses the line already in PIX_PTR.
;-----------------------------------------------------------------------------
READ_PIXEL:     ldx PLOT_Y
                ldy PLOT_X
READ_PIXEL_XY:  cpx #$C0                ; clamp y into the bitmap
                bcs RP_CLAMP
                cpx #$08                ; if X >= 8 goto RP_LINE
                bcs RP_LINE
RP_CLAMP:       ldx #$08
RP_LINE:        lda LINE_LO,x           ; PIX_PTR = LINE_LO[X]
                sta PIX_PTR
                lda LINE_HI,x           ; PIX_PTR+1 = LINE_HI[X]
                sta PIX_PTR+1
READ_PIXEL_PTR: tya                     ; P/M x -> pixel x
                sec
                sbc #$30
                tay
                and #$03                ; X = x and 3
                tax
                tya                     ; Y = x / 4
                lsr a
                lsr a
                tay
                lda (PIX_PTR),y
RP_SHIFT:       cpx #$03                ; shift the pair down to bits 1-0
                beq RP_DONE
                lsr a
                lsr a
                inx
                bne RP_SHIFT
RP_DONE:        and #$03
                cmp #$03                ; Z = colour 3?
RP_RTS:         rts

;-----------------------------------------------------------------------------
;  Station 11 (the opening credits) has no status line: these 4 bytes replace the top of
;  the display list with "8 blank lines + DLI" and "mode E, LMS $2100".
;-----------------------------------------------------------------------------
DL_CREDITS_TOP: .byte $F0,$4E,$00,$21

;-----------------------------------------------------------------------------
;  BUILD_DLIST - build the game screen's display list at $2000 and the line tables.
;    $2000  3 x "8 blank lines"                      (top border)
;    $2003  mode 2 + LMS $20D8 + DLI                  status line (40 text characters)
;    $2006  184 x mode E (160 x 1, 4 colours)        the playfield bitmap at $2100
;           bitmap lines 46, 93 and 140 also request a DLI (mutant bands, see DLI_MUTANTS)
;           line 96 reloads the address ($3000): ANTIC cannot cross a 4K boundary
;    $20C0  JVB $2000
;  Then LINE_LO/LINE_HI[y] = $2100 + 40 * (y - 8) for y = 8..191, and the bitmap is cleared.
;-----------------------------------------------------------------------------
BUILD_DLIST:    lda #$70                ; 3 lines of 8 blank scan lines
                sta DLIST
                sta DLIST+1
                sta DLIST+2
                lda #$C2                ; status line: mode 2 + LMS + DLI
                sta DLIST+3
                lda #$D8                ; at $20D8
                sta DLIST+4
                lda #$20                ; DLIST+5 = $20
                sta DLIST+5
                lda #$0E                ; 186 x mode E (two are overwritten by the LMS below)
                ldx #$BA
BD_FILL:        sta DLIST+5,x
                dex                     ; loop until X = 0
                bne BD_FILL
                lda STATION             ; the credits screen has no status line
                cmp #$0B                ; if A == $0B goto BD_CREDITS
                beq BD_CREDITS
                lda #$8E                ; DLIs for the mutant bands
                sta DLIST+52
                sta $2063
                sta $2094
                bne BD_LMS
BD_CREDITS:     ldy #$04
BD_CREDITS_LOOP:
                lda RP_RTS,y            ; DLIST+2[Y] = RP_RTS[Y]
                sta DLIST+2,y
                dey                     ; loop until Y = 0
                bne BD_CREDITS_LOOP
BD_LMS:         lda #$4E                ; line 96: mode E + LMS $3000 (across the 4K boundary)
                sta $2066
                lda #$00                ; $2067 = 0
                sta $2067
                lda #$30                ; $2068 = $30
                sta $2068
                lda #$41                ; JVB $2000
                sta $20C0
                lda #$00                ; $20C1 = 0
                sta $20C1
                lda #$20                ; $20C2 = $20
                sta $20C2
                ldx #$00                ; line tables for y = 8 ... 191
                stx PTR
                txa
                ldy #$21
BD_TABLE:       sta LINE_LO+8,x
                tya
                sta LINE_HI+8,x
                lda PTR                 ; + 40 bytes per line
                clc
                adc #$28
                sta PTR
                bcc BD_TABLE_NEXT
                iny
BD_TABLE_NEXT:  inx
                cpx #$B8                ; if X <> $B8 goto BD_TABLE
                bne BD_TABLE
                ldx #$20                ; clear $20D8 onwards: status line + bitmap ($1D28 bytes)
                stx PTR+1
                ldx #$D8
                stx PTR
                ldx #$E3
                ldy #$18

;-----------------------------------------------------------------------------
;  ZERO_MEM - zero memory from (PTR) for -(X:Y) bytes.
;-----------------------------------------------------------------------------
ZERO_MEM:       stx CNT1
                sty CNT0
                lda #$00
                tay
ZM_LOOP:        sta (PTR),y
                inc PTR                 ; PTR += 1, until 0
                bne ZM_COUNT
                inc PTR+1
ZM_COUNT:       inc CNT0                ; CNT0 += 1, until 0
                bne ZM_LOOP
                inc CNT1                ; CNT1 += 1, until 0
                bne ZM_LOOP
                rts

;-----------------------------------------------------------------------------
;  PIXEL_SET - bits to OR in, indexed by PLOT_COLOR + (x and 3):
;    +0 colour 1 ($40 $10 $04 $01)   +4 colour 2 ($80 $20 $08 $02)   +8 colour 3 (PIXEL_MASK)
;   +12 background (the zeros after PIXEL_MASK).
;  PIXEL_MASK - the two bits of each pixel ($C0 $30 $0C $03); doubles as colour 3.
;  PIXEL_CLEAR - the complement, to clear one pixel.
;-----------------------------------------------------------------------------
PIXEL_SET:      .byte $40,$10,$04,$01
                .byte $80,$20,$08,$02
PIXEL_MASK:     .byte $C0,$30,$0C,$03
                .byte $00,$00,$00,$00
PIXEL_CLEAR:    .byte $3F,$CF,$F3,$FC

;-----------------------------------------------------------------------------
;  SETUP_PULVERIZERS - station 9 ("The Pulverizers").
;  Draws the 3-line-thick beam the pulverizers hang from (lines $9D-$9F, x 40-131), gives
;  the four pulverizers a random starting delay, draws their heads in the raised position
;  (y = $A0), and draws the two 2-pixel posts at the ends of the frame.
;-----------------------------------------------------------------------------
SETUP_PULVERIZERS:
                ldx #$9D                ; first line of the beam
                stx PLOT_X
                ldx #$03                ; 3 lines thick
                stx CNT3
                ldx #$08                ; colour 3
                stx PLOT_COLOR
SP_BEAM:        ldy #$28                ; from x = 40 ...
                lda #$5C                ; ... 92 pixels long
                jsr DRAW_HLINE_A        ; horizontal line: line = PLOT_X, from x = Y, A pixels
                inc PLOT_X
                dec CNT3                ; CNT3 -= 1, until 0
                bne SP_BEAM
                ldx #$04                ; 4 pulverizers
                stx CNT6
                ldy #$00
SP_INIT:        lda (pAUDCTL,x)         ; X = 4 here, so this reads (pSKRES) = RANDOM: random start delay
                sta PULV_TAB,y
                lda #$01                ; moving down when it starts
                sta PULV_TAB+1,y
                lda #$A0                ; at the top (y = $A0)
                sta PULV_TAB+2,y
                iny                     ; next 3-byte record
                iny
                iny
                dec CNT6                ; CNT6 -= 1, until 0
                bne SP_INIT
                lda #$0B                ; draw the four heads at byte columns $0B, $11, $17, $1D
SP_HEADS:       ldx #$A0
                tay
                pha
                jsr DRAW_PULV           ; draw a pulverizer head with its top line at y = X, byte column Y
                pla
                clc
                adc #$06
                cmp #$1E                ; if A < $1E goto SP_HEADS
                bcc SP_HEADS
                ldx #$28                ; the two posts, at pixel x = $28 and $82
                jsr DRAW_POST           ; 2-pixel-wide post, 31 lines, at pixel x = X
                ldx #$82
DRAW_POST:      stx PLOT_X              ; 2 pixels wide, 31 lines from y = $A0, colour 2
                ldy #$A0
                sty PLOT_Y
                lda #$04                ; PLOT_COLOR = 4
                sta PLOT_COLOR
                lda #$1F                ; CNT3 = $1F
                sta CNT3
DP_LOOP:        jsr PLOT                ; set pixel (PLOT_X, PLOT_Y) to colour PLOT_COLOR, replacing what was th
                inc PLOT_X
                jsr PLOT                ; set pixel (PLOT_X, PLOT_Y) to colour PLOT_COLOR, replacing what was th
                dec PLOT_X
                inc PLOT_Y
                dec CNT3                ; CNT3 -= 1, until 0
                bne DP_LOOP
DP_RTS:         rts

;-----------------------------------------------------------------------------
;  PULV_SHAPE - a pulverizer head, read backwards by DRAW_PULV: 6 lines of 3 bytes
;  (12 pixels). The top line is a thin rod: as the head moves down, each frame leaves
;  that line behind, so the rod grows from the beam. The blank bottom line erases the
;  head's old bottom line as it rises.
;-----------------------------------------------------------------------------
PULV_SHAPE:     .byte $00,$00,$00       ; .... .... ....
                .byte $55,$55,$55       ; 1111 1111 1111
                .byte $55,$55,$55       ; 1111 1111 1111
                .byte $50,$55,$05       ; 11.. 1111 ..11
                .byte $50,$55,$05       ; 11.. 1111 ..11
                .byte $00,$AA,$00       ; .... 2222 ....

;-----------------------------------------------------------------------------
;  DRAW_PULV - draw a pulverizer head with its top line at y = X, byte column Y.
;-----------------------------------------------------------------------------
DRAW_PULV:      lda LINE_LO,x           ; line address
                sta PTR
                lda LINE_HI,x           ; PTR+1 = LINE_HI[X]
                sta PTR+1
                ldx #$12                ; 18 bytes, last first
DPV_LINE:       lda #$03                ; 3 bytes per line
                sta CNT2
DPV_BYTE:       lda DP_RTS,x            ; (PTR)[Y] = DP_RTS[X]
                sta (PTR),y
                iny
                dex
                dec CNT2                ; CNT2 -= 1, until 0
                bne DPV_BYTE
                dey                     ; back to the first byte, next line
                dey
                dey
                lda PTR                 ; PTR = PTR + $28
                clc
                adc #$28
                sta PTR
                bcc DPV_NEXT
                inc PTR+1
DPV_NEXT:       inx
                dex                     ; loop until X = 0
                bne DPV_LINE
                rts

;-----------------------------------------------------------------------------
;  MOVE_PULVERIZERS - station 9, every frame. Each head waits, drops 22 lines to y = $B6,
;  rises back to $A0, then waits again. The wait gets shorter as the zone rises:
;    delay = (18 - 2 * min(zone, 9)) * 8 + 40 frames
;-----------------------------------------------------------------------------
MOVE_PULVERIZERS:
                lda STATION             ; only on station 9
                cmp #$09                ; if A <> 9 goto MP_RTS
                bne MP_RTS
                ldy #$0B                ; Y = byte column of the first head
                ldx #$00
MP_LOOP:        lda PULV_TAB,x          ; waiting?
                bne MP_WAIT
                lda PULV_TAB+1,x        ; move by the direction (+1 / -1)
                clc
                adc PULV_TAB+2,x
                sta PULV_TAB+2,x
                cmp #$B6                ; at the bottom: turn round
                beq MP_BOTTOM
                cmp #$A0                ; back at the top?
                bne MP_DRAW
                lda #$01                ; yes: moving down next time ...
                sta PULV_TAB+1,x
                lda ZONE                ; ... after a delay that depends on the zone
                cmp #$0A                ; if A < $0A goto MP_DELAY
                bcc MP_DELAY
                lda #$09
MP_DELAY:       asl a
                sta PLOT_X
                lda #$12
                sec
                sbc PLOT_X
                asl a
                asl a
                asl a
                clc
                adc #$28
                sta PULV_TAB,x
                lda #$A0                ; redraw at the top
                bne MP_DRAW
MP_BOTTOM:      lda #$FF                ; direction = up
                sta PULV_TAB+1,x
                lda #$B6
MP_DRAW:        stx PLOT_X              ; redraw the head at its new height
                sty PLOT_Y
                tax
                jsr DRAW_PULV           ; draw a pulverizer head with its top line at y = X, byte column Y
                ldx PLOT_X
                ldy PLOT_Y              ; if PLOT_Y <> 0 goto MP_NEXT
                bne MP_NEXT
MP_WAIT:        dec PULV_TAB,x          ; count the delay down
MP_NEXT:        inx                     ; next record and next column (+6 bytes = 24 pixels)
                inx
                inx
                tya
                clc
                adc #$06
                tay
                cmp #$1E                ; if A < $1E goto MP_LOOP
                bcc MP_LOOP
MP_RTS:         rts

;-----------------------------------------------------------------------------
;  GAME_OVER_TUNE - plays "Oh My Darling, Clementine" ("...dwelt a miner, forty-niner")
;  three times: on voice 1, then on voice 2, then on both. START, the button, a digit key
;  or OPTION cuts it short; at the end the high-score screen appears.
;
;  TUNE holds (note, length) pairs; a note is an AUDF1 divider (smaller = higher), $FE ends
;  a phrase and $FF the tune. Voice 2 does not read the table: its divider is worked out
;  from the melody note, (note - $1D) * 4 + $79 ($6C for note $1A), which puts it about
;  two octaves lower. Each note starts at volume 15 (pure tone, AUDC $AF), holds for
;  length+2 frames, then fades one step per frame to volume 6.
;-----------------------------------------------------------------------------
GAME_OVER_TUNE: ldx #$01                ; pass 1: voice 1 only
GOT_PASS:       stx MOVE_B              ; voice mask: 1 = voice 1, 2 = voice 2, 3 = both
                ldx #$00
GOT_NOTE:       lda TUNE,x              ; next byte of the tune
                bpl GOT_PLAY            ; a note?
                ldy #$A5                ; end of phrase: fade from volume 5 down to 0 ...
GOT_FADE:       jsr SET_TUNE_VOL        ; write AUDC value Y to the voices selected in MOVE_B (bit 0 = voice 1,
                jsr WAIT_FRAME_KEYS     ; ... two frames per step
                jsr WAIT_FRAME_KEYS     ; wait for the next frame, checking OPTION, digit keys and START while
                dey
                cpy #$9F                ; if Y <> $9F goto GOT_FADE
                bne GOT_FADE
                lda TUNE,x              ; end of the tune?
                cmp #$FF                ; if A <> $FF goto GOT_NEXT
                bne GOT_NEXT
                ldy #$14                ; yes: 20 frames of silence
GOT_REST:       jsr WAIT_FRAME_KEYS     ; wait for the next frame, checking OPTION, digit keys and START while
                dey                     ; loop until Y = 0
                bne GOT_REST
                ldx MOVE_B              ; next pass
                inx
                cpx #$04                ; if X <> 4 goto GOT_PASS
                bne GOT_PASS
                jmp TITLE_SCREEN        ; three passes played: the high-score screen
GOT_PLAY:       ldy #$00                ; melody on voice 1
                sta (pAUDF1),y          ; work out voice 2's note from the melody note
                cmp #$1A                ; if A <> $1A goto GOT_BASS
                bne GOT_BASS
                lda #$6C
                bne GOT_SET2
GOT_BASS:       sec
                sbc #$1D
                asl a
                asl a
                clc
                adc #$79
GOT_SET2:       sta (pAUDF2),y          ; AUDF2 = A
                ldy #$AF                ; attack: pure tone, volume 15
                jsr SET_TUNE_VOL        ; write AUDC value Y to the voices selected in MOVE_B (bit 0 = voice 1,
                inx                     ; length
                lda TUNE,x
                tay                     ; + 2 frames
                iny
                iny
GOT_HOLD:       jsr WAIT_FRAME_KEYS     ; wait for the next frame, checking OPTION, digit keys and START while
                dey                     ; loop until Y = 0
                bne GOT_HOLD
                ldy #$AE                ; decay: volume 14 down to 6, one per frame
GOT_DECAY:      jsr SET_TUNE_VOL        ; write AUDC value Y to the voices selected in MOVE_B (bit 0 = voice 1,
                jsr WAIT_FRAME_KEYS     ; wait for the next frame, checking OPTION, digit keys and START while
                dey
                cpy #$A5                ; if Y <> $A5 goto GOT_DECAY
                bne GOT_DECAY
GOT_NEXT:       inx
                bne GOT_NOTE

;-----------------------------------------------------------------------------
;  WAIT_FRAME_KEYS - wait for the next frame, checking OPTION, digit keys and START while
;  waiting. START/button/digit start a game at once (abandoning the caller).
;-----------------------------------------------------------------------------
WAIT_FRAME_KEYS:
                lda FRAMES              ; FRAMES changes once per frame
                sty SAVE_Y
WFK_LOOP:       pha
                jsr CHECK_OPTION        ; OPTION: high-score screen
                jsr CHECK_ZONE_KEY      ; digit: start in that zone
                jsr CHECK_START_ANY     ; START or button?
                bcc WFK_WAIT
                jmp START_GAME          ; start a game (DEMO_PTR+1 = 0) or the demo (DEMO_PTR+1 <> 0)
WFK_WAIT:       pla
                cmp FRAMES              ; if A == FRAMES goto WFK_LOOP
                beq WFK_LOOP
                ldy SAVE_Y
                rts

;-----------------------------------------------------------------------------
;  SET_TUNE_VOL - write AUDC value Y to the voices selected in MOVE_B (bit 0 = voice 1,
;  bit 1 = voice 2).
;-----------------------------------------------------------------------------
SET_TUNE_VOL:   lda MOVE_B
                lsr a
                bcc STV_VOICE2
                pha
                tya
                ldy #$00
                sta (pAUDC1),y          ; AUDC1 = A
                tay
                pla
STV_VOICE2:     lsr a
                bcc STV_RTS
                tya
                ldy #$00
                sta (pAUDC2),y          ; AUDC2 = A
                tay
STV_RTS:        rts

;-----------------------------------------------------------------------------
;  TUNE - Clementine: (POKEY divider, frames) pairs. $28 = C, $35 = G below it,
;  $1F = E, $1A = G, $1D = F, $23 = D, $2A = B: "In a cav-ern, in a can-yon,
;  ex-ca-vat-ing for a mine ..."
;-----------------------------------------------------------------------------
TUNE:           .byte $28,$06,$28,$02,$28,$04,$35,$04,$1F,$06,$1F,$02,$1F,$04,$28,$04
                .byte $28,$06,$1F,$02,$1A,$04,$1A,$04,$1D,$06,$1F,$02,$23,$08,$FE,$23
                .byte $06,$1F,$02,$1D,$04,$1D,$04,$1F,$06,$23,$02,$1F,$04,$28,$04,$28
                .byte $06,$1F,$02,$23,$04,$35,$04,$2A,$06,$23,$02,$28,$08,$FF

;-----------------------------------------------------------------------------
;  DRAW_TRANSPORTER - stations 3 and 7: draw the column of four numbered transporter
;  booths at x = A (SPECIAL_X; 0 = this station has none).
;  The digits 1-4 are drawn with the font renderer; the booths come from BOOTH_SHAPE,
;  each bit drawn as 2 pixels.
;-----------------------------------------------------------------------------
DRAW_TRANSPORTER:
                sta SPECIAL_X
                bne DT_DIGITS
                rts
DT_DIGITS:      sec                     ; text x = column - $33
                sbc #$33
                sta TXT_X
                ldx #$00                ; colour 1, normal height
                stx TXT_COLOR
                inx
                stx TXT_VSCALE
                stx TRANS_LOCK
                ldx #$9D                ; first digit ('1') at the bottom, y = $9D
                stx TXT_Y
                lda #$11                ; CNT1 = $11
                sta CNT1
DT_DIGIT:       jsr DRAW_CHAR           ; draw the digit
                lda TXT_Y               ; next booth up: 47 lines higher (DRAW_CHAR left y 8 lower)
                sec
                sbc #$37
                sta TXT_Y
                inc CNT1                ; digits '1' to '4'
                lda CNT1
                cmp #$15                ; if A <> $15 goto DT_DIGIT
                bne DT_DIGIT
                ldx #$04                ; 4 booths
                stx CNT0
                ldx #$0E                ; starting at y = 14
                stx PLOT_Y
DT_BOOTH:       ldy #$00
                sty CNT1
                sty PLOT_COLOR          ; colour 1
DT_RUN:         lda BOOTH_SHAPE,y       ; lines in this run (0 = booth done)
                beq DT_NEXT_BOOTH
                sta CNT2
                iny
                sty CNT1
DT_LINE:        lda SPECIAL_X           ; x = column - $37
                sec
                sbc #$37
                sta PLOT_X
                lda BOOTH_SHAPE,y       ; bit pattern for this run
                ldy #$08                ; 8 bits
                sty CNT3
DT_BIT:         asl a
                bcc DT_BIT_NEXT
                pha                     ; bit set: 2 pixels
                jsr PLOT                ; set pixel (PLOT_X, PLOT_Y) to colour PLOT_COLOR, replacing what was th
                ldx PLOT_Y
                ldy PLOT_X
                iny
                jsr PLOT_XY             ; set pixel (x = Y, line = X) to PLOT_COLOR
                pla
DT_BIT_NEXT:    inc PLOT_X
                inc PLOT_X
                dec CNT3                ; CNT3 -= 1, until 0
                bne DT_BIT
                inc PLOT_Y              ; next line
                ldy CNT1
                dec CNT2                ; CNT2 -= 1, until 0
                bne DT_LINE
                iny
                bne DT_RUN
DT_NEXT_BOOTH:  dec CNT0                ; CNT0 -= 1, until 0
                bne DT_BOOTH
                rts

;-----------------------------------------------------------------------------
;  DRAW_CHAR - draw character A (screen code $00-$7F) into the bitmap from the machine's
;  ROM font, at TXT_X/TXT_Y, in colour TXT_COLOR, each font row repeated TXT_VSCALE
;  times. 1 bits are drawn in the ink colour and 0 bits are cleared, so text erases what
;  was under it. On return TXT_X is unchanged and TXT_Y has moved down 8 * TXT_VSCALE
;  lines; DRAW_STRING moves on to the next character position itself.
;  The font address is FONTPAGE*256 + A*8, so the 400/800 and the 5200 each use their own
;  ROM font.
;-----------------------------------------------------------------------------
DRAW_CHAR:      ldy FONTPAGE            ; font page
DC_PAGE:        cmp #$20                ; 32 characters per page of font
                bcc DC_FOUND
                iny
                sec
                sbc #$20
                jmp DC_PAGE
DC_FOUND:       sty TXT_FONT+1
                ldy #$00
                sty TXT_FONT
                asl a                   ; offset of the character in its page
                asl a
                asl a
                sta TXT_ROW
                ldx #$08                ; 8 font rows
                stx TXT_ROWS
                lda TXT_VSCALE
DC_ROW:         pha                     ; repeat count for this row
                ldx #$08                ; 8 pixels
                stx TXT_BITS
                ldy TXT_ROW
                lda (TXT_FONT),y
DC_BIT:         asl a                   ; next bit into carry
                pha
                bcs DC_INK
                lda TXT_COLOR           ; 0 bit: draw it as background (TXT_COLOR 12) ...
                cmp #$0C                ; if A == $0C goto DC_BIT_NEXT
                beq DC_BIT_NEXT
                pha
                lda #$0C                ; TXT_COLOR = $0C
                sta TXT_COLOR
                jsr TXT_PLOT            ; PLOT for the text renderer
                pla
                sta TXT_COLOR
                jmp DC_BIT_NEXT
DC_INK:         jsr TXT_PLOT            ; 1 bit: ink
DC_BIT_NEXT:    inc TXT_X
                pla
                dec TXT_BITS            ; TXT_BITS -= 1, until 0
                bne DC_BIT
                inc TXT_Y               ; next line
                lda TXT_X               ; TXT_X = TXT_X - 8
                sec
                sbc #$08
                sta TXT_X
                pla                     ; same font row again?
                sec
                sbc #$01
                bne DC_ROW
                lda TXT_VSCALE          ; next font row
                inc TXT_ROW
                dec TXT_ROWS            ; TXT_ROWS -= 1, until 0
                bne DC_ROW
                rts

;-----------------------------------------------------------------------------
;  TXT_PLOT - PLOT for the text renderer: pixel (TXT_X - no offset, TXT_Y), colour
;  TXT_COLOR. Uses its own pointer (TXT_DST) so it can run inside other drawing.
;-----------------------------------------------------------------------------
TXT_PLOT:       ldy TXT_X
                ldx TXT_Y
                lda LINE_LO,x           ; TXT_DST = LINE_LO[X]
                sta TXT_DST
                lda LINE_HI,x           ; TXT_DST+1 = LINE_HI[X]
                sta TXT_DST+1
                tya
                and #$03
                tax
                tya
                lsr a
                lsr a
                tay
                lda PIXEL_CLEAR,x
                and (TXT_DST),y
                pha
                txa
                clc
                adc TXT_COLOR
                tax
                pla
                ora PIXEL_SET,x
                sta (TXT_DST),y
                rts

;-----------------------------------------------------------------------------
;  BOOTH_SHAPE - transporter booth as (lines, 8-bit pattern) runs, 0 = end:
;    2 x 01111110   top of the number window
;    8 x 01000010   sides of the window (the digit goes inside)
;    1 x 01111110   bottom of the window
;    2 x 11111111   roof
;   23 x 10000001   walls
;   11 x 00000000   gap to the next booth
;-----------------------------------------------------------------------------
BOOTH_SHAPE:    .byte $02,$7E,$08,$42,$01,$7E,$02,$FF,$17,$81,$0B,$00,$00

;-----------------------------------------------------------------------------
;  CHECK_OPTION - OPTION (5200: the * key) abandons everything for the high-score screen.
;-----------------------------------------------------------------------------
CHECK_OPTION:   lda IS5200              ; if IS5200 == 0 goto CO_800
                beq CO_800
                lda KEYCODE
                cmp #$02
                jmp CO_CHK
CO_800:         lda CONSOL              ; OPTION = CONSOL bit 2
                and #$04
CO_CHK:         bne CS_RTS
                jmp TITLE_SCREEN        ; the high-score screen with its ring of "chasing lights"

;-----------------------------------------------------------------------------
;  CHECK_START - START (or the button, during the demo) pressed?
;  Out: carry set = start a new game (DEMO_PTR+1 is set to 0 on the way).
;  CHECK_START_ANY skips the "only during the demo" test. START_DLY makes sure START has
;  been released for a few frames first.
;-----------------------------------------------------------------------------
CHECK_START:    lda DEMO_PTR+1          ; in a real game only START counts
                beq CS_START
CHECK_START_ANY:
                lda IS5200              ; the button counts too (not on the 5200)
                bne CS_5200
                ldy #$00
                lda (pTRIG0),y          ; A = TRIG0
                and #$01                ; test bits $01
                beq CS_PRESSED
CS_START:       lda IS5200              ; if IS5200 == 0 goto CS_800
                beq CS_800
CS_5200:        lda KEYCODE             ; 5200 START key
                cmp #$03
                jmp CS_CHK
CS_800:         lda CONSOL              ; 400/800 START key
                and #$01
CS_CHK:         beq CS_PRESSED
                lda START_DLY           ; not pressed: count the release time
                beq CS_NO
                dec START_DLY
CS_NO:          clc
                rts
CS_PRESSED:     lda #$FF                ; forget the key
                sta KEYCODE
                lda START_DLY           ; released long enough before?
                beq CS_YES
                lda #$05                ; no: start the release count again
                sta START_DLY
                bne CS_NO
CS_YES:         sta DEMO_PTR+1          ; A = 0: DEMO_PTR+1 = 0, a real game
                sec
CS_RTS:         rts

;-----------------------------------------------------------------------------
;  CANNON_WALLS - station 10: vertical 2-pixel walls (lines, y, x), 0 = end.
;-----------------------------------------------------------------------------
CANNON_WALLS:   .byte $09,$5B,$0D
                .byte $09,$5B,$29
                .byte $59,$66,$00
                .byte $43,$66,$34

;-----------------------------------------------------------------------------
;  CANNON_SHAPE - the cannon, 35 lines of (missile byte, player 3 byte): the four missiles
;  (as a "fifth player") form the left 8 pixels and player 3 the right 8. Read backwards, indexed
;  from 1 (CANNON_SHAPE,y with y = $46..1), so the pairs start at $9EF3 and $9EF2 is unused.
;-----------------------------------------------------------------------------
CANNON_SHAPE:   .byte $00
                .byte $0F,$F0           ; ....#### ####....
                .byte $0F,$F0           ; ....#### ####....
                .byte $0F,$F0           ; ....#### ####....
                .byte $0F,$F0           ; ....#### ####....
                .byte $0F,$F0           ; ....#### ####....
                .byte $0F,$F0           ; ....#### ####....
                .byte $1F,$F8           ; ...##### #####...
                .byte $1F,$F8           ; ...##### #####...
                .byte $1F,$F8           ; ...##### #####...
                .byte $1F,$F8           ; ...##### #####...
                .byte $1F,$F8           ; ...##### #####...
                .byte $1F,$F8           ; ...##### #####...
                .byte $1F,$F8           ; ...##### #####...
                .byte $1F,$F8           ; ...##### #####...
                .byte $1F,$F8           ; ...##### #####...
                .byte $3F,$FC           ; ..###### ######..
                .byte $3F,$FC           ; ..###### ######..
                .byte $3F,$FC           ; ..###### ######..
                .byte $3F,$FC           ; ..###### ######..
                .byte $FF,$FF           ; ######## ########
                .byte $FF,$FF           ; ######## ########
                .byte $BF,$FD           ; #.###### ######.#
                .byte $BF,$FD           ; #.###### ######.#
                .byte $BF,$FD           ; #.###### ######.#
                .byte $9F,$F9           ; #..##### #####..#
                .byte $8F,$F1           ; #...#### ####...#
                .byte $83,$C1           ; #.....## ##.....#
                .byte $C1,$83           ; ##.....# #.....##
                .byte $61,$86           ; .##....# #....##.
                .byte $30,$0C           ; ..##.... ....##..
                .byte $18,$18           ; ...##... ...##...
                .byte $1F,$F8           ; ...##### #####...
                .byte $1F,$F8           ; ...##### #####...
                .byte $1E,$78           ; ...####. .####...
                .byte $1E,$78           ; ...####. .####...

;-----------------------------------------------------------------------------
;  SETUP_CANNON - station 10 ("The Cannon"): put the cannon into player 3 + missiles at
;  x = $A1, write "TNT Charge=   0 Tons", and draw the TNT store (shelves, walls and its
;  "TNT" sign) and the cannon's track.
;-----------------------------------------------------------------------------
SETUP_CANNON:   lda #$A1                ; cannon starts at x = $A1
                sta CANNON_X
                ldy #$46                ; copy the shape, 35 lines, into P/M rows $B9-$DB
                ldx #$23
SC_COPY:        lda CANNON_SHAPE,y      ; player 3 byte
                sta $07B8,x
                dey
                lda CANNON_SHAPE,y      ; missile byte
                sta $03B8,x
                dey
                dex                     ; loop until X = 0
                bne SC_COPY
                lda #$00                ; colour 1 for text and lines
                sta TXT_COLOR
                sta PLOT_COLOR
                ldx #$A5                ; "TNT Charge=   0 Tons"
                stx TXT_IDX
                lda #$01                ; TXT_VSCALE = 1
                sta TXT_VSCALE
                ldx #$00                ; at x = 0, y = 13, 20 characters
                ldy #$0D
                lda #$14
                jsr DRAW_STRING         ; draw A characters of TEXT_POOL, starting at TXT_IDX, at x = X, y = Y
                ldy #$0D                ; shelves of the TNT store: lines $59/$5A and $64/$65
                ldx #$59
                lda #$1E
                jsr DRAW_HLINE          ; horizontal line of A pixels
                ldy #$0D
                ldx #$5A
                lda #$1E
                jsr DRAW_HLINE          ; horizontal line of A pixels
                ldy #$00
                ldx #$64
                lda #$36
                jsr DRAW_HLINE          ; horizontal line of A pixels
                ldy #$00
                ldx #$65
                lda #$36
                jsr DRAW_HLINE          ; horizontal line of A pixels
                ldy #$00                ; the store's walls from CANNON_WALLS
SC_WALL:        sty CNT1
                lda CANNON_WALLS,y      ; lines (0 = end)
                beq SC_SIGN
                sta CNT4
                lda CANNON_WALLS+1,y    ; y
                sta PLOT_Y
                lda CANNON_WALLS+2,y    ; x
                sta PLOT_X
SC_WALL_LINE:   jsr PLOT                ; 2 pixels wide
                inc PLOT_X
                jsr PLOT                ; set pixel (PLOT_X, PLOT_Y) to colour PLOT_COLOR, replacing what was th
                dec PLOT_X
                inc PLOT_Y
                dec CNT4                ; CNT4 -= 1, until 0
                bne SC_WALL_LINE
                ldy CNT1
                iny
                iny
                iny
                bne SC_WALL
SC_SIGN:        lda #$04                ; colour 2 ...
                sta TXT_COLOR
                sta PLOT_COLOR
                ldx #$A5                ; ... "TNT" (the first 3 characters of the same string)
                stx TXT_IDX
                lda #$01                ; TXT_VSCALE = 1
                sta TXT_VSCALE
                ldx #$10                ; at x = $10, y = $5C
                ldy #$5C
                lda #$03
                jsr DRAW_STRING         ; draw A characters of TEXT_POOL, starting at TXT_IDX, at x = X, y = Y
                lda #$40                ; the cannon's track starts at x = $40

;-----------------------------------------------------------------------------
;  DRAW_TRACK - rails on lines $BC/$BD from pixel x = A, 62 pixels long, plus sleepers
;  (2 pixels on, 2 off) on line $BE. Also used for the lift's track on station 8.
;-----------------------------------------------------------------------------
DRAW_TRACK:     pha
                tay
                ldx #$BC
                lda #$3E
                jsr DRAW_HLINE          ; horizontal line of A pixels
                pla
                pha
                tay
                ldx #$BD
                lda #$3E
                jsr DRAW_HLINE          ; horizontal line of A pixels
                ldy #$BE                ; sleepers on line $BE
                sty PLOT_Y
                pla
                sta PLOT_X
                lda #$10                ; 16 sleepers
                sta CNT3
DT_SLEEPER:     jsr PLOT                ; set pixel (PLOT_X, PLOT_Y) to colour PLOT_COLOR, replacing what was th
                inc PLOT_X
                jsr PLOT                ; set pixel (PLOT_X, PLOT_Y) to colour PLOT_COLOR, replacing what was th
                inc PLOT_X              ; 4 pixels per sleeper
                inc PLOT_X
                inc PLOT_X
                dec CNT3                ; CNT3 -= 1, until 0
                bne DT_SLEEPER
                rts

;-----------------------------------------------------------------------------
;  DRAW_WASTE - station 6 ("Radioactive Waste"): a solid box (lines $9E-$BE, x 20-139)
;  with 2-pixel edges in colour 2, and "DANGER / Radioactive / Waste" cut into it in the
;  background colour.
;-----------------------------------------------------------------------------
DRAW_WASTE:     ldx #$00                ; colour 1
                stx PLOT_COLOR
                ldx #$9E                ; 33 lines from $9E ...
                lda #$21                ; CNT2 = $21
                sta CNT2
DW_FILL:        ldy #$14                ; ... each from x = 20, 120 pixels long
                lda #$78
                jsr DRAW_HLINE          ; horizontal line of A pixels
                ldx PLOT_X
                inx
                dec CNT2                ; CNT2 -= 1, until 0
                bne DW_FILL
                ldy #$00                ; colour 2 edges at the x positions in WASTE_EDGES
                sty CNT2
                ldy #$04
                sty PLOT_COLOR
DW_EDGE:        ldy CNT2
                lda WASTE_EDGES,y       ; if WASTE_EDGES[Y] == 0 goto DW_TEXT
                beq DW_TEXT
                sta PLOT_X
                iny
                sty CNT2
                lda #$21                ; 33 lines
                sta CNT3
                ldx #$9E
                stx PLOT_Y
DW_EDGE_LINE:   jsr PLOT                ; set pixel (PLOT_X, PLOT_Y) to colour PLOT_COLOR, replacing what was th
                inc PLOT_Y
                dec CNT3                ; CNT3 -= 1, until 0
                bne DW_EDGE_LINE
                beq DW_EDGE
DW_TEXT:        ldx #$0C                ; text in the background colour (12)
                stx TXT_COLOR
                ldx #$00                ; string 0 of TEXT_POOL
                stx TXT_IDX
                lda #$01                ; normal height
                sta TXT_VSCALE
                ldx #$38                ; "DANGER" at ($38, $A2)
                ldy #$A2
                lda #$06
                jsr DRAW_STRING         ; draw A characters of TEXT_POOL, starting at TXT_IDX, at x = X, y = Y
                ldx #$24                ; "Radioactive" at ($24, $AD)
                ldy #$AD
                lda #$0B
                jsr DRAW_STRING         ; draw A characters of TEXT_POOL, starting at TXT_IDX, at x = X, y = Y
                ldx #$3C                ; "Waste" at ($3C, $B5)
                ldy #$B5
                lda #$05

;-----------------------------------------------------------------------------
;  DRAW_STRING - draw A characters of TEXT_POOL, starting at TXT_IDX, at x = X, y = Y.
;  DRAW_STRING_Y is the same with TXT_X already set. Characters are 8 pixels apart;
;  TXT_IDX is left pointing after the string, so strings can be drawn one after another.
;-----------------------------------------------------------------------------
DRAW_STRING:    sta TXT_LEN
                stx TXT_X
DRAW_STRING_Y:  sty TXT_Y
DSTR_LOOP:      ldy TXT_IDX             ; next character
                lda TEXT_POOL,y
                jsr DRAW_CHAR           ; draw character A (screen code $00-$7F) into the bitmap from the machin
                lda TXT_X               ; move right 8 pixels ...
                clc
                adc #$08
                sta TXT_X
                lda TXT_Y               ; ... and back up to the same top line (8 or 16 lines)
                sec
                sbc #$08
                ldx TXT_VSCALE
                dex
                beq DSTR_NEXT
                sbc #$08
DSTR_NEXT:      sta TXT_Y
                inc TXT_IDX
                dec TXT_LEN             ; TXT_LEN -= 1, until 0
                bne DSTR_LOOP
                rts
WASTE_EDGES:    .byte $12,$13,$8C,$8D,$00

;-----------------------------------------------------------------------------
;  GET_BOB_FRAME - SPR_PTR = address of Bob's animation frame BOB_FRAME.
;-----------------------------------------------------------------------------
GET_BOB_FRAME:  ldx BOB_FRAME
                lda BOB_FRAME_HI,x      ; SPR_PTR+1 = BOB_FRAME_HI[X]
                sta SPR_PTR+1
                lda BOB_FRAME_LO,x      ; SPR_PTR = BOB_FRAME_LO[X]
                sta SPR_PTR
                rts

;-----------------------------------------------------------------------------
;  DRAW_BOB - copy Bob's current frame into players 0, 1 and 2 at height BOB_Y.
;  Bob is three overlaid single-colour players, which gives him three colours (hat and
;  coat, face and hands, legs and boots ...). A frame holds the three layers back to back
;  (20, 17 and 17 lines) with neighbouring layers sharing a byte, 51 bytes in all. Copying
;  backwards with the extra blank lines at the ends also erases his previous position.
;-----------------------------------------------------------------------------
DRAW_BOB:       jsr GET_BOB_FRAME       ; SPR_PTR = address of Bob's animation frame BOB_FRAME
                lda BOB_Y               ; player 0: 20 lines, bottom at row BOB_Y + $32
                clc
                adc #$32
                tax
                ldy #$14
DB_P0:          lda (SPR_PTR),y         ; TITLE_KERNEL[X] = (SPR_PTR)[Y]
                sta TITLE_KERNEL,x
                dex
                dey                     ; loop until Y = 0
                bne DB_P0
                lda #$13                ; next layer starts 19 bytes on
                jsr ADD_SPR_PTR         ; SPR_PTR = SPR_PTR + A
                txa                     ; player 1: 17 lines, bottom at row BOB_Y + $2F
                clc
                adc #$11
                tax
                ldy #$11
DB_P1:          lda (SPR_PTR),y         ; PM_P1[X] = (SPR_PTR)[Y]
                sta PM_P1,x
                dex
                dey                     ; loop until Y = 0
                bne DB_P1
                txa                     ; player 2: 17 lines, bottom at row BOB_Y + $35
                clc
                adc #$17
                tax
                ldy #$11
                lda #$10                ; next layer starts 16 bytes on
                jsr ADD_SPR_PTR         ; SPR_PTR = SPR_PTR + A
DB_P2:          lda (SPR_PTR),y         ; PM_P2[X] = (SPR_PTR)[Y]
                sta PM_P2,x
                dex
                dey                     ; loop until Y = 0
                bne DB_P2
                rts

;-----------------------------------------------------------------------------
;  SHOW_BOB - draw Bob (upside down once he has been fired from the cannon), and on
;  station 10 hide his legs while he stands inside the loaded cannon.
;-----------------------------------------------------------------------------
SHOW_BOB:       lda CANNON_DONE         ; fired from the cannon?
                bne DRAW_BOB_FLIPPED
                jsr DRAW_BOB            ; copy Bob's current frame into players 0, 1 and 2 at height BOB_Y
HIDE_IN_CANNON: lda STATION             ; station 10 only
                cmp #$0A                ; if A <> $0A goto HIC_RTS
                bne HIC_RTS
                lda CANNON_ST           ; already inside?
                bne HIC_HIDE
                lda TNT                 ; TNT loaded?
                beq HIC_RTS
                lda BOB_FRAME           ; walking or standing?
                cmp #$07                ; if A >= 7 goto HIC_RTS
                bcs HIC_RTS
                lda CANNON_X            ; level with the cannon's mouth ...
                clc
                adc #$04
                cmp BOB_X               ; if A <> BOB_X goto HIC_RTS
                bne HIC_RTS
                lda BOB_Y               ; ... and at its height?
                cmp #$7C                ; if A < $7C goto HIC_RTS
                bcc HIC_RTS
                cmp #$92                ; if A >= $92 goto HIC_RTS
                bcs HIC_RTS
HIC_HIDE:       ldy #$0B                ; blank P/M rows $B9-$C3 of players 0-2 (the cannon covers him)
                lda #$00
HIC_LOOP:       sta $04B8,y
                sta $05B8,y
                sta $06B8,y
                dey                     ; loop until Y = 0
                bne HIC_LOOP
HIC_RTS:        rts

;-----------------------------------------------------------------------------
;  DRAW_BOB_FLIPPED - as DRAW_BOB but copying forwards, so Bob is upside down (flying
;  out of the cannon head first). Blank lines are written at both ends.
;-----------------------------------------------------------------------------
DRAW_BOB_FLIPPED:
                jsr GET_BOB_FRAME       ; SPR_PTR = address of Bob's animation frame BOB_FRAME
                lda BOB_Y
                clc
                adc #$1F
                tax
                ldy #$03                ; 3 blank lines above
                lda #$00
DBF_CLR0:       sta TITLE_KERNEL,x
                inx
                dey                     ; loop until Y = 0
                bne DBF_CLR0
                ldy #$14                ; then player 0's 20 lines, top to bottom
DBF_P0:         lda (SPR_PTR),y         ; TITLE_KERNEL[X] = (SPR_PTR)[Y]
                sta TITLE_KERNEL,x
                inx
                dey                     ; loop until Y = 0
                bne DBF_P0
                lda #$13
                jsr ADD_SPR_PTR         ; SPR_PTR = SPR_PTR + A
                txa                     ; player 1
                sec
                sbc #$17
                tax
                ldy #$06                ; 6 blank lines
                lda #$00
DBF_CLR1:       sta PM_P1,x
                inx
                dey                     ; loop until Y = 0
                bne DBF_CLR1
                ldy #$11
DBF_P1:         lda (SPR_PTR),y         ; PM_P1[X] = (SPR_PTR)[Y]
                sta PM_P1,x
                inx
                dey                     ; loop until Y = 0
                bne DBF_P1
                txa                     ; player 2
                sec
                sbc #$17
                tax
                ldy #$11
                lda #$10
                jsr ADD_SPR_PTR         ; SPR_PTR = SPR_PTR + A
DBF_P2:         lda (SPR_PTR),y         ; PM_P2[X] = (SPR_PTR)[Y]
                sta PM_P2,x
                inx
                dey                     ; loop until Y = 0
                bne DBF_P2
                ldy #$08                ; 8 blank lines below
                lda #$00
DBF_CLR2:       sta PM_P2,x
                inx
                dey                     ; loop until Y = 0
                bne DBF_CLR2
                jmp HIDE_IN_CANNON      ; station 10: hide Bob's legs inside the loaded cannon

;-----------------------------------------------------------------------------
;  SPARKLE_BOB - draw Bob, then AND every line of his three players with a random number,
;  so he appears as a cloud of flickering dots (transporter beam, death).
;-----------------------------------------------------------------------------
SPARKLE_BOB:    jsr DRAW_BOB            ; copy Bob's current frame into players 0, 1 and 2 at height BOB_Y
                ldx #$15                ; 21 lines
                stx CNT5
                ldx BOB_Y
                ldy #$00
SB_LOOP:        lda KERNEL_LINE+27,x
                and (pSKRES),y          ; A &= RANDOM
                sta KERNEL_LINE+27,x
                lda PM_P1+32,x
                and (pSKRES),y          ; A &= RANDOM
                sta PM_P1+32,x
                lda PM_P2+32,x
                and (pSKRES),y          ; A &= RANDOM
                sta PM_P2+32,x
                inx
                dec CNT5                ; CNT5 -= 1, until 0
                bne SB_LOOP
                rts

;-----------------------------------------------------------------------------
;  ADD_SPR_PTR - SPR_PTR = SPR_PTR + A.
;-----------------------------------------------------------------------------
ADD_SPR_PTR:    clc
                adc SPR_PTR
                sta SPR_PTR
                bcc ASP_RTS
                inc SPR_PTR+1
ASP_RTS:        rts

;-----------------------------------------------------------------------------
;  COLD_START - power-up / RESET entry (cartridge init vector at $BFFE).
;
;  The cartridge's option byte ($BFFD) is $FF. On the 400/800 its bit 7 makes this a
;  "diagnostic" cartridge: the OS jumps here straight after RESET, before initialising
;  anything, so the game owns the whole machine. On the 5200 the same $FF tells the BIOS
;  to skip its title screen and jump through the same address. One ROM image therefore
;  boots on both machines, and the code below works out which one it is on:
;
;    $F800-$F80F all $00 or $18?  -> those are the first two glyphs (space and '!') of the
;    5200 BIOS font, so this is a 5200. On the 400/800 that address holds OS code.
;
;  It then builds the hardware pointer table at $10-$6F:
;    $10+2r -> GTIA register r     ($D000+r on the 400/800, $C000+r on the 5200)
;    $50+2r -> POKEY register r    ($D200+r on the 400/800, $E800+r on the 5200)
;  and from then on every GTIA/POKEY access goes "LDA (pTRIG0),Y"-style through it. ANTIC
;  sits at $D400 on both machines and is addressed directly.
;-----------------------------------------------------------------------------
COLD_START:     ldy #$01                ; starting zone 1
                sty START_ZONE
                dey                     ; Y = 0
                sty NMIEN               ; no NMIs
                sei                     ; no IRQs
                sty DMACTL              ; no DMA
                sty CHEAT_IDX           ; phone-number code: nothing typed yet
                cld
                ldx #$0F                ; look at $F800-$F80F
PWR_DETECT:     lda FONT_5200,x         ; if FONT_5200[X] == 0 goto PWR_DETECT_NEXT
                beq PWR_DETECT_NEXT
                cmp #$18                ; if A <> $18 goto PWR_MACHINE
                bne PWR_MACHINE         ; something else: a 400/800
PWR_DETECT_NEXT:
                dex
                bpl PWR_DETECT
                sty WARMST              ; 5200: there is no warm-start flag, so force "cold" (clear the high scores)
                iny                     ; Y = 1
PWR_MACHINE:    tya
                sta IS5200              ; 0 = 400/800, 1 = 5200
                beq PWR_800
                ldy #$C0                ; 5200: GTIA page $C0, POKEY page $E8, font at $F800
                lda #$E8
                ldx #$F8
                bne PWR_TABLE
PWR_800:        ldy #$D0                ; 400/800: GTIA page $D0, POKEY page $D2, font at $E000
                lda #$D2
                ldx #$E0
PWR_TABLE:      stx FONTPAGE
                pha
                lda #$00                ; 32 pointers to GTIA registers 0-31 at $10-$4F
                tax
PWR_GTIA:       sta pHPOSP0,x
                sty pHPOSP0+1,x
                clc
                adc #$01
                inx
                inx
                cpx #$40                ; if X <> $40 goto PWR_GTIA
                bne PWR_GTIA
                pla                     ; 16 pointers to POKEY registers 0-15 at $50-$6F
                tay
                lda #$00
PWR_POKEY:      sta pHPOSP0,x
                sty pHPOSP0+1,x
                clc
                adc #$01
                inx
                inx
                cpx #$60                ; if X <> $60 goto PWR_POKEY
                bne PWR_POKEY
                lda WARMST              ; power-on (not RESET): clear the high-score table
                bne PWR_TEXT
                ldx #$C8
PWR_CLEAR_HI:   sta HISCORES-1,x
                dex                     ; loop until X = 0
                bne PWR_CLEAR_HI
                nop                     ; three NOPs: room left for a patch
                nop
                nop
PWR_TEXT:       ldx #$28                ; copy "Press START For a 1 Miner Game" to TEXT_RAM
PWR_TEXT_LOOP:  lda TITLE_TEXT-1,x      ; TEXT_RAM-1[X] = TITLE_TEXT-1[X]
                sta TEXT_RAM-1,x
                dex                     ; loop until X = 0
                bne PWR_TEXT_LOOP
                stx TWO_PLAYER          ; one player

;-----------------------------------------------------------------------------
;  RESTART - the cartridge's start address ($BFFA). Starts the attract sequence: the
;  opening credits on station 11, played from the DEMO_CREDITS recording.
;-----------------------------------------------------------------------------
RESTART:        jsr HW_RESET            ; silence and blank everything
                jsr INIT_PLAYERS        ; fresh player variables
                lda #$0B                ; station 11 = the credits screen
                sta STATION
                ldx #$02                ; recording 2 (DEMO_CREDITS)
SET_DEMO:       lda DEMO_TABLE,x        ; DEMO_PTR = DEMO_TABLE[X]
                sta DEMO_PTR
                lda DEMO_TABLE+1,x      ; DEMO_PTR+1 = DEMO_TABLE+1[X]
                sta DEMO_PTR+1

;-----------------------------------------------------------------------------
;  PLAY_STATION - build STATION and run it until the turn ends.
;-----------------------------------------------------------------------------
PLAY_STATION:   jsr HW_RESET            ; silence and blank everything
                jsr BUILD_STATION       ; build the station (prepare screen, drawing, start-up)
                lda STATION             ; the credits screen has its own loop
                cmp #$0B                ; if A <> $0B goto GAME_LOOP
                bne GAME_LOOP
                jmp CREDITS_LOOP        ; station 11, the opening credits

;-----------------------------------------------------------------------------
;  GAME_LOOP - foreground loop while a station is played. All the action happens in the
;  vertical-blank interrupt (GAME_VBI); this loop only watches the keys and waits for the
;  turn to end (ALIVE = 0) or the station's end-of-station wipe to finish (WIPE_LINE = 0).
;-----------------------------------------------------------------------------
GAME_LOOP:      lda ALIVE               ; turn over?
                beq TURN_OVER
                lda DEMO_PTR+1          ; demo: a digit key starts a real game
                beq GL_KEYS
                jsr CHECK_ZONE_KEY      ; on the title screens a digit key starts a one-player game at that zone
GL_KEYS:        jsr SHOW_TNT            ; station 10: show the TNT charge
                lda IS5200              ; if IS5200 <> 0 goto GL_START
                bne GL_START
                jsr CHECK_OPTION        ; OPTION -> high-score screen (400/800)
GL_START:       jsr CHECK_START         ; START (or the button during the demo) -> new game
                bcc GL_WIPE
                jmp START_GAME          ; start a game (DEMO_PTR+1 = 0) or the demo (DEMO_PTR+1 <> 0)
GL_WIPE:        lda WIPE_LINE           ; station cleared and the screen wiped away?
                bne GAME_LOOP
                sta NMIEN               ; next station: NMIs off (A = 0)
                ldx STATION
                inx
                cpx #$0B                ; after station 10 ...
                bcc GL_STATION
                ldx #$01                ; ... back to station 1 of the next zone
                ldy ZONE
                iny
                beq GL_STATION          ; (the zone stops at 255)
                sty ZONE
GL_STATION:     stx STATION
                lda DEMO_PTR+1          ; demo: back to the credits
                beq PLAY_STATION
                jmp RESTART             ; the cartridge's start address ($BFFA)

;-----------------------------------------------------------------------------
;  TURN_OVER - Bob has died. If that was his last life, show "Game Over / Miner n" in a
;  box with a little siren of sound; then hand over to the next player, or end the game.
;-----------------------------------------------------------------------------
TURN_OVER:      lda LIVES               ; lives left?
                beq GAME_OVER_BOX
                jmp TURN_NEXT
GAME_OVER_BOX:  ldx #$28                ; fill a box (x 40-119, lines $5C-$6B) in colour 3, column by column
                stx PLOT_X
                jsr SILENCE             ; all four voices off (SILENCE_234 leaves voice 1 alone; A must be 0)
                ldx #$08
                stx PLOT_COLOR
                lda #$AF                ; voices 1 and 2: pure tone, volume 15 (X = 8 makes these AUDC1/AUDC2)
                sta (pGRACTL,x)
                sta (pCONSOL,x)
GOB_COLUMN:     ldx #$5C
                stx PLOT_Y
                lda FRAMES              ; one column per frame
GOB_WAIT:       cmp FRAMES              ; if A == FRAMES goto GOB_WAIT
                beq GOB_WAIT
GOB_PIXEL:      lda PLOT_X              ; two tones that rise with the column
                sec
                sbc #$1E
                ldy #$00
                sta (pAUDF1),y          ; AUDF1 = A
                adc #$6D
                sta (pAUDF2),y          ; AUDF2 = A
                jsr PLOT                ; set pixel (PLOT_X, PLOT_Y) to colour PLOT_COLOR, replacing what was th
                ldx #$00                ; status line stops blinking
                stx CHACTL
                dex
                stx BLINK_TMR
                inc PLOT_Y
                ldx PLOT_Y
                cpx #$6C                ; if X <> $6C goto GOB_PIXEL
                bne GOB_PIXEL
                inc PLOT_X
                ldy PLOT_X
                cpy #$78                ; if Y <> $78 goto GOB_COLUMN
                bne GOB_COLUMN
                lda #$00                ; silence voice 2; voice 1 to a low hum
                tay
                sta (pAUDC2),y          ; AUDC2 = A
                lda #$6F                ; AUDC1 = $6F
                sta (pAUDC1),y          ; AUDC1 = A
                sta PLOT_Y
                lda #$FF                ; AUDF1 = $FF
                sta (pAUDF1),y          ; AUDF1 = A
                lda #$32                ; PLOT_X = $32
                sta PLOT_X
                lda #$0C                ; text in the background colour, cut into the box
                sta TXT_COLOR
                ldx #$97                ; "Game Over" (TEXT_POOL + $97)
                stx TXT_IDX
                lda #$01                ; TXT_VSCALE = 1
                sta TXT_VSCALE
                ldx #$2C
                ldy #$5C
                lda #$09
                jsr DRAW_STRING         ; draw A characters of TEXT_POOL, starting at TXT_IDX, at x = X, y = Y
                ldx #$34                ; "Miner" below it
                ldy #$64
                lda #$05
                jsr DRAW_STRING         ; draw A characters of TEXT_POOL, starting at TXT_IDX, at x = X, y = Y
                ldx #$64                ; then the player's number
                stx TXT_X
                lda PLAYER
                clc
                adc #$11
                jsr DRAW_CHAR           ; draw character A (screen code $00-$7F) into the bitmap from the machin
                lda FRAMES              ; wait 3 seconds while the hum fades
                adc #$B4
                tax
GOB_FADE:       lda FRAMES
GOB_FADE_WAIT:  cmp FRAMES              ; if A == FRAMES goto GOB_FADE_WAIT
                beq GOB_FADE_WAIT
                dec PLOT_X              ; every 4 frames ...
                bne GOB_FADE_NEXT
                lda #$04                ; PLOT_X = 4
                sta PLOT_X
                lda PLOT_Y              ; ... one step quieter (down to volume 0)
                cmp #$60                ; if A == $60 goto GOB_FADE_NEXT
                beq GOB_FADE_NEXT
                sec
                sbc #$01
                sta PLOT_Y
                ldy #$00
                sta (pAUDC1),y          ; AUDC1 = A
GOB_FADE_NEXT:  cpx FRAMES              ; if X <> FRAMES goto GOB_FADE
                bne GOB_FADE
TURN_NEXT:      jsr NEXT_PLAYER         ; after a turn
                jmp PLAY_STATION        ; build STATION and run it until the turn ends

;-----------------------------------------------------------------------------
;  NEXT_PLAYER - after a turn: in the demo go back to the credits; in a two-player game
;  swap to the other player if he has lives left; otherwise carry on, or if nobody has
;  lives left, enter the high scores and show the high-score screen.
;-----------------------------------------------------------------------------
NEXT_PLAYER:    lda DEMO_PTR+1          ; demo?
                beq NP_REAL
                jmp RESTART             ; the cartridge's start address ($BFFA)
NP_REAL:        lda a:$00C3             ; the other player still in the game?
                beq NP_ALONE
                ldx #$0A                ; swap STATION..SCORE ($B7-$C0) with the other player's copy ($C1-$CA)
NP_SWAP:        lda PLAYER+1,x
                ldy a:$00C0,x
                sty PLAYER+1,x
                sta a:$00C0,x
                dex                     ; loop until X = 0
                bne NP_SWAP
                lda #$01                ; PLAYER = 1 - PLAYER
                sec
                sbc PLAYER
                sta PLAYER
NP_GO:          lda #$00                ; a life will be taken when the turn starts
                sta LIFE_USED
                rts
NP_ALONE:       lda LIVES               ; this player still has lives?
                bne NP_GO
                jsr HISCORE_CHECK       ; everybody is out: high-score table ...
                jmp TITLE_SCREEN        ; ... and the high-score screen

;-----------------------------------------------------------------------------
;  CREDITS_LOOP - station 11, the opening credits. The credits ("MINER 2049er / By /
;  Bill Hogue / Starring "Bounty Bob" / Copyright (C) 1982 By / Big Five Software / ...
;  (213) 782-6861") were drawn at the start in pixel colour 1, whose colour register is
;  black, so they are invisible. As Bob (driven by DEMO_CREDITS) walks along the girders,
;  GAME_VBI repaints every colour-1 pixel in a band around him in colour 2, so the words
;  appear in his wake. When he reaches the bottom right corner the rest is revealed, a
;  DLI rainbow starts on the copyright lines, and the game-over tune plays.
;-----------------------------------------------------------------------------
CREDITS_LOOP:   lda #$05                ; START_DLY = 5
                sta START_DLY
CL_LOOP:        jsr CHECK_ZONE_KEY      ; digit: start a game in that zone
                jsr CHECK_START_ANY     ; START or the button: start a game
                bcc CL_WAIT
                jmp START_GAME          ; start a game (DEMO_PTR+1 = 0) or the demo (DEMO_PTR+1 <> 0)
CL_WAIT:        jsr CHECK_OPTION        ; OPTION: high-score screen
                ldx BOB_X               ; has Bob reached the bottom right?
                cpx #$C8                ; if X < $C8 goto CL_LOOP
                bcc CL_LOOP
                ldy BOB_Y
                cpy #$9F                ; if Y < $9F goto CL_LOOP
                bcc CL_LOOP
                lda VCOUNT              ; wait until the beam is half way down the screen
                cmp #$3F                ; if A < $3F goto CL_LOOP
                bcc CL_LOOP
                lda #$00                ; stop the VBI, footsteps off
                tay
                sta NMIEN
                sta (pAUDC3),y          ; AUDC3 = A
                lda COLPF1_V            ; colour 1 = the revealed-text colour: everything not yet uncovered appears
                                        ;   ...
                sta (pCOLPF0),y         ; COLPF0 = A
                jsr DRAW_CREDITS        ; ... and the credits are drawn again on top
                lda COLPF1_V            ; colour for the rainbow DLI
                sta PLOT_COLOR
                ldx #$C2
                stx CNT3
                ldx #$AB                ; DLI = DLI_RAINBOW
                ldy #$B3
                jsr SET_DLI             ; install a display-list-interrupt handler
                lda #$80                ; DLI only (no VBI)
                sta NMIEN
                jmp GAME_OVER_TUNE      ; play Clementine, then the high-score screen
ST_RTS:         rts

;-----------------------------------------------------------------------------
;  SHOW_TNT - station 10: print the TNT charge ("TNT Charge=  nn Tons") on the status
;  text, and print "DANGER" (at pixel $48, line $35) once 4 or more tons are loaded.
;-----------------------------------------------------------------------------
SHOW_TNT:       lda STATION
                cmp #$0A                ; if A <> $0A goto ST_RTS
                bne ST_RTS
                lda SECTIONS            ; station finished?
                beq ST_RTS
                lda TNT                 ; 4 tons or more?
                cmp #$04                ; if A < 4 goto ST_NUMBER
                bcc ST_NUMBER
                ldy #$04                ; "DANGER" in colour 2 at ($48, $35)
                sty TXT_COLOR
                ldx #$01
                stx CNT4
                dex
                stx TXT_IDX
                ldx #$48
                ldy #$35
                lda #$06
                jsr DRAW_STRING         ; draw A characters of TEXT_POOL, starting at TXT_IDX, at x = X, y = Y
ST_NUMBER:      ldy #$00                ; colour 1
                sty TXT_COLOR
                lda CANNON_ST           ; fired, or nothing loaded: show 0
                cmp #$02                ; if A == 2 goto ST_ZERO
                beq ST_ZERO
                lda TNT                 ; if TNT == 0 goto ST_ZERO
                beq ST_ZERO
                ldx #$00                ; tens and units
ST_TENS:        cmp #$0A                ; if A < $0A goto ST_DIGITS
                bcc ST_DIGITS
                sbc #$0A
                inx
                bne ST_TENS
ST_DIGITS:      pha
                txa                     ; tens digit (blank if 0)
                beq ST_TENS_OUT
                clc
                adc #$10
ST_TENS_OUT:    jsr ST_TENS_X           ; draw the tens digit A at x = $60
                pla                     ; units digit
                clc
                adc #$10
ST_UNITS:       ldx #$68                ; at x = $68
ST_DRAW:        stx TXT_X
                ldy #$0D                ; y = 13
                sty TXT_Y
                jmp DRAW_CHAR           ; draw character A (screen code $00-$7F) into the bitmap from the machin
ST_ZERO:        lda #$00                ; "0"
                jsr ST_UNITS            ; draw the units digit A at x = $68
                lda #$00                ; and a blank tens digit
ST_TENS_X:      ldx #$60                ; at x = $60
                bne ST_DRAW

;-----------------------------------------------------------------------------
;  INIT_PLAYERS - both players to station 1, zone 1, 3 lives, extra life pending, score 0
;  (from PLAYER_INIT). In a one-player game player 2 gets no lives.
;-----------------------------------------------------------------------------
INIT_PLAYERS:   ldx #$0A
IP_LOOP:        lda IP_RTS,x            ; PLAYER+1[X] = IP_RTS[X]
                sta PLAYER+1,x
                sta a:$00C0,x
                dex                     ; loop until X = 0
                bne IP_LOOP
                stx PLAYER              ; player 1 first
                stx LIFE_USED
                lda TWO_PLAYER          ; if TWO_PLAYER <> 0 goto IP_RTS
                bne IP_RTS
                sta a:$00C3             ; one player: the other player has no lives
IP_RTS:         rts

;-----------------------------------------------------------------------------
;  PLAYER_INIT - STATION, ZONE, LIVES, XLIFE, SCORE (6 digits).
;-----------------------------------------------------------------------------
PLAYER_INIT:    .byte $01,$01,$03,$0A,$00,$00,$00,$00,$00,$00

;-----------------------------------------------------------------------------
;  HISCORE_CHECK - after a game, offer the high-score table to both players' scores,
;  the higher score first (so the two never compete for the same slot out of order).
;-----------------------------------------------------------------------------
HISCORE_CHECK:  lda #$00                ; screen off
                sta NMIEN
                tay
                sta DMACTL
                sta (pGRACTL),y         ; GRACTL = A
                jsr HIDE_PLAYERS        ; players to x = 0 (off screen)
                ldy #$0A                ; Y = 10 = player 2's offset if his score is higher
                ldx #$00
HC_COMPARE:     lda SCORE,x             ; compare the two scores digit by digit
                cmp P2_DATA+4,x         ; ; player 2's digit
                bcc HC_ORDER
                bne HC_P1
                inx
                cpx #$06                ; if X <> 6 goto HC_COMPARE
                bne HC_COMPARE
HC_P1:          ldy #$00                ; player 1 is higher
HC_ORDER:       sty PTR
                jsr INSERT_SCORE        ; the higher score ...
                lda #$0A                ; ... then the other one
                sec
                sbc PTR
                sta PTR
                jmp INSERT_SCORE        ; put the score at SCORE+CNT1(=PTR) (player 1

;-----------------------------------------------------------------------------
;  INSERT_SCORE - put the score at SCORE+CNT1(=PTR) (player 1: offset 0, player 2: 10)
;  into the high-score table if it beats an entry, and ask for a name.
;  Table lines are 20 screen-code characters; the score sits at columns 11-17 as
;  "nnn,nnn" with leading zeros blank. The top line is shown in ANTIC mode 7, whose
;  characters carry their colour in bits 6-7, so its digits are $50-$59, not $10-$19.
;-----------------------------------------------------------------------------
INSERT_SCORE:   ldx PTR
                ldy #$06                ; a score of zero is never entered
                lda #$00
IS_ZERO:        ora SCORE,x
                inx
                dey                     ; loop until Y = 0
                bne IS_ZERO
                cmp #$00                ; if A == 0 goto IS_RTS
                beq IS_RTS
                lda #$50                ; line 0 digits are $50-$59
                sta PLOT_COLOR
                lda #$0A                ; 10 lines
                sta PTR+1
                lda #$00
IS_LINE:        sta CNT0
                tay
                lda #$06                ; 6 digits
                sta CNT1
                ldx PTR
IS_DIGIT:       lda HISCORES+11,y       ; table digit (blank counts as 0)
                sec
                sbc PLOT_COLOR
                cmp #$0A                ; if A < $0A goto IS_CMP
                bcc IS_CMP
                lda #$00
IS_CMP:         cmp SCORE,x             ; if A < SCORE[X] goto IS_INSERT
                bcc IS_INSERT           ; the new score is higher: insert here
                bne IS_NEXT_LINE        ; lower: try the next line
                inx                     ; equal: next digit
                iny
                dec CNT1                ; CNT1 -= 1, goto IS_NEXT_LINE if 0
                beq IS_NEXT_LINE
                lda CNT1
                cmp #$03                ; if A <> 3 goto IS_DIGIT
                bne IS_DIGIT
                iny                     ; skip the comma
                bne IS_DIGIT
IS_NEXT_LINE:   lda #$10                ; lines 1-9 use plain digits
                sta PLOT_COLOR
                lda CNT0
                clc
                adc #$14
                dec PTR+1               ; PTR+1 -= 1, until 0
                bne IS_LINE
IS_RTS:         rts
IS_INSERT:      lda #$B4                ; move the lines below down by one (20 bytes)
                sec
                sbc CNT0
                beq IS_CLEAR
                tax
                ldy #$B3
IS_MOVE:        lda HISCORES,y          ; HISCORES+20[Y] = HISCORES[Y]
                sta HISCORES+20,y
                dey
                dex                     ; loop until X = 0
                bne IS_MOVE
IS_CLEAR:       ldx #$14                ; clear the new line
                lda #$00
                ldy CNT0
IS_CLEAR_LOOP:  sta HISCORES,y
                iny
                dex                     ; loop until X = 0
                bne IS_CLEAR_LOOP
                ldx PTR                 ; write the score into it
                ldy CNT0
                lda #$06                ; CNT1 = 6
                sta CNT1
                lda #$00                ; no digit written yet (leading zeros stay blank)
                sta PTR+1
IS_WRITE:       lda SCORE,x             ; if SCORE[X] <> 0 goto IS_DIGIT_OUT
                bne IS_DIGIT_OUT
                lda PTR+1               ; if PTR+1 == 0 goto IS_WRITE_NEXT
                beq IS_WRITE_NEXT
                lda #$00
IS_DIGIT_OUT:   clc                     ; digit -> screen code
                adc #$10
                sta HISCORES+11,y
                sta PTR+1
IS_WRITE_NEXT:  iny
                inx
                dec CNT1                ; CNT1 -= 1, goto IS_NAME if 0
                beq IS_NAME
                lda CNT1                ; after 3 digits: comma (if any digit has been written)
                cmp #$03                ; if A <> 3 goto IS_WRITE
                bne IS_WRITE
                lda PTR+1               ; if PTR+1 == 0 goto IS_COMMA
                beq IS_COMMA
                lda #$0C
IS_COMMA:       sta HISCORES+11,y
                iny
                bne IS_WRITE
IS_NAME:        lda CNT0
                pha                     ; ask for the name
                jsr NAME_ENTRY          ; "MINER 1 / great score! / enter your name
                pla                     ; new top score?
                bne IS_RTS2
                ldx #$10                ; yes: line 0 to the mode 7 colour ...
IS_RECOLOUR0:   lda HISCORES+1,x        ; HISCORES+1[X] = HISCORES+1[X] + $40
                clc
                adc #$40
                sta HISCORES+1,x
                dex                     ; loop until X = 0
                bne IS_RECOLOUR0
                ldx #$10                ; ... and the old top line, now line 1, back to plain codes
IS_RECOLOUR1:   lda HISCORES+21,x       ; HISCORES+21[X] = HISCORES+21[X] - $40
                sec
                sbc #$40
                sta HISCORES+21,x
                dex                     ; loop until X = 0
                bne IS_RECOLOUR1
IS_RTS2:        rts

;-----------------------------------------------------------------------------
;  BUILD_STATION - show the "prepare for station" screen, then draw STATION from its
;  description and set everything up for play.
;
;  STATION_TABLE (8 bytes per station, indexed by station number) gives the addresses of
;  four lists: ladders, slides, moving platforms and girders. Three more tables indexed by
;  station give Bob's start position and the transporter column, and two word tables
;  give the item list and the mutant list. Stations with machinery (6, 8, 9, 10) get extra
;  set-up code.
;-----------------------------------------------------------------------------
BUILD_STATION:  jsr PREPARE_SCREEN      ; prepare screen (also builds the empty game screen)
                lda STATION             ; X = station * 8
                asl a
                asl a
                asl a
                tax
BS_FILLER:      lda #$4C                ; two instructions with no effect (5 bytes of filler; $4C is the JMP opcode,
                lda BS_FILLER           ; so this may be space reserved for a patch)
                lda STATION_TABLE,x     ; ladder list
                sta LADDERS
                lda STATION_TABLE+1,x   ; LADDERS+1 = STATION_TABLE+1[X]
                sta LADDERS+1
                lda STATION_TABLE+2,x   ; slide list
                sta SLIDES
                lda STATION_TABLE+3,x   ; SLIDES+1 = STATION_TABLE+3[X]
                sta SLIDES+1
                lda STATION_TABLE+4,x   ; moving-platform list
                sta LIFTS
                lda STATION_TABLE+5,x   ; LIFTS+1 = STATION_TABLE+5[X]
                sta LIFTS+1
                lda STATION_TABLE+6,x   ; girder list (Y/X = lo/hi)
                tay
                lda STATION_TABLE+7,x
                tax
                lda #$03                ; girders sloping down ...
                jsr DRAW_GIRDERS        ; draw the station's girders (floors) and count their sections
                lda #$05                ; ... sloping up ...
                jsr DRAW_GIRDERS_MORE   ; continue drawing girders with slope A
                lda #$00                ; (lift x = 0: no lift)
                sta LIFT_X
                jsr DRAW_GIRDERS_MORE   ; ... and flat
                jsr DRAW_LADDERS        ; draw the station's ladders (list at LADDERS) in colour 2
                jsr DRAW_SLIDES         ; draw the station's slides (chutes) from the list at SLIDES
                jsr INIT_LIFTS          ; copy the moving platforms (6-byte records, list at LIFTS) to LIFT_TAB
                ldx STATION             ; Bob's starting position
                lda BOB_START_X,x       ; BOB_X = BOB_START_X[X]
                sta BOB_X
                lda BOB_START_Y,x       ; BOB_Y = BOB_START_Y[X]
                sta BOB_Y
                lda TRANS_COLUMN,x      ; transporter column (0 = none)
                jsr DRAW_TRANSPORTER    ; stations 3 and 7
                lda STATION             ; word tables: X = station * 2
                asl a
                tax
                lda MUTANT_LISTS,x      ; mutant list
                sta MUTANTS
                lda MUTANT_LISTS+1,x    ; MUTANTS+1 = MUTANT_LISTS+1[X]
                sta MUTANTS+1
                lda ITEM_LISTS,x        ; item list
                sta PTR
                lda ITEM_LISTS+1,x      ; PTR+1 = ITEM_LISTS+1[X]
                sta PTR+1
                jsr SETUP_ITEMS         ; draw the items
                lda #$FF                ; mask = $FF: copy the mutants ...
                ldx STATION
                cpx #$0B                ; if X < $0B goto BS_MUTANTS
                bcc BS_MUTANTS
                lda #$00                ; ... except on the credits screen (mask 0: no mutants)
BS_MUTANTS:     sta START_DLY
                ldy #$00
                lda #$08                ; 8 mutant records
                sta CNT3
BS_MUT_REC:     ldx #$0B                ; 11 bytes each
BS_MUT_BYTE:    lda (MUTANTS),y
                and START_DLY
                sta MUT_TAB,y
                iny
                dex                     ; loop until X = 0
                bne BS_MUT_BYTE
                lda (pSKRES,x)          ; X = 0, so (pSKRES,x) reads RANDOM: a random colour, never too dark
                and #$F6
                ora #$02
                sta ITEMS+38,y          ; byte 3 of the record just copied = current colour
                sta ITEMS+36,y          ; byte 1 = its normal colour
                dec CNT3                ; CNT3 -= 1, until 0
                bne BS_MUT_REC
                lda STATION             ; station 6: the radioactive waste box
                cmp #$06                ; if A <> 6 goto BS_SPECIAL
                bne BS_SPECIAL
                jsr DRAW_WASTE          ; station 6 ("Radioactive Waste")
BS_SPECIAL:     lda STATION             ; credits screen: nothing more
                cmp #$0B                ; if A <> $0B goto BS_SPECIAL2
                bne BS_SPECIAL2
                jmp BS_FLOOR
BS_SPECIAL2:    cmp #$08                ; if A == 8 goto BS_LIFT
                beq BS_LIFT             ; station 8: the lift
                cmp #$0A                ; if A <> $0A goto BS_SPECIAL3
                bne BS_SPECIAL3
                jsr SETUP_CANNON        ; station 10: the cannon and the TNT store
                jmp BS_BONUS
BS_SPECIAL3:    cmp #$09                ; if A <> 9 goto BS_SPECIAL_DONE
                bne BS_SPECIAL_DONE
                jsr SETUP_PULVERIZERS   ; station 9: the pulverizers
BS_SPECIAL_DONE:
                jmp BS_BONUS
BS_LIFT:        ldx #$07                ; station 8: the lift's cart (7 lines from LIFT_CART into player 3)
BS_LIFT_CART:   lda LIFT_CART-1,x       ; $07D4[X] = LIFT_CART-1[X]
                sta $07D4,x
                dex                     ; loop until X = 0
                bne BS_LIFT_CART
                lda #$96                ; lift at x = $96, platform on line $A0
                sta LIFT_X
                lda #$A0                ; LIFT_Y = $A0
                sta LIFT_Y
                lda #$04                ; colour 2 for its track
                sta PLOT_COLOR
                ldx #$02                ; the scissor arms: P/M rows $A1-$B4 of player 3, from LIFT_SCISSOR
                ldy #$B4
BS_SCISSOR:     lda LIFT_SCISSOR,x      ; PM_P3+32[Y] = LIFT_SCISSOR[X]
                sta PM_P3+32,y
                dey
                dex
                bpl BS_SCISSOR_NEXT
                ldx #$06
BS_SCISSOR_NEXT:
                cpy #$A1                ; if Y <> $A1 goto BS_SCISSOR
                bne BS_SCISSOR
                inx                     ; animation phase it was left at
                stx LIFT_ANIM
                lda #$FF                ; two solid lines for the platform
                sta PM_P3+32,y
                sta PM_P3+31,y
                lda #$3A                ; its track at x = $3A
                jsr DRAW_TRACK          ; rails and sleepers from x = A
BS_BONUS:       lda #$10                ; bonus "0000" on the status line
                ldx #$04
BS_BONUS_ZERO:  sta STATUS+17,x
                dex                     ; loop until X = 0
                bne BS_BONUS_ZERO
                ldx STATION             ; bonus (hundreds) = BONUS_BASE[station] + 5 * zone, at most 99
                lda BONUS_BASE,x
                ldx ZONE
BS_BONUS_ADD:   clc
                adc #$05
                bcs BS_BONUS_MAX
                dex                     ; loop until X = 0
                bne BS_BONUS_ADD
                cmp #$64                ; if A < $64 goto BS_BONUS_TENS
                bcc BS_BONUS_TENS
BS_BONUS_MAX:   lda #$63
BS_BONUS_TENS:  cmp #$0A                ; tens digit
                bcc BS_BONUS_UNITS
                sec
                sbc #$0A
                inc STATUS+18           ; STATUS+18 += 1, until 0
                bne BS_BONUS_TENS
BS_BONUS_UNITS: adc #$10                ; units digit (carry is clear: + $10)
                sta STATUS+19
BS_FLOOR:       ldx #$F0                ; bonus timer: first tick after 240 frames
                stx BONUS_TMR
                ldx #$08                ; the bottom floor: one line, colour 3, the full 160 pixels
                stx PLOT_COLOR
                ldy #$00
                ldx #$BF
                lda #$A0
                jsr DRAW_HLINE          ; horizontal line of A pixels
                jmp START_STATION       ; carry on: colours, variables, NMIs

;-----------------------------------------------------------------------------
;  LIFT_SCISSOR - the lift's scissor arms: a 7-line cycle drawn down the lift's column of
;  player 3, starting at the phase LIFT_ANIM so the arms seem to fold and unfold.
;-----------------------------------------------------------------------------
LIFT_SCISSOR:   .byte $18,$24,$42,$81,$42,$24,$18; ...##... ..#..#.. .#....#. #......# .#....#. ..#..#.. ...##...

;-----------------------------------------------------------------------------
;  LIFT_CART - the lift's cart (7 lines). Its last line, the wheels, is the first byte of
;  BONUS_BASE, which no station uses: the two tables overlap by one byte.
;-----------------------------------------------------------------------------
LIFT_CART:      .byte $7E,$7E,$FF,$FF,$FF,$66; .######. .######. ######## ######## ######## .##..##.

;-----------------------------------------------------------------------------
;  BONUS_BASE - starting bonus for each station, in hundreds, before adding 5 per zone.
;  Index 0 is the cart's wheels; station 10 reads one past the end, the $41 at the start
;  of TRANS_COLUMN (so its bonus starts at 6500 + 500 per zone).
;-----------------------------------------------------------------------------
BONUS_BASE:     .byte $66,$19,$1E,$23,$28,$2D,$32,$37,$28,$3C

;-----------------------------------------------------------------------------
;  TRANS_COLUMN - x of the transporter column per station (0 = none); stations 3 and 7.
;  (Station 11 reads one past the end: BOB_START_X's first byte, 0.)
;-----------------------------------------------------------------------------
TRANS_COLUMN:   .byte $41,$00,$00,$7A,$00,$00,$00,$43,$00,$00,$00

;-----------------------------------------------------------------------------
;  BOB_START_X / BOB_START_Y - where Bob starts on each station (index 1-11). Station 11
;  reads BOB_START_X one past the end, i.e. BOB_START_Y's unused first byte, $30.
;-----------------------------------------------------------------------------
BOB_START_X:    .byte $00,$34,$8A,$AF,$3A,$30,$39,$30,$B1,$C8,$C3
BOB_START_Y:    .byte $30,$AA,$AA,$AA,$AA,$AA,$AA,$AA,$8B,$05,$AA,$0F

;-----------------------------------------------------------------------------
;  SETUP_ITEMS - copy the station's items to ITEMS and draw them.
;  List entry: shape (bit 7 set = present), y, x (pixels). The shape number selects an
;  entry of ITEM_SHAPES: width, height, points, then the picture as whole bytes (4 pixels
;  per byte, 2 bits per pixel), copied straight into the bitmap. x is rounded down to a
;  multiple of 4 so items sit on byte boundaries.
;-----------------------------------------------------------------------------
SETUP_ITEMS:    ldy #$00
SI_LOOP:        lda (PTR),y             ; shape (0 = end of list)
                sta ITEMS,y
                beq BL_RTS
                and #$7F
                asl a
                tax
SI_FILLER:      lda NMI_EXIT            ; three instructions with no effect (8 bytes of filler)
                lda #$4C
                lda SI_FILLER
                lda ITEM_SHAPES,x       ; address of the shape
                sta CNT3
                lda ITEM_SHAPES+1,x     ; CNT4 = ITEM_SHAPES+1[X]
                sta CNT4
                iny                     ; y
                lda (PTR),y             ; ITEMS[Y] = (PTR)[Y]
                sta ITEMS,y
                tax                     ; line address
                lda LINE_LO,x           ; CNT0 = LINE_LO[X]
                sta CNT0
                lda LINE_HI,x           ; CNT1 = LINE_HI[X]
                sta CNT1
                iny                     ; x, rounded to a byte
                lda (PTR),y
                and #$FC
                sta ITEMS,y
                iny
                sty PLOT_X
                jsr ADD_X_BYTES         ; + x/4
                jsr BLIT_SHAPE          ; copy the picture
                ldy PLOT_X              ; if PLOT_X <> 0 goto SI_LOOP
                bne SI_LOOP

;-----------------------------------------------------------------------------
;  BLIT_SHAPE - copy the item picture at (CNT3) to the bitmap at (CNT0), byte by byte.
;-----------------------------------------------------------------------------
BLIT_SHAPE:     ldy #$00                ; width in pixels -> bytes
                lda (CNT3),y
                jsr WIDTH_BYTES         ; PLOT_Y = number of bytes covering A pixels = (A - 1) / 4 + 1
                iny                     ; height
                lda (CNT3),y            ; CNT2 = (CNT3)[Y]
                sta CNT2
                iny                     ; skip the points byte
                iny
BL_LINE:        ldx PLOT_Y
                lda #$00                ; PIX_PTR+1 = 0
                sta PIX_PTR+1
BL_BYTE:        lda (CNT3),y
                sty PIX_PTR
                ldy PIX_PTR+1
                sta (CNT0),y
                inc PIX_PTR+1
                ldy PIX_PTR
                iny
                dex                     ; loop until X = 0
                bne BL_BYTE
                jsr NEXT_LINE_PTR       ; next line
                bne BL_LINE
BL_RTS:         rts

;-----------------------------------------------------------------------------
;  ITEM_ADDR - CNT0/CNT1 = bitmap address of item X (offset into ITEMS).
;  ADD_X_BYTES adds A/4 to CNT0.
;-----------------------------------------------------------------------------
ITEM_ADDR:      lda ITEMS+1,x           ; line
                tay
                lda LINE_LO,y           ; CNT0 = LINE_LO[Y]
                sta CNT0
                lda LINE_HI,y           ; CNT1 = LINE_HI[Y]
                sta CNT1
                lda ITEMS+2,x           ; + x/4
ADD_X_BYTES:    lsr a
                lsr a
                clc
                adc CNT0
                bcc AXB_STORE
                inc CNT1
AXB_STORE:      sta CNT0
                rts

;-----------------------------------------------------------------------------
;  WIDTH_BYTES - PLOT_Y = number of bytes covering A pixels = (A - 1) / 4 + 1.
;-----------------------------------------------------------------------------
WIDTH_BYTES:    sec
                sbc #$01
                lsr a
                lsr a
                clc
                adc #$01
                sta PLOT_Y
                rts

;-----------------------------------------------------------------------------
;  NEXT_LINE_PTR - CNT0/CNT1 += 40 (one bitmap line), CNT2 -= 1.
;-----------------------------------------------------------------------------
NEXT_LINE_PTR:  lda #$28                ; CNT0 = $28 + CNT0
                clc
                adc CNT0
                sta CNT0
                bcc NLP_COUNT
                inc CNT1
NLP_COUNT:      dec CNT2
                rts

;-----------------------------------------------------------------------------
;  UPDATE_ITEMS - every frame (from GAME_VBI): pick up items Bob touches.
;  ITEMS[n+0]: bit 7 set = item present. When Bob touches it, the item is replaced by its
;  points value ("100" .. "500", "1100" for the BF logo), the score goes up by
;  points x 100, mutants become edible (ITEM_GOT), and the byte becomes a countdown from
;  $55: while it runs a falling whistle plays on voice 4; at 1 the points are erased.
;  On station 10 the points of a TNT bundle are also added to the charge (1-3 tons).
;  On station 5 the goblet (shape $21) is poisoned: touching it kills Bob.
;-----------------------------------------------------------------------------
UPDATE_ITEMS:   ldx #$80                ; a meaningless sequence: compares a ROM byte with itself minus 5 and
                                        ;   ignores the
                stx PTR+1               ; result; the NOPs suggest a check that was patched out
                lda (PTR),y
                sbc #$05
                nop
                nop
                cmp (PTR),y             ; if A <> (PTR)[Y] goto UI_START
                bne UI_START
                nop
                nop
UI_START:       ldx #$00
UI_LOOP:        lda ITEMS,x             ; 0 = end of list
                bne UI_ENTRY
                rts
UI_ENTRY:       bmi UI_PRESENT          ; present?
                sec                     ; counting down after a pick-up
                sbc #$01
                beq UI_NEXT             ; (stays at 1 = gone)
                sta ITEMS,x
                cmp #$01                ; at 1: erase the points
                bne UI_WHISTLE
                jmp UI_ERASE_POINTS
UI_WHISTLE:     ldy SECTIONS            ; the whistle (not after the station is cleared)
                beq UI_NEXT
                ldy #$00
                sec                     ; only during the first 31 frames
                sbc #$36
                bcc UI_NEXT
                beq UI_VOL
                asl a                   ; pitch falls as the count goes down
                asl a
                asl a
                sta CNT1
                lda #$FF                ; AUDF4 = $FF - CNT1
                sec
                sbc CNT1
                sta (pAUDF4),y          ; AUDF4 = A
                ldy #$A8                ; pure tone, volume 8
UI_VOL:         tya
                ldy #$00
                sta (pAUDC4),y          ; AUDC4 = A
UI_NEXT:        inx                     ; next item
                inx
                inx
                bne UI_LOOP
UI_PRESENT:     ldy DYING               ; not while Bob is dying or in the transporter
                bne UI_NEXT
                ldy SPECIAL             ; if SPECIAL <> 0 goto UI_NEXT
                bne UI_NEXT
                and #$7F                ; shape
                jsr SHAPE_ADDR          ; CNT3/CNT4 = address of item shape A
                ldy #$00                ; horizontal: centre of the item within 8 of Bob's x?
                lda (CNT3),y
                lsr a
                clc
                adc ITEMS+2,x
                adc #$30
                sec
                sbc BOB_X
                cmp #$08                ; if A >= 8 goto UI_NEXT
                bcs UI_NEXT
                iny                     ; vertical: does Bob's body overlap the item's lines?
                lda (CNT3),y
                clc
                adc ITEMS+1,x
                adc #$20
                sta CNT1
                lda BOB_Y
                adc #$20
                cmp CNT1                ; if A >= CNT1 goto UI_NEXT
                bcs UI_NEXT
                sta CNT1
                lda ITEMS+1,x
                adc #$0C
                cmp CNT1                ; if A >= CNT1 goto UI_NEXT
                bcs UI_NEXT
                lda ITEMS,x             ; touched: the goblet on station 5 kills
                cmp #$A1                ; if A <> $A1 goto UI_COLLECT
                bne UI_COLLECT
                lda STATION
                cmp #$05                ; if A <> 5 goto UI_COLLECT
                bne UI_COLLECT
                sta KILLED              ; KILLED = 5
UI_COLLECT:     lda #$55                ; start the countdown
                sta ITEMS,x
                dey                     ; width, height and points of the shape
                lda (CNT3),y
                pha
                iny
                lda (CNT3),y
                pha
                iny
                lda (CNT3),y
                pha
                jsr SHAPE_ADDR          ; the points value is itself a shape number: draw it over the item
                jsr ITEM_ADDR           ; CNT0/CNT1 = bitmap address of item X (offset into ITEMS)
                jsr BLIT_SHAPE          ; copy the item picture at (CNT3) to the bitmap at (CNT0), byte by byte
                lda STATION             ; station 10: TNT bundles add their tons
                cmp #$0A                ; if A <> $0A goto UI_SCORE
                bne UI_SCORE
                pla
                pha
                clc
                adc TNT
                sta TNT
UI_SCORE:       pla                     ; score += points * 100 (digit 4 = hundreds)
                ldx #$04
                stx ITEM_GOT            ; and the mutants turn edible
                jsr ADD_SCORE           ; add A to score digit X (1 = 100,000s
                pla                     ; height
                tay
                pla                     ; width
                cpy #$06                ; taller than the 5-line number? erase the rest of the item below it
                bcc CB_RTS
                jsr WIDTH_BYTES         ; PLOT_Y = number of bytes covering A pixels = (A - 1) / 4 + 1
                tya
                sec
                sbc #$05
CLEAR_BLOCK:    sta CNT2                ; lines
CB_LINE:        ldx PLOT_Y
                ldy #$00
                tya
CB_BYTE:        sta (CNT0),y
                iny
                dex                     ; loop until X = 0
                bne CB_BYTE
                jsr NEXT_LINE_PTR       ; CNT0/CNT1 += 40 (one bitmap line), CNT2 -= 1
                bne CB_LINE
CB_RTS:         rts
UI_ERASE_POINTS:
                txa                     ; erase the 3-byte, 5-line points number
                pha
                jsr ITEM_ADDR           ; CNT0/CNT1 = bitmap address of item X (offset into ITEMS)
                lda #$03                ; PLOT_Y = 3
                sta PLOT_Y
                lda #$05
                jsr CLEAR_BLOCK         ; clear CNT2 lines of PLOT_Y bytes at (CNT0)
                pla
                tax
                lda SECTIONS            ; whistle off (unless the station is over: the bonus count owns voice 4)
                beq UI_ERASE_DONE
                lda #$00
                tay
                sta (pAUDC4),y          ; AUDC4 = A
UI_ERASE_DONE:  jmp UI_NEXT

;-----------------------------------------------------------------------------
;  SHAPE_ADDR - CNT3/CNT4 = address of item shape A.
;-----------------------------------------------------------------------------
SHAPE_ADDR:     asl a
                tay
                lda ITEM_SHAPES,y       ; CNT3 = ITEM_SHAPES[Y]
                sta CNT3
                lda ITEM_SHAPES+1,y     ; CNT4 = ITEM_SHAPES+1[Y]
                sta CNT4
                rts

;-----------------------------------------------------------------------------
;  PREP_VBI - vertical blank of the "MINER 1 / PREPARE FOR / STATION 1 / ZONE 1" screen.
;  Every 30 frames FRAMES counts down (it starts at 6: three seconds). The background
;  flashes red/black with a two-tone siren, and the station line flickers through random
;  colours. The station is drawn behind this screen meanwhile.
;-----------------------------------------------------------------------------
PREP_VBI:       lda #$22                ; DMACTL: normal playfield, display list on, no P/M
                sta DMACTL
                lda #$09                ; display list at $0978 (built by PREPARE_SCREEN)
                sta DLISTH
                lda #$78                ; DLISTL = $78
                sta DLISTL
                ldx #$04                ; fine scroll used to centre some lines
                stx HSCROL
                dec BCD_100             ; every 30 frames ...
                bne PV_COLOURS
                ldx #$1E
                stx BCD_100
                dec FRAMES              ; ... count down
PV_COLOURS:     lda FRAMES              ; odd or even second?
                and #$01                ; test bits $01
                beq PV_EVEN
                ldx #$42                ; red background, siren note $96, zone line black
                ldy #$00
                lda #$96
                bne PV_SET
PV_EVEN:        ldx #$00                ; black background, siren note $4B, zone line orange
                ldy #$48
                lda #$4B
PV_SET:         pha
                tya
                ldy #$00
                sta (pCOLPF3),y         ; COLPF3: "ZONE n"
                txa
                sta (pCOLBK),y          ; COLBK
                pla
                sta (pAUDF1),y          ; siren
                lda #$AF                ; AUDC1 = $AF
                sta (pAUDC1),y          ; AUDC1 = A
                lda #$88                ; COLPF0: "MINER n"
                sta (pCOLPF0),y         ; COLPF0 = A
                lda #$C4                ; COLPF1: "PREPARE FOR"
                sta (pCOLPF1),y         ; COLPF1 = A
                lda (pSKRES),y          ; COLPF2: "STATION n", a random colour every frame
                sta (pCOLPF2),y         ; COLPF2 = A
                jmp NMI_EXIT            ; common tail of every interrupt handler

;-----------------------------------------------------------------------------
;  NAME_ENTRY - "MINER 1 / great score! / enter your name. / >>        <<"
;  The player types up to 8 characters (400/800 keyboard), or on the 5200 picks letters
;  with the stick and enters them with the fire button. RETURN / START / the 5200's lower
;  button ends entry, and so does a time limit (60 s; 120 s on the 5200).
;  Each character goes both into the name on screen ($095E) and straight into the
;  high-score line at HISCORES + CNT0 + 2. The whole thing runs in NAME_VBI; this routine
;  sets up and waits for CNT4 to become non-zero.
;-----------------------------------------------------------------------------
NAME_ENTRY:     ldy #$54                ; copy the screen text (84 bytes from NAME_TEXT)
NE_TEXT:        lda NAME_TEXT-1,y       ; $0917[Y] = NAME_TEXT-1[Y]
                sta $0917,y
                dey                     ; loop until Y = 0
                bne NE_TEXT
                tya                     ; clear the missiles ($0300-$03FF): they form the cursor
NE_CLEAR:       sta PM_MISSILES,y
                iny
                bne NE_CLEAR
                lda IS5200              ; 5200: copy its ROM font to RAM at $1C00 so one glyph can be changed
                beq NE_PLAYER
                sty PLOT_Y
                sty CNT3
                lda #$F8                ; CNT2 = $F8
                sta CNT2
                lda #$1C                ; CNT4 = $1C
                sta CNT4
                sta CHBASE
                ldx #$02                ; 512 bytes = the first 64 characters
NE_FONT:        lda (PLOT_Y),y          ; (CNT3)[Y] = (PLOT_Y)[Y]
                sta (CNT3),y
                iny
                bne NE_FONT
                inc CNT2
                inc CNT4
                dex                     ; loop until X = 0
                bne NE_FONT
                ldx #$07                ; character $3E (the "delete" choice) gets the glyph at $FAF0
NE_GLYPH:       lda $FAF0,x             ; $1DF0[X] = $FAF0[X]
                sta $1DF0,x
                dex
                bpl NE_GLYPH
NE_PLAYER:      lda PLAYER              ; "MINER n": which player's score is this?
                ldx PTR                 ; if PTR == 0 goto NE_PLAYER_SET
                beq NE_PLAYER_SET
                lda #$01
                sec
                sbc PLAYER
NE_PLAYER_SET:  clc                     ; digit with colour bits ($91 = '1' in colour 2)
                adc #$91
                sta $0926
                ldx #$08                ; X = 8: (pAUDF4,x) is (pSKRES) = RANDOM: a random hue for the rainbow
                lda (pAUDF4,x)
                and #$F0
                ora #$0A
                sta PLOT_COLOR
                stx PTR+1
                stx PLOT_Y
                lda #$00                ; name length 0, no repeat, not finished
                sta CNT1
                sta CNT2
                sta CNT4
                sta COLBK_V
                sta COLPF0_V
                sta NAME_RPT
                jsr SILENCE_234         ; silence voices 2-4
                ldx #$21                ; 5200 letter starts at 'A'
                stx LASTCHAR
                ldx #$FF                ; cursor: two solid missile rows
                stx $03CF
                stx $03D0
                stx KEYCODE             ; no key
                ldx #$C2
                stx CNT3
                lda #$02                ; opening beep sweep
                sta PLOT_X
                sta START_DLY           ; START must be released first
                tax                     ; X = 2: (pCONSOL,x) = (pAUDF1): AUDF1 = 2
                sta (pCONSOL,x)
                lda #$8F                ; and (pAUDF1,x) = (pAUDC1): pure tone, volume 15
                sta (pAUDF1,x)
                lda #$FF                ; no key held
                sta COLPF1_V
                lda #$3C                ; one second ...
                sta NAME_DLY
                sta COLPF2_V
                ldx IS5200              ; ... and 60 of them (120 on the 5200) before giving up
                beq NE_LIMIT
                asl a
NE_LIMIT:       sta BLINK_TMR
                ldx #$A9                ; VBI = NAME_VBI
                ldy #$A9
                jsr SET_VBI             ; install a vertical-blank interrupt handler
                ldx #$AB                ; DLI = DLI_NAME
                ldy #$78
                jsr SET_DLI             ; install a display-list-interrupt handler
                lda #$C0                ; NMIEN = $C0
                sta NMIEN
NE_WAIT:        lda CNT4                ; wait for NAME_VBI to finish
                beq NE_WAIT
                lda #$00                ; NMIEN = 0
                sta NMIEN
NE_RTS:         rts

;-----------------------------------------------------------------------------
;  NAME_DLIST - display list of the name-entry screen, also copied to $0978 for the
;  "prepare" screen: 7 x 8 blank lines (the 5th requests the DLI), then four mode 7 text
;  lines with blank lines between them, starting at $0918, then JVB $0978.
;-----------------------------------------------------------------------------
NAME_DLIST:     .byte $70               ; 8 blank lines
                .byte $70               ; 8 blank lines
                .byte $70               ; 8 blank lines
                .byte $70               ; 8 blank lines
                .byte $F0               ; 8 blank lines +DLI
                .byte $70               ; 8 blank lines
                .byte $70               ; 8 blank lines
                .byte $57,$18,$09       ; mode 7 LMS $0918 +HSCROL
                .byte $70               ; 8 blank lines
                .byte $70               ; 8 blank lines
                .byte $70               ; 8 blank lines
                .byte $70               ; 8 blank lines
                .byte $70               ; 8 blank lines
                .byte $70               ; 8 blank lines
                .byte $07               ; mode 7
                .byte $70               ; 8 blank lines
                .byte $70               ; 8 blank lines
                .byte $07               ; mode 7
                .byte $70               ; 8 blank lines
                .byte $70               ; 8 blank lines
                .byte $07               ; mode 7
                .byte $41,$78,$09       ; JVB $0978

;-----------------------------------------------------------------------------
;  NAME_VBI - runs the whole name entry, once per frame.
;-----------------------------------------------------------------------------
NAME_VBI:       jsr POLL_KEYS           ; called at the start of every VBI handler
                lda #$A9                ; display list
                sta DLISTH
                lda #$8F                ; DLISTL = $8F
                sta DLISTL
                lda #$36                ; DMACTL: normal playfield, missiles on, single-line P/M
                sta DMACTL
                jsr READ_POTS           ; 5200: read the analog stick
                jsr READ_STICK          ; stick, 400/800 or 5200 format
                ldy #$FF                ; 5200 letter choice: left = -1 ...
                lsr a
                lsr a
                lsr a
                bcc NV_REPEAT
                ldy #$01                ; ... right = +1
                lsr a
                bcc NV_REPEAT
                lda #$00                ; centred: reset the auto-repeat
                sta NAME_RPT
                beq NV_COLOURS
NV_REPEAT:      inc NAME_RPT            ; first frame moves at once, then after 40 frames every 8
                lda NAME_RPT
                cmp #$01                ; if A == 1 goto NV_MOVE
                beq NV_MOVE
                cmp #$28                ; if A < $28 goto NV_COLOURS
                bcc NV_COLOURS
                lda #$20                ; NAME_RPT = $20
                sta NAME_RPT
NV_MOVE:        tya                     ; new letter, kept within $00-$3E
                clc
                adc LASTCHAR
                bmi NV_COLOURS
                cmp #$3F                ; if A >= $3F goto NV_COLOURS
                bcs NV_COLOURS
                sta LASTCHAR
NV_COLOURS:     lda #$00                ; black background, playfield colour 2 black
                tay
                sta (pCOLBK),y          ; COLBK = A
                sta (pCOLPF2),y         ; COLPF2 = A
                lda #$01                ; missile DMA on (the cursor)
                sta (pGRACTL),y         ; GRACTL = A
                lda #$46                ; text colours
                sta (pCOLPF0),y         ; COLPF0 = A
                lda #$86                ; cursor colour (missiles use COLPF3 in fifth-player mode)
                sta (pCOLPF3),y         ; COLPF3 = A
                ldx COLBK_V             ; key click: switch off after 5 frames
                beq NV_RAINBOW
                dec COLBK_V             ; COLBK_V -= 1, until 0
                bne NV_RAINBOW
                dex
                txa
                sta (pAUDC2,x)          ; X = 0 here: AUDC2 = 0
NV_RAINBOW:     dec PTR+1               ; every 15 frames move the rainbow on one hue (skipping grey)
                bne NV_KEYS
                ldx #$03
                stx PTR+1
                dec CNT3                ; CNT3 -= 1, until 0
                bne NV_KEYS
                ldx #$05
                stx CNT3
                lda PLOT_COLOR
                clc
                adc #$10
                cmp #$0A                ; if A <> $0A goto NV_RAINBOW_SET
                bne NV_RAINBOW_SET
                lda #$1A
NV_RAINBOW_SET: sta PLOT_COLOR
NV_KEYS:        jsr CHECK_START_ANY     ; START (or the button on the 400/800) finishes
                bcs NV_FINISH
                ldy #$00
                lda IS5200              ; which machine?
                beq NV_800_KEY
                lda (pSKCTL),y          ; 5200: lower button (SKSTAT bit 3) finishes, once NAME_DLY has run out
                and #$08                ; test bits $08
                bne NV_5200_FIRE
                lda NAME_DLY            ; if NAME_DLY == 0 goto NV_FINISH
                beq NV_FINISH
                lda #$3C                ; NAME_DLY = $3C
                sta NAME_DLY
NV_5200_FIRE:   lda (pTRIG0),y          ; 5200: fire button enters the chosen letter
                bne NV_RELEASED
                ldx #$21                ; (code of the space key, $21, or of DELETE, $34, if the "delete" glyph is
                                        ;   chosen)
                lda LASTCHAR
                cmp #$3E                ; if A <> $3E goto NV_5200_RPT
                bne NV_5200_RPT
                ldx #$34
NV_5200_RPT:    inc COLPF0_V            ; only on the first frame of the press
                lda COLPF0_V
                cmp #$01                ; if A <> 1 goto NV_REPEAT_CHK
                bne NV_REPEAT_CHK
                beq NV_CHAR
NV_800_KEY:     lda KEYCODE             ; 400/800: a new key?
                cmp #$FF                ; if A <> $FF goto NV_NEW_KEY
                bne NV_NEW_KEY
                lda (pSKCTL),y          ; none: is the last key still held down?
                and #$04                ; test bits $04
                beq NV_HELD
NV_RELEASED:    jmp NV_NO_REPEAT
NV_HELD:        ldx COLPF1_V            ; held: auto-repeat after 40 frames
                cpx #$FF                ; if X <> $FF goto NV_REPEAT_KEY
                bne NV_REPEAT_KEY
NV_TAIL_J:      jmp NV_CURSOR
NV_REPEAT_KEY:  inc COLPF0_V
                lda COLPF0_V
NV_REPEAT_CHK:  cmp #$28                ; if A <> $28 goto NV_TAIL_J
                bne NV_TAIL_J
                lda #$21                ; COLPF0_V = $21
                sta COLPF0_V
                bne NV_RETURN
NV_NEW_KEY:     and #$3F                ; new key: remember it
                sta COLPF1_V
                tax
                lda #$FF                ; KEYCODE = $FF
                sta KEYCODE
                lda #$00                ; COLPF0_V = 0
                sta COLPF0_V
NV_RETURN:      cpx #$0C                ; RETURN finishes
                bne NV_CHAR
NV_FINISH:      ldx #$0C
                jmp NV_SET_DONE
NV_CHAR:        cpx #$34                ; DELETE?
                beq NV_DELETE
                ldy CNT1                ; name full (8 characters)? low buzz
                lda #$FA
                cpy #$08                ; if Y == 8 goto NV_BEEP
                beq NV_BEEP
                lda KEY_TO_SCREEN,x     ; key code -> screen code
                beq NV_STORE
                cmp #$1C                ; digits and punctuation: with SHIFT use the shifted symbol
                bcs NV_STORE
                pha
                ldy #$00
                lda (pSKCTL),y          ; A = SKSTAT
                and #$08
                tax
                pla
                dex
                inx
                bne NV_STORE
                tax
                lda SHIFT_MAP-1,x
NV_STORE:       ldy CNT1
                pha
                lda IS5200              ; on the 5200 the character is the chosen letter
                beq NV_STORE2
                pla
                lda LASTCHAR
                pha
NV_STORE2:      pla                     ; into the name on screen
                sta $095E,y
                inc CNT1
                pha                     ; cursor visible
                lda #$FF                ; CNT2 = $FF
                sta CNT2
                lda #$0A                ; PLOT_Y = $0A
                sta PLOT_Y
                pla                     ; and into the high-score line
                ldy CNT0
                sta HISCORES+2,y
                inc CNT0
NV_CLICK:       lda #$32                ; click
NV_BEEP:        ldy #$00
                sta (pAUDF2),y          ; AUDF2 = A
                lda #$05                ; COLBK_V = 5
                sta COLBK_V
                lda #$AA                ; AUDC2 = $AA
                sta (pAUDC2),y          ; AUDC2 = A
                bne NV_CURSOR
NV_DELETE:      lda #$FA                ; delete: nothing to delete? buzz
                ldx CNT1                ; if CNT1 == 0 goto NV_BEEP
                beq NV_BEEP
                lda #$00                ; remove the last character from both places
                sta $095E,x
                dec CNT1
                dec CNT0
                ldx CNT0
                lda #$00                ; HISCORES+2[X] = 0
                sta HISCORES+2,x
                beq NV_CLICK
NV_NO_REPEAT:   lda #$00                ; COLPF0_V = 0
                sta COLPF0_V
                beq NV_CURSOR
NV_SET_DONE:    stx CNT4                ; finished
NV_CURSOR:      dec PLOT_Y              ; cursor blinks every 15 frames
                bne NV_CURSOR_POS
                lda #$0F                ; PLOT_Y = $0F
                sta PLOT_Y
                lda CNT2
                eor #$FF
                sta CNT2
NV_CURSOR_POS:  lda CNT1                ; four missiles side by side under the next character
                asl a
                asl a
                asl a
                adc #$61
                and CNT2
                ldx #$06
                clc
NV_CURSOR_LOOP: sta (pHPOSM0,x)         ; X = 6,4,2,0: HPOSM3 ... HPOSM0
                adc #$02
                dex
                dex
                bpl NV_CURSOR_LOOP
                ldy #$00                ; the character at the cursor: blank, or on the 5200 the letter being chosen
                tya
                ldx IS5200              ; if IS5200 == 0 goto NV_PREVIEW
                beq NV_PREVIEW
                lda LASTCHAR
NV_PREVIEW:     ldx CNT1
                sta $095E,x
                lda PLOT_X              ; opening beep: rising sweep until it wraps to 0
                beq NV_TIMEOUT
                inc PLOT_X
                inc PLOT_X
                lda PLOT_X              ; AUDF1 = PLOT_X
                sta (pAUDF1),y          ; AUDF1 = A
                bne NV_TIMEOUT
                sta (pAUDC1),y          ; AUDC1 = A
NV_TIMEOUT:     dec COLPF2_V            ; time limit
                bne NV_EXIT
                ldx #$3C
                stx COLPF2_V
                dec BLINK_TMR           ; BLINK_TMR -= 1, until 0
                bne NV_EXIT
                stx CNT4
NV_EXIT:        lda NAME_DLY            ; if NAME_DLY == 0 goto NV_EXIT2
                beq NV_EXIT2
                dec NAME_DLY
NV_EXIT2:       jmp NMI_EXIT            ; common tail of every interrupt handler

;-----------------------------------------------------------------------------
;  BLANK_VBI - used while the credits screen (station 11) is being built: screen, players
;  and sound off, FRAMES held at 0.
;-----------------------------------------------------------------------------
BLANK_VBI:      .byte $20,$18,$92,$98,$8D,$00,$D4,$91,$4A,$91,$44,$91,$52,$85,$9D,$F0
                .byte $E6

;-----------------------------------------------------------------------------
;  DLI_NAME - the name-entry screen's background: 170 scan lines of colour bands, the
;  hue moving on every 5 lines, while the text brightness ripples line by line.
;-----------------------------------------------------------------------------
DLI_NAME:       pha
                txa
                pha
                tya
                pha
                ldy #$AA                ; 170 lines
                sty LINECNT
                ldy #$00
                ldx CNT3
                lda PLOT_COLOR          ; start colour (moves every 15 frames)
                sta (pCOLPF1),y         ; COLPF1 = A
DN_LINE:        sta WSYNC
                sta (pCOLBK),y          ; background colour for this line
                pha
                lda LINECNT             ; text brightness
                clc
                adc #$03
                and #$0F
                sta (pCOLPF1),y         ; COLPF1 = A
                pla
                dex                     ; every 5 lines the next hue (skipping grey)
                bne DN_NEXT
                ldx #$05
                adc #$10
                cmp #$0A                ; if A <> $0A goto DN_NEXT
                bne DN_NEXT
                lda #$1A
DN_NEXT:        dec LINECNT             ; LINECNT -= 1, until 0
                bne DN_LINE
DN_END:         sty WSYNC
                tya                     ; background back to black
                sta (pCOLBK),y          ; COLBK = A
                jmp NMI_EXIT            ; common tail of every interrupt handler

;-----------------------------------------------------------------------------
;  DLI_RAINBOW - the end of the credits: the only interrupt left running (there is no
;  VBI), so it also reads the keys and advances FRAMES. 180 lines of colour 1 change
;  hue every 16 lines, so the credits text is striped with a scrolling rainbow.
;-----------------------------------------------------------------------------
DLI_RAINBOW:    pha
                txa
                pha
                tya
                pha
                jsr POLL_KEYS           ; called at the start of every VBI handler
                lda PLOT_COLOR
                dec CNT3                ; every 16 frames the starting hue moves on
                bne DR_GO
                ldx #$10
                stx CNT3
                clc
                adc #$10
                cmp #$10                ; if A >= $10 goto DR_START
                bcs DR_START
                adc #$10
DR_START:       sta PLOT_COLOR
DR_GO:          ldx CNT3
                inc FRAMES              ; a frame has passed
                ldy #$B4                ; 180 lines
                sty LINECNT
                ldy #$00
DR_LINE:        sta WSYNC
                sta (pCOLPF0),y         ; COLPF0 = A
                dex                     ; loop until X = 0
                bne DR_NEXT
                ldx #$10
                clc
                adc #$10
                cmp #$10                ; if A >= $10 goto DR_NEXT
                bcs DR_NEXT
                adc #$10
DR_NEXT:        dec LINECNT             ; LINECNT -= 1, until 0
                bne DR_LINE
                beq DN_END

;-----------------------------------------------------------------------------
;  CREDITS_TEXT - (characters, x, y) for each line of the credits, drawn from TEXT_POOL
;  starting at "MINER 2049er" (the first line double height). 0 ends the list.
;-----------------------------------------------------------------------------
CREDITS_TEXT:   .byte $0C,$24,$10
                .byte $02,$48,$2D
                .byte $0A,$2C,$35
                .byte $08,$34,$55
                .byte $0C,$24,$5D
                .byte $0D,$02,$80
                .byte $07,$1A,$88
                .byte $11,$10,$9D
                .byte $11,$10,$A5
                .byte $11,$10,$AD
                .byte $0E,$10,$B5
                .byte $00

;-----------------------------------------------------------------------------
;  HIDE_PLAYERS - zero GTIA registers 0-12: positions of players and missiles, sizes.
;-----------------------------------------------------------------------------
HIDE_PLAYERS:   ldx #$18
                lda #$00
HP_LOOP:        sta (pHPOSP0,x)
                dex
                dex
                bpl HP_LOOP
                rts

;-----------------------------------------------------------------------------
;  PREPARE_SCREEN - show "MINER n / PREPARE FOR / STATION n / ZONE n" (built in RAM from
;  the text at PREP_TEXT and the display list NAME_DLIST), start its VBI and a 3-second
;  countdown, clear P/M memory and build the (still invisible) game screen.
;  The credits screen instead gets BLANK_VBI.
;-----------------------------------------------------------------------------
PREPARE_SCREEN: jsr HIDE_PLAYERS        ; zero GTIA registers 0-12
                lda STATION
                cmp #$0B                ; if A <> $0B goto PS_TEXT
                bne PS_TEXT
                ldx #$AB
                ldy #$67
                jmp PS_START
PS_TEXT:        ldy #$30                ; "MINER 1" / "Prepare for" text
PS_TEXT_LOOP:   lda PREP_TEXT-2,y       ; $0917[Y] = PREP_TEXT-2[Y]
                sta $0917,y
                dey                     ; loop until Y = 0
                bne PS_TEXT_LOOP
                ldy #$1A                ; copy the display list to $0978
PS_DL_LOOP:     lda NE_RTS,y            ; $0977[Y] = NE_RTS[Y]
                sta $0977,y
                dey                     ; loop until Y = 0
                bne PS_DL_LOOP
                ldx #$17                ; and adjust it: the station line gets fine scrolling (centring)
                stx $0988
                lda #$70                ; $097C = $70
                sta $097C
                lda PLAYER              ; player number
                clc
                adc #$11
                sta $0926
                lda STATION             ; two-digit station?
                cmp #$0A                ; if A < $0A goto PS_ONE_DIGIT
                bcc PS_ONE_DIGIT
                ldy #$2C                ; "STATION 10" layout
PS_TEXT10:      lda PREP_TEXT+48,y      ; $0947[Y] = PREP_TEXT+48[Y]
                sta $0947,y
                dey                     ; loop until Y = 0
                bne PS_TEXT10
                lda STATION             ; the units digit, in colour 2
                clc
                adc #$86
                sta $0956
                ldx #$09                ; zone digits will go at $095C
                ldy #$5C
                jmp PS_ZONE
PS_ONE_DIGIT:   stx $098B               ; one-digit station: centre that line too
                ldy #$30
PS_TEXT1:       lda PREP_TEXT+46,y      ; $0947[Y] = PREP_TEXT+46[Y]
                sta $0947,y
                dey                     ; loop until Y = 0
                bne PS_TEXT1
                lda STATION             ; the digit, in colour 2
                clc
                adc #$90
                sta $0957
                ldx #$09                ; zone digits will go at $0960
                ldy #$60
PS_ZONE:        stx PTR+1
                sty PTR
                ldx #$D0                ; zone in decimal, digits in colour 3 ($D0 = '0')
                stx BCD_100
                stx SEC_TMR
                lda ZONE
PS_HUNDREDS:    cmp #$64                ; if A < $64 goto PS_TENS
                bcc PS_TENS
                sbc #$64
                inc BCD_100             ; BCD_100 += 1, until 0
                bne PS_HUNDREDS
PS_TENS:        cmp #$0A                ; if A < $0A goto PS_UNITS
                bcc PS_UNITS
                sbc #$0A
                inc SEC_TMR             ; SEC_TMR += 1, until 0
                bne PS_TENS
PS_UNITS:       adc #$D0
                sta BONUS_TMR
                ldx #$04                ; "Zone" (4 characters)
                stx MOVE_OK
                ldx #$00
                ldy #$06                ; how many digits, and where to start (centred)
                lda ZONE
                cmp #$64                ; if A >= $64 goto PS_WRITE
                bcs PS_WRITE
                iny
                ldx #$02
                cmp #$0A                ; if A < $0A goto PS_WRITE
                bcc PS_WRITE
                iny
                dex
                lda #$17                ; $098E = $17
                sta $098E
PS_WRITE:       stx KILLED
                ldx #$00
PS_ZONE_WORD:   lda ZONE_TEXT,x         ; (PTR)[Y] = ZONE_TEXT[X]
                sta (PTR),y
                iny
                inx
                dec MOVE_OK             ; MOVE_OK -= 1, until 0
                bne PS_ZONE_WORD
                iny                     ; a space
                ldx KILLED
PS_ZONE_DIGIT:  lda BCD_100,x           ; (PTR)[Y] = BCD_100[X]
                sta (PTR),y
                inx
                iny
                cpx #$03                ; if X <> 3 goto PS_ZONE_DIGIT
                bne PS_ZONE_DIGIT
                ldx #$1E                ; countdown step: 30 frames
                stx BCD_100
                ldx #$A8                ; VBI = PREP_VBI
                ldy #$81
PS_START:       jsr SET_VBI             ; install a vertical-blank interrupt handler
                ldx #$06                ; 6 x 30 frames = 3 seconds
                stx FRAMES
                lda #$40                ; VBI only
                sta NMIEN
                jsr SILENCE             ; silence
                lda IS5200              ; 400/800: PIA port A all inputs (joysticks)
                bne PS_PM
                ldx #$38                ; PACTL bit 2 = 0: PORTA addresses the direction register
                stx PACTL
                sta PORTA               ; all inputs
                lda #$3C                ; back to the data register
                sta PACTL
PS_PM:          ldx #$03                ; PMBASE = 3; in single-line mode ANTIC ignores the low 3 bits, so P/M
                                        ;   memory
                stx PMBASE              ; starts at $0000: missiles $0300, players $0400 $0500 $0600 $0700
                stx PTR+1               ; clear $0300-$07FF
                ldx #$00
                stx PTR
                ldx #$FB
                ldy #$00
                jsr ZERO_MEM            ; zero memory from (PTR) for -(X:Y) bytes
                jmp BUILD_DLIST         ; build the game display list and clear the screen

;-----------------------------------------------------------------------------
;  DRAW_CREDITS - draw the credits text from CREDITS_TEXT in colour 1.
;-----------------------------------------------------------------------------
DRAW_CREDITS:   lda #$00                ; TXT_COLOR = 0
                sta TXT_COLOR
                ldx #$16
                stx TXT_IDX
                ldx #$02                ; the first line double height
DCR_LINE:       stx TXT_VSCALE
                tax
                lda CREDITS_TEXT,x      ; characters (0 = end)
                bne DCR_DRAW
                rts
DCR_DRAW:       sta TXT_LEN
                lda CREDITS_TEXT+1,x    ; x
                sta TXT_X
                lda CREDITS_TEXT+2,x    ; y
                tay
                txa
                clc
                adc #$03
                pha
                jsr DRAW_STRING_Y       ; draw A characters of TEXT_POOL at TXT_X, line Y
                pla
                ldx #$01                ; the rest normal height
                bne DCR_LINE

;-----------------------------------------------------------------------------
;  START_STATION - choose the station's colours, reset the per-turn variables, wait for
;  the prepare countdown, then switch on the game interrupts and let Bob go.
;
;  Colours: three random hues for pixel colours 1-3, all different, and three random
;  brightnesses from {4, 6, 8}, also all different. Different brightness keeps items,
;  ladders and girders distinguishable on a black-and-white TV.
;-----------------------------------------------------------------------------
START_STATION:  ldx #$03
                stx CNT7
SS_CLEAR:       lda COLBK_V,x           ; keep only the hues of the old colours (so they can be compared)
                and #$F0
                sta COLBK_V,x
                dex                     ; loop until X = 0
                bne SS_CLEAR
SS_HUE:         ldy #$00                ; random hue ...
                lda (pSKRES),y          ; A = RANDOM
                and #$F0
                sta MOVE_A
                ldx #$03
SS_HUE_CHK:     lda COLBK_V,x           ; ... not used by another colour
                and #$F0
                cmp MOVE_A              ; if A == MOVE_A goto SS_HUE
                beq SS_HUE
                dex                     ; loop until X = 0
                bne SS_HUE_CHK
SS_LUM:         lda (pSKRES),y          ; random brightness 4, 6 or 8 ...
                and #$06                ; test bits $06
                beq SS_LUM
                clc
                adc #$02
                sta MOVE_B
                ldx #$03
SS_LUM_CHK:     lda COLBK_V,x           ; ... not used by another colour
                and #$0F
                cmp MOVE_B              ; if A == MOVE_B goto SS_LUM
                beq SS_LUM
                dex                     ; loop until X = 0
                bne SS_LUM_CHK
                lda MOVE_A
                ora MOVE_B
                ldy CNT7
                sta a:$008A,y
                dec CNT7                ; CNT7 -= 1, until 0
                bne SS_HUE
                lda STATION             ; credits: colour 1 black (the text starts hidden) and draw the text
                cmp #$0B                ; if A <> $0B goto SS_PRIOR
                bne SS_PRIOR
                ldx #$00
                stx COLPF0_V
                jsr DRAW_CREDITS        ; draw the credits text from CREDITS_TEXT in colour 1
SS_PRIOR:       lda #$31                ; X = 8: (pCOLPF1,x) = (pPRIOR): PRIOR = $31 = players in front, fifth
                                        ;   player
                ldx #$08                ; (missiles take COLPF3), multicolour players
                sta (pCOLPF1,x)
                lda STATION
                cmp #$0B                ; if A == $0B goto SS_VARS
                beq SS_VARS
                lda #$FF                ; missile rows $20-$27: the box behind the bonus on the status line
SS_BOX:         sta PM_MISSILES+31,x
                dex                     ; loop until X = 0
                bne SS_BOX
SS_VARS:        lda #$1E                ; status line steady for 30 frames
                sta BLINK_TMR
                lda #$00                ; clear START_DLY .. HIT_P3
                ldx #$0A
SS_CLR:         sta START_DLY,x
                dex                     ; loop until X = 0
                bne SS_CLR
                tax                     ; per-turn state = 0
                stx ITEM_GOT
                stx CANNON_DONE
                stx CANNON_ST
                stx TNT
                stx LIFT_DLY
                stx LIFT_ON
                stx KILLED
                stx BLINK_ON
                stx CHACTL
                stx SND3_VOL
                stx FALL_LEN
                stx SPECIAL
                stx BOB_FALL
                stx SLIDE_LEN
                stx DYING
                stx COLBK_V
                inx                     ; = 1
                stx ON_LIFT
                stx TICK_SND
                stx BOB_FRAME
                stx WALK_STEP
                inx                     ; = 2
                stx ALIVE
                stx PAUSE_DLY
                ldx #$0A
                stx JUMP_LOCK
                ldx #$3C
                stx SEC_TMR
                ldx #$B8                ; the end-of-station wipe starts at display-list line 184
                stx WIPE_LINE
                ldy #$01                ; first demo input lasts this long
                lda (DEMO_PTR),y        ; DEMO_CNT = (DEMO_PTR)[Y]
                sta DEMO_CNT
                jsr BOB_COLOURS         ; Bob's colours
                jsr DRAW_STATUS         ; status line
SS_WAIT:        lda FRAMES              ; wait for the prepare countdown
                bne SS_WAIT
                sta MOVE_OK             ; Bob may not move yet
                sta NMIEN               ; NMIs off while the vectors change
                ldx #$B7                ; DLI = DLI_MUTANTS
                ldy #$0E
                jsr SET_DLI             ; install a display-list-interrupt handler
                ldy #$B0                ; VBI = GAME_VBI
                ldx #$BB
                jsr SET_VBI             ; install a vertical-blank interrupt handler
                ldy #$00                ; clear collisions
                sta (pHITCLR),y         ; HITCLR = A
                ldx #$C0                ; DLI + VBI on
                stx NMIEN
                ldx #$3C                ; one second of quiet (GAME_VBI counts FRAMES up)
SS_PAUSE:       jsr SILENCE             ; all four voices off (SILENCE_234 leaves voice 1 alone; A must be 0)
                cpx FRAMES              ; if X <> FRAMES goto SS_PAUSE
                bne SS_PAUSE
                lda #$07                ; go!
                sta MOVE_OK
                ldx LIFE_USED           ; take a life at the start of the turn (once)
                bne SS_RTS
                inc LIFE_USED
                dec LIVES
SS_RTS:         rts

;-----------------------------------------------------------------------------
;  DRAW_STATUS - the status line: player 1's score and lives at the left; in a two-player
;  game player 2's score and lives at the right. The current player's score is written with bit 7 set,
;  so that CHACTL bit 0 (blank such characters) makes it blink.
;  Lives are shown as balls (internal code $54, ATASCII ball).
;-----------------------------------------------------------------------------
DRAW_STATUS:    lda STATION             ; nothing on the credits screen
                cmp #$0B                ; if A == $0B goto DS_RTS
                beq DS_RTS
                lda #$00                ; player 1's score at column 1
                ldy #$01
                jsr DRAW_SCORE          ; player A's score on the status line from column Y
                lda #$00                ; his lives after it, left to right
                ldx #$01
                jsr DRAW_LIVES          ; lives of player A as balls, from column Y, step X
                lda TWO_PLAYER          ; if TWO_PLAYER == 0 goto DS_RTS
                beq DS_RTS
                lda #$01                ; player 2's score from column 32, right-aligned
                ldy #$20
                jsr DRAW_SCORE          ; player A's score on the status line from column Y
                ldy PLOT_X              ; his lives to the left of it, right to left
                dey
                lda #$01
                ldx #$FF
DRAW_LIVES:     stx PLOT_X
                cmp PLAYER              ; lives of this player
                beq DLV_CURRENT
                ldx P2_LIVES
                jmp DLV_START
DLV_CURRENT:    ldx LIVES
DLV_START:      inx                     ; a blank, then one ball per life, then a blank
                lda #$00
                beq DLV_PUT
DLV_BALL:       lda #$44
                clc
                adc CNT1
DLV_PUT:        sta STATUS,y
                tya
                clc
                adc PLOT_X
                tay
                dex                     ; loop until X = 0
                bne DLV_BALL
                txa
                sta STATUS,y
DS_RTS:         rts

;-----------------------------------------------------------------------------
;  DRAW_SCORE - player A's score on the status line from column Y: six digits, leading
;  zeros blank (player 1 left-justified, player 2 right-justified), a comma after the
;  thousands, "0" for no score. Leaves PLOT_X = column of the first character printed.
;-----------------------------------------------------------------------------
DRAW_SCORE:     sta PLOT_Y
                cmp PLAYER              ; current player: bit 7 set ($90), blinked off by CHACTL bit 0 ...
                beq DSC_CURRENT
                ldx #$C5                ; ... the other: normal ($10)
                lda #$10
                bne DSC_GO
DSC_CURRENT:    lda #$90
                ldx #$BB
DSC_GO:         sta CNT1
                lda #$06                ; CNT3 = 6
                sta CNT3
                lda #$00                ; no digit printed yet
                sta CNT2
DSC_DIGIT:      lda 0,x                 ; digit X of zero page (X = SCORE or P2_DATA+4)
                bne DSC_OUT
                bit CNT2
                bmi DSC_OUT
                lda CNT3                ; always print the last digit
                cmp #$01                ; if A == 1 goto DSC_ZERO
                beq DSC_ZERO
                tya                     ; leading zero: player 2 still moves along
                clc
                adc PLOT_Y
                tay
                bne DSC_NEXT
DSC_ZERO:       lda #$00
DSC_OUT:        clc
                adc CNT1
                sta STATUS,y
                lda CNT2                ; first digit printed?
                bne DSC_ADV
                sty PLOT_X
                lda #$FF                ; CNT2 = $FF
                sta CNT2
DSC_ADV:        iny
DSC_NEXT:       inx
                dec CNT3                ; CNT3 -= 1, goto DS_RTS if 0
                beq DS_RTS
                lda CNT3                ; after the thousands ...
                cmp #$03                ; if A <> 3 goto DSC_DIGIT
                bne DSC_DIGIT
                lda CNT2                ; ... a comma, if any digit has been printed
                beq DSC_NO_COMMA
                lda #$FC                ; STATUS[Y] = $FC + CNT1
                clc
                adc CNT1
                sta STATUS,y
                iny
                bne DSC_DIGIT
DSC_NO_COMMA:   tya
                clc
                adc PLOT_Y
                tay
                bne DSC_DIGIT
AS_CARRY:       dex                     ; carry into the next digit up (lost beyond the 100,000s)
                beq AS_STEADY

;-----------------------------------------------------------------------------
;  ADD_SCORE - add A to score digit X (1 = 100,000s ... 4 = hundreds, 5 = tens,
;  6 = units), carrying upwards. Awards the one extra life when the score first reaches
;  10,000, and makes the status line hold still for two seconds.
;-----------------------------------------------------------------------------
ADD_SCORE:      ldy #$00
                clc
                adc SCORE-1,x
AS_DIV:         cmp #$0A                ; if A < $0A goto AS_STORE
                bcc AS_STORE
                sbc #$0A
                iny
                jmp AS_DIV
AS_STORE:       sta SCORE-1,x
                tya
                bne AS_CARRY
                ldx XLIFE               ; extra life still to come, and 10,000 reached?
                cpx #$0A                ; if X <> $0A goto AS_STEADY
                bne AS_STEADY
                lda SCORE+1             ; if SCORE+1 == 0 goto AS_STEADY
                beq AS_STEADY
                dex                     ; yes: start the jingle (XLIFE = 9) and add a life
                stx XLIFE
                inc LIVES
AS_STEADY:      lda #$78                ; BLINK_TMR = $78
                sta BLINK_TMR
                lda #$00                ; BLINK_ON = 0
                sta BLINK_ON
                sta CHACTL
                rts

;-----------------------------------------------------------------------------
;  TRY_CLIMB_UP - stick pushed up: is Bob standing at the foot of a ladder?
;  A ladder entry is (height, x, y, style). Bob qualifies if his feet (BOB_Y + $15) are
;  level with the ladder's bottom (y + height) or one line above it, and his x within 2 of the ladder's.
;  He is then lined up with the ladder and starts climbing: frame 7, MOVE_A = lines to
;  the top, MOVE_B = lines above the bottom.
;-----------------------------------------------------------------------------
TRY_CLIMB_UP:   ldy #$00
TCU_LOOP:       lda (LADDERS),y         ; end of the ladder list: no ladder, treat as a plain stick movement
                bne TCU_ENTRY
                jmp NO_LADDER
TCU_ENTRY:      iny                     ; bottom of the ladder = y + height
                iny
                clc
                adc (LADDERS),y
                sec                     ; - feet line
                sbc BOB_Y
                sec
                sbc #$15
                cmp #$02                ; within 0-1 lines?
                bcs TCU_NEXT
                sta TMP9B
                dey                     ; x within -2..+2?
                lda (LADDERS),y
                sec
                sbc BOB_X
                clc
                adc #$02
                cmp #$05                ; if A >= 5 goto TCU_NEXT_X
                bcs TCU_NEXT_X
                lda (LADDERS),y         ; line up with the ladder and step on
                sta BOB_X
                dec BOB_Y
                lda #$07                ; climbing frame
                sta BOB_FRAME
                dey                     ; MOVE_A = height + 4 - offset = lines to the top
                lda (LADDERS),y
                adc #$04
                sec
                sbc TMP9B
                sta MOVE_A
                ldy #$01                ; MOVE_B = 1
                sty MOVE_B
                dey
LADDER_ON:      tya                     ; footsteps off
                sta (pAUDC3),y          ; AUDC3 = A
                jmp SHOW_BOB            ; draw Bob (upside down once he has been fired from the cannon), and on
TCU_NEXT_X:     iny
TCU_NEXT:       iny
                iny
                jmp TCU_LOOP

;-----------------------------------------------------------------------------
;  TRY_CLIMB_DOWN - stick pulled down: is Bob standing at the top of a ladder?
;  (feet within 2 lines of y + 4, x within 2). Then frame 10, MOVE_A = 1,
;  MOVE_B = lines to the bottom.
;-----------------------------------------------------------------------------
TRY_CLIMB_DOWN: ldy #$00
TCD_LOOP:       lda (LADDERS),y         ; if (LADDERS)[Y] == 0 goto NO_LADDER
                beq NO_LADDER
                iny
                iny
                lda (LADDERS),y         ; top of the ladder - Bob's feet - 4
                sec
                sbc BOB_Y
                sec
                sbc #$19
                cmp #$02                ; if A >= 2 goto TCD_NEXT
                bcs TCD_NEXT
                sta TMP9B
                dey
                lda (LADDERS),y
                sec
                sbc BOB_X
                clc
                adc #$02
                cmp #$05                ; if A >= 5 goto TCD_NEXT_X
                bcs TCD_NEXT_X
                lda (LADDERS),y         ; line up and step down
                sta BOB_X
                inc BOB_Y
                lda #$0A                ; frame 10 (stepping onto the ladder)
                sta BOB_FRAME
                lda #$01                ; MOVE_A = 1
                sta MOVE_A
                dey                     ; MOVE_B = height + 3 + offset = lines to the bottom
                lda (LADDERS),y
                adc #$03
                adc TMP9B
                sta MOVE_B
                ldy #$00
                jmp LADDER_ON
TCD_NEXT_X:     iny
TCD_NEXT:       iny
                iny
                jmp TCD_LOOP
NO_LADDER:      jsr READ_STICK          ; no ladder here: continue with left/right
                lsr a
                lsr a
                jmp MB_STICK_LR

;-----------------------------------------------------------------------------
;  MOVE_BOB - Bob's state machine, run every frame by GAME_VBI.
;
;    SPECIAL = 1 ........ dying: MELT_BOB
;    SPECIAL = 2 ........ dead: nothing (GAME_VBI ends the turn)
;    SPECIAL = 3-7 ...... in the transporter: TRANSPORT
;    BOB_FALL ........... falling: FALLING
;    SLIDE_LEN .......... sliding down a chute: SLIDING
;    on a slide start ... begin a slide
;    BOB_FRAME 11-12 .... jumping: JUMPING
;    BOB_FRAME 7-10 ..... on a ladder: ON_LADDER
;    otherwise .......... on a girder: button = jump, up/down = ladders,
;                         left/right = walk, still in a transporter booth + digit = go
;-----------------------------------------------------------------------------
MOVE_BOB:       lda SPECIAL             ; if SPECIAL == 0 goto MB_NORMAL
                beq MB_NORMAL
                cmp #$01                ; if A <> 1 goto MB_SPECIAL
                bne MB_SPECIAL
                jmp MELT_BOB            ; SPECIAL = 1
MB_SPECIAL:     cmp #$03                ; if A < 3 goto MB_DEAD
                bcc MB_DEAD
                jmp TRANSPORT           ; the transporter, SPECIAL = 3..7, with a random buzz on voice 3:
MB_DEAD:        rts
MB_NORMAL:      lda BOB_FALL            ; if BOB_FALL == 0 goto MB_SLIDING
                beq MB_SLIDING
                jmp FALLING             ; one line down per frame with a falling whistle; then the landing test
MB_SLIDING:     lda SLIDE_LEN           ; if SLIDE_LEN == 0 goto MB_SLIDE_CHECK
                beq MB_SLIDE_CHECK
                jmp SLIDING             ; one line down and MOVE_A pixels sideways per frame, with a falling whi
MB_SLIDE_CHECK: ldy #$00                ; is Bob exactly at the top of a slide?
MBS_LOOP:       lda (SLIDES),y          ; rows (0 = end of list)
                beq MB_FRAME
                tax
                iny
                lda (SLIDES),y
                iny
                cmp BOB_X               ; if A <> BOB_X goto MBS_NEXT
                bne MBS_NEXT
                lda (SLIDES),y
                cmp BOB_Y               ; if A <> BOB_Y goto MBS_NEXT
                bne MBS_NEXT
                stx SLIDE_LEN           ; yes: slide for that many frames
                iny
                ldx #$0B                ; frame 11 (sliding right) or 12 (left)
                lda (SLIDES),y          ; MOVE_A = (SLIDES)[Y]
                sta MOVE_A              ; MOVE_A = x step per frame
                bpl MBS_FRAME
                inx
MBS_FRAME:      stx BOB_FRAME
                lda #$00                ; start 2 * step further back
                sec
                sbc (SLIDES),y
                asl a
                clc
                adc BOB_X
                sta BOB_X
                jmp FALL_SOUND          ; slide noise
MBS_NEXT:       iny
                iny
                bne MBS_LOOP
MB_FRAME:       lda BOB_FRAME           ; jumping?
                cmp #$0B                ; if A < $0B goto MB_LADDER_Q
                bcc MB_LADDER_Q
                jmp JUMPING             ; every other frame move MOVE_B sideways (unless blocked); every frame m
MB_LADDER_Q:    cmp #$07                ; on a ladder?
                bcc MB_GROUND
                jmp ON_LADDER           ; climbing, one line every other frame
MB_GROUND:      jsr READ_BUTTON         ; button: carry clear = pressed
                lsr a
                bcc MB_BUTTON
                ldx JUMP_LOCK           ; not pressed: run the lock-out down
                beq MB_STICK
                dec JUMP_LOCK
                bcs MB_STICK
MB_BUTTON:      ldy #$06                ; pressed: jump only on a fresh press (lock-out was 0)
                ldx JUMP_LOCK
                sty JUMP_LOCK
                bne MB_STICK
                lda CANNON_ST           ; and not while inside the cannon
                bne MB_STICK
                jmp START_JUMP          ; button pressed
MB_STICK:       jsr READ_STICK          ; stick bit 0 = up
                lsr a
                bcs MB_STICK_DOWN
                jmp TRY_CLIMB_UP        ; stick pushed up
MB_STICK_DOWN:  lsr a                   ; bit 1 = down
                bcs MB_STICK_LR
                jmp TRY_CLIMB_DOWN      ; stick pulled down
MB_STICK_LR:    ldy WALK_STEP           ; bit 2 = left
                ldx BOB_X
                lsr a
                bcs MB_STICK_RIGHT
                jmp WALK_LEFT           ; as WALK_RIGHT, frames 4-6, feet tested at x+2..x+4
MB_STICK_RIGHT: lsr a                   ; bit 3 = right
                bcc WALK_RIGHT
                lda SPECIAL_X           ; standing still: inside a transporter booth?
                clc
                sbc BOB_X
                cmp #$05                ; if A >= 5 goto MB_STILL
                bcs MB_STILL
                lda #$1D                ; on one of the four floors ($1D + 47 n)?
                ldx #$04
MB_BOOTH:       cmp BOB_Y               ; if A <> BOB_Y goto MB_BOOTH_NEXT
                bne MB_BOOTH_NEXT
                jsr READ_DIGIT          ; a digit key 1-4 ...
                beq MB_STILL
                cpy #$05                ; if Y >= 5 goto MB_STILL
                bcs MB_STILL
                sty TRANS_DEST          ; ... that is not this floor ...
                cpx TRANS_DEST          ; if X == TRANS_DEST goto MB_STILL
                beq MB_STILL
                lda TRANS_LOCK          ; ... and the transporter is not cooling down
                bne MB_STILL
                stx TRANS_SRC           ; go: start the transporter sequence
                ldy #$03
                sty SPECIAL
                ldy #$08
                sty MOVE_A
                sty MOVE_B
                jmp SPARKLE_BOB         ; draw Bob, then AND every line of his three players with a random numbe
MB_BOOTH_NEXT:  clc                     ; next floor up
                adc #$2F
                dex                     ; loop until X = 0
                bne MB_BOOTH
MB_STILL:       jmp FS_QUIET

;-----------------------------------------------------------------------------
;  WALK_RIGHT - walk animation frames 1-3, one pixel every other frame.
;  After moving, look at Bob's feet:
;    girder 1 line above the feet  -> the girder rises: step up one line
;    girder under the feet          -> fine
;    girder 1 line below            -> the girder falls: step down
;    nothing                         -> walk off the edge and start falling
;-----------------------------------------------------------------------------
WALK_RIGHT:     iny                     ; next walk frame (1-3)
                cpy #$04                ; if Y < 4 goto WR_FRAME
                bcc WR_FRAME
                ldy #$01
WR_FRAME:       sty WALK_STEP
                sty BOB_FRAME
                lda FRAMES              ; move on even frames only
                and #$01                ; test bits $01
                bne FOOTSTEPS
                inx
                jsr CHECK_RIGHT         ; wall or screen edge?
                beq FOOTSTEPS
                stx BOB_X
                lda CANNON_ST           ; inside the cannon: no ground check
                bne FOOTSTEPS
                txa                     ; girder one line above the feet, at x + 5?
                clc
                adc #$05
                tay
                lda #$14
                jsr PROBE_LINE          ; girder at x = Y, line BOB_Y + A?
                bne WR_FEET
                dec BOB_Y               ; yes: step up
                jmp FOOTSTEPS
WR_FEET:        lda #$03                ; girder under the feet at x+3, x+4 or x+5?
                sta TMP9B
                jsr PROBE_FEET3         ; is there girder under Bob's feet at x = BOB_X + 3?
WR_FEET_LOOP:   beq FOOTSTEPS
                dec TMP9B               ; TMP9B -= 1, goto WR_DOWN if 0
                beq WR_DOWN
                ldx PROBE_Y
                ldy PROBE_X
                iny
                jsr PROBE_AT_Y          ; girder at x = Y, line PROBE_Y?
                jmp WR_FEET_LOOP
WR_DOWN:        inc BOB_Y               ; none: try one line lower
                jsr PROBE_FEET3         ; is there girder under Bob's feet at x = BOB_X + 3?
                beq FOOTSTEPS           ; found: step down
                ldx #$01                ; nothing: walked off, start to fall (frame 1)
START_FALL:     stx BOB_FRAME
                ldx #$00
                stx FALL_LEN
                inx
                stx BOB_FALL
FALL_SOUND:     lda #$1E                ; X = $1E: (pCOLPM3,x) = (pAUDF3), (pCOLPF0,x) = (pAUDC3)
                tax
                sta SND3_F
                sta (pCOLPM3,x)
                lda #$AA
                sta (pCOLPF0,x)
                bne FS_DONE
FOOTSTEPS:      ldy CANNON_ST           ; inside the cannon: a low rumble
                beq FS_STEP
                ldy #$4F
                ldx #$1A
                bne FS_SET
FS_STEP:        ldy SND3_F              ; 14-frame cycle: thud (0-2), silence, click (7-9), silence
                iny
                cpy #$0E                ; if Y < $0E goto FS_PHASE
                bcc FS_PHASE
                ldy #$00
FS_PHASE:       sty SND3_F
                cpy #$03                ; if Y < 3 goto FS_THUD
                bcc FS_THUD
                cpy #$07                ; if Y < 7 goto FS_QUIET
                bcc FS_QUIET
                cpy #$0A                ; if Y < $0A goto FS_CLICK
                bcc FS_CLICK
FS_QUIET:       ldy #$00
                beq FS_VOL
FS_THUD:        ldx #$FA
                ldy #$CA
                bne FS_SET
FS_CLICK:       ldx #$00
                ldy #$8A
FS_SET:         txa
                ldx #$00
                sta (pAUDF3,x)
FS_VOL:         tya
                ldy #$00
                sta (pAUDC3),y          ; AUDC3 = A
FS_DONE:        jmp SHOW_BOB            ; draw Bob (upside down once he has been fired from the cannon), and on

;-----------------------------------------------------------------------------
;  WALK_LEFT - as WALK_RIGHT, frames 4-6, feet tested at x+2..x+4.
;-----------------------------------------------------------------------------
WALK_LEFT:      iny
                cpy #$04                ; if Y < 4 goto WL_FRAME
                bcc WL_FRAME
                ldy #$01
WL_FRAME:       sty WALK_STEP
                tya
                clc
                adc #$03
                sta BOB_FRAME
                lda FRAMES
                and #$01                ; test bits $01
                bne FOOTSTEPS
                dex
                jsr CHECK_LEFT          ; wall or screen edge?
                beq FOOTSTEPS
                stx BOB_X
                lda CANNON_ST           ; if CANNON_ST <> 0 goto FOOTSTEPS
                bne FOOTSTEPS
                txa                     ; girder one line above the feet, at x + 2?
                tay
                iny
                iny
                lda #$14
                jsr PROBE_LINE          ; girder at x = Y, line BOB_Y + A?
                bne WL_FEET
                dec BOB_Y               ; step up
                jmp FOOTSTEPS
WL_FEET:        lda #$03                ; TMP9B = 3
                sta TMP9B
                ldy BOB_X
                iny
                iny
                jsr PROBE_FEET          ; girder at x = Y, line BOB_Y + $15 (the feet)?
WL_FEET_LOOP:   beq FOOTSTEPS
                dec TMP9B               ; TMP9B -= 1, goto WL_DOWN if 0
                beq WL_DOWN
                ldx PROBE_Y
                ldy PROBE_X
                iny
                jsr PROBE_AT_Y          ; girder at x = Y, line PROBE_Y?
                jmp WL_FEET_LOOP
WL_DOWN:        inc BOB_Y
                ldy BOB_X
                iny
                iny
                jsr PROBE_FEET          ; girder at x = Y, line BOB_Y + $15 (the feet)?
                bne WL_FALL
                jmp FOOTSTEPS
WL_FALL:        ldx #$04                ; walked off: fall, facing left (frame 4)
                jmp START_FALL

;-----------------------------------------------------------------------------
;  PROBE_FEET - is there girder (colour 3) at x = Y, line = BOB_Y + A?
;  PROBE_FEET3: x = BOB_X + 3, line = feet. PROBE_FEET: x in Y, line = BOB_Y + $15.
;  PROBE_AT: line in X. PROBE_AT_Y: x in Y, line already in PROBE_Y.
;  Out: Z set = solid. Station 8's lift counts as solid where Bob's feet meet its
;  platform; ON_LIFT is set to 0 there.
;-----------------------------------------------------------------------------
PROBE_FEET3:    ldy BOB_X
                iny
                iny
                iny
PROBE_FEET:     lda #$15
PROBE_LINE:     clc
                adc BOB_Y
                tax
PROBE_AT:       stx PROBE_Y
PROBE_AT_Y:     sty PROBE_X
                jsr READ_PIXEL_XY       ; girder?
                beq PR_SET
                lda BOB_Y               ; no: the lift's platform? (only at the feet line)
                clc
                adc #$15
                cmp PROBE_Y             ; if A <> PROBE_Y goto PR_RTS
                bne PR_RTS
                cmp LIFT_Y              ; if A <> LIFT_Y goto PR_NONE
                bne PR_NONE
                lda PROBE_X
                cmp LIFT_X              ; if A < LIFT_X goto PR_NONE
                bcc PR_NONE
                lda LIFT_X
                adc #$0E
                cmp PROBE_X             ; if A >= PROBE_X goto PR_LIFT
                bcs PR_LIFT
PR_NONE:        lda #$02
                bne PR_SET
PR_LIFT:        lda #$00                ; on the lift
                sta ON_LIFT
                lda #$03                ; Z set
                cmp #$03
PR_RTS:         rts
PR_SET:         sta ON_LIFT
                rts

;-----------------------------------------------------------------------------
;  TRANSPORT - the transporter, SPECIAL = 3..7, with a random buzz on voice 3:
;    3  Bob fades into sparkles while the buzz gets louder
;    4  a short pause
;    5  Bob appears at the chosen floor; the sparkles at the old booth die away
;    6  sparkle for a moment at the new booth
;    7  Bob forms again while the buzz fades; the transporter is then locked for a while
;-----------------------------------------------------------------------------
TRANSPORT:      ldy #$00                ; random buzz
                lda (pSKRES),y          ; A = RANDOM
                and #$1E
                sta (pAUDF3),y          ; AUDF3 = A
                ldx SPECIAL
                dex
                dex
                dex
                beq TR_FADE
                dex
                beq TR_PAUSE
                dex                     ; loop until X = 0
                bne TR_7Q
                jmp TR_OLD_BOOTH
TR_7Q:          dex                     ; loop until X = 0
                bne TR_ARRIVE
                jmp TR_NEW_BOOTH
TR_ARRIVE:      dec MOVE_A              ; state 7: slow down the sparkle, quieter each step
                bne TR_SHOW
                inc MOVE_B
                lda MOVE_B              ; MOVE_A = MOVE_B
                sta MOVE_A
                lda #$08
                sec
                sbc MOVE_B
                asl a
                ora #$A0
                ldx #$05                ; X = 5: (pAUDF2+1,x) = (pAUDC3)
                sta (pAUDF2+1,x)
                cmp #$A0                ; fully formed?
                bne TR_SPARKLE
                stx TRANS_LOCK          ; lock the transporter (TRANS_LOCK = 5) and return to normal
                ldx #$00
                stx SPECIAL
TR_SHOW:        jmp SHOW_BOB            ; draw Bob (upside down once he has been fired from the cannon), and on
TR_SPARKLE:     jmp SPARKLE_BOB         ; draw Bob, then AND every line of his three players with a random numbe
TR_FADE:        dec MOVE_A              ; state 3: fade out, louder each step
                bne TR_SHOW
                dec MOVE_B              ; MOVE_B -= 1, goto TR_GONE if 0
                beq TR_GONE
                lda MOVE_B              ; MOVE_A = MOVE_B
                sta MOVE_A
                lda #$08
                sec
                sbc MOVE_B
                asl a
                ldy #$00
                ora #$A0
                sta (pAUDC3),y          ; AUDC3 = A
                bne TR_SPARKLE
TR_GONE:        ldx #$04                ; gone: state 4 for 8 frames
                stx SPECIAL
                ldx #$08
                stx MOVE_A
                bne TR_SPARKLE
TR_PAUSE:       dec MOVE_A              ; state 4
                bne TR_SPARKLE
                ldx BOB_Y               ; remember the old height
                stx TRANS_Y
                ldx #$05                ; state 5
                stx SPECIAL
                ldx #$0E
                stx MOVE_A
                ldy TRANS_DEST          ; new height = $D9 - 47 * floor
                lda #$D9
TR_FLOOR:       sec
                sbc #$2F
                dey                     ; loop until Y = 0
                bne TR_FLOOR
                sta BOB_Y
                bne TR_SHOW
TR_OLD_BOOTH:   lda BOB_Y               ; state 5: sparkle at the old booth (BOB_Y briefly set back)
                pha
                lda TRANS_Y             ; BOB_Y = TRANS_Y
                sta BOB_Y
                jsr SPARKLE_BOB         ; draw Bob, then AND every line of his three players with a random numbe
                pla
                sta BOB_Y
                lda FRAMES
                and #$01                ; test bits $01
                bne TR_SPARKLE
                dec MOVE_A
                bpl TR_SPARKLE
                lda TRANS_Y             ; done: wipe the old image from players 0-2
                clc
                adc #$3C
                tax
                ldy #$14
                lda #$00
TR_WIPE0:       sta $03F6,x
                dex
                dey                     ; loop until Y = 0
                bne TR_WIPE0
                ldy #$11
TR_WIPE1:       sta PM_P1+7,x
                dex
                dey                     ; loop until Y = 0
                bne TR_WIPE1
                ldy #$11
TR_WIPE2:       sta PM_P2+30,x
                dex
                dey                     ; loop until Y = 0
                bne TR_WIPE2
                ldx #$08                ; state 6 for 8 frames
                stx MOVE_A
                ldx #$06
                stx SPECIAL
                jsr TR_SPARKLE          ; draw Bob as sparkles

;-----------------------------------------------------------------------------
;  BOB_COLOURS - Bob's three colours: player 0 blue ($8A), player 1 orange ($3A),
;  player 2 white ($0F).
;-----------------------------------------------------------------------------
BOB_COLOURS:    lda #$8A
                ldy #$00
                sta (pCOLPM0),y         ; COLPM0 = A
                lda #$3A                ; COLPM1 = $3A
                sta (pCOLPM1),y         ; COLPM1 = A
                lda #$0F                ; COLPM2 = $0F
                sta (pCOLPM2),y         ; COLPM2 = A
                rts
TR_NEW_BOOTH:   dec MOVE_A              ; state 6
                beq TR_TO_7
                jmp SPARKLE_BOB         ; draw Bob, then AND every line of his three players with a random numbe
TR_TO_7:        ldx #$07                ; state 7
                stx SPECIAL
                ldx #$01
                stx MOVE_A
                dex
                stx MOVE_B
                jmp TR_SPARKLE          ; draw Bob as sparkles

;-----------------------------------------------------------------------------
;  SLIDING - one line down and MOVE_A pixels sideways per frame, with a falling whistle (AUDF3 rises),
;  until SLIDE_LEN runs out.
;-----------------------------------------------------------------------------
SLIDING:        ldy #$00
                inc BOB_Y
                lda MOVE_A              ; BOB_X = MOVE_A + BOB_X
                clc
                adc BOB_X
                sta BOB_X
                lda FRAMES
                and #$01                ; test bits $01
                bne SL_COUNT
                inc SND3_F              ; every second frame the whistle drops a step
                lda SND3_F              ; AUDF3 = SND3_F
                sta (pAUDF3),y          ; AUDF3 = A
SL_COUNT:       dec SLIDE_LEN           ; SLIDE_LEN -= 1, until 0
                bne SL_SHOW
                lda #$FF                ; end of the slide: sound to a low hiss
                sta (pAUDF3),y          ; AUDF3 = A
                lda #$8F                ; AUDC3 = $8F
                sta (pAUDC3),y          ; AUDC3 = A
                lda BOB_FRAME           ; standing frame facing the same way (1 or 4)
                ldx #$01
                cmp #$0B                ; if A == $0B goto SL_FRAME
                beq SL_FRAME
                ldx #$04
SL_FRAME:       stx BOB_FRAME
SL_SHOW:        jmp SHOW_BOB            ; draw Bob (upside down once he has been fired from the cannon), and on

;-----------------------------------------------------------------------------
;  MELT_BOB - SPECIAL = 1: Bob melts. Each frame a random byte is fed in at his feet in
;  each of his three players and the column above is shifted down a line, from the feet
;  up to MOVE_B; MOVE_B moves down one line per frame. When it reaches BOB_Y + $11 (his shins) he is a
;  puddle of noise and SPECIAL becomes 2 (dead).
;-----------------------------------------------------------------------------
MELT_BOB:       lda BOB_Y               ; feet line
                clc
                adc #$15
                sta TMP9B
                ldy #$04                ; player 0 ($041F + row)
                ldx #$1F
                jsr MELT_COLUMN         ; melt one of Bob's players (page Y)
                ldy #$05                ; player 1
                ldx #$1F
                jsr MELT_COLUMN         ; melt one of Bob's players (page Y)
                ldy #$06                ; player 2
                ldx #$1F
                jsr MELT_COLUMN         ; melt one of Bob's players (page Y)
                inc MOVE_B
                lda BOB_Y
                clc
                adc #$11
                cmp MOVE_B              ; if A <> MOVE_B goto MELT_SHOW
                bne MELT_SHOW
                lda #$02                ; melted: dead
                sta SPECIAL
MELT_SHOW:      jmp HIDE_IN_CANNON      ; station 10: hide Bob's legs inside the loaded cannon
MELT_COLUMN:    stx SPR_PTR
                ldx #$00
                sty SPR_PTR+1
                ldy TMP9B
                lda (pSKRES,x)          ; X = 0: (pSKRES,x) = RANDOM
                sta (SPR_PTR),y
MELT_SHIFT:     dey
                dey
                lda (SPR_PTR),y
                iny
                sta (SPR_PTR),y
                cpy MOVE_B              ; if Y <> MOVE_B goto MELT_SHIFT
                bne MELT_SHIFT
                rts

;-----------------------------------------------------------------------------
;  ON_LADDER - climbing, one line every other frame. MOVE_A = lines to the top,
;  MOVE_B = lines to the bottom; reaching either end puts Bob back on his feet (frame 0).
;  Frames: 7/8 alternate while climbing, 9 and 10 near the top as he steps on and off.
;-----------------------------------------------------------------------------
ON_LADDER:      lda FRAMES
                and #$01                ; test bits $01
                beq OL_MOVE
OL_RTS:         rts
OL_MOVE:        jsr READ_STICK          ; joystick in the PORTA format (bit 0 up, 1 down, 2 left, 3 right; 0 mea
                lsr a                   ; up?
                bcc OL_UP
                lsr a                   ; down?
                bcs OL_RTS
                inc BOB_Y               ; down a line
                inc MOVE_A
                dec MOVE_B              ; MOVE_B -= 1, goto OL_OFF if 0
                beq OL_OFF
OL_FRAME:       lda MOVE_A              ; near the top?
                cmp #$05                ; if A >= 5 goto OL_CLIMB
                bcs OL_CLIMB
                ldx #$09                ; 3-4 lines from the top: frame 9; 1-2: frame 10
                cmp #$03                ; if A >= 3 goto OL_SET
                bcs OL_SET
                inx
                bne OL_SET
OL_CLIMB:       lda FRAMES              ; alternate frames 7 and 8 every 2 frames
                and #$02                ; test bits $02
                bne OL_SHOW
                lda BOB_FRAME
                ldx #$07
                cmp #$08                ; if A == 8 goto OL_SET
                beq OL_SET
                inx
OL_SET:         stx BOB_FRAME
OL_SHOW:        jmp SHOW_BOB            ; draw Bob (upside down once he has been fired from the cannon), and on
OL_UP:          dec BOB_Y               ; up a line
                inc MOVE_B
                dec MOVE_A              ; MOVE_A -= 1, until 0
                bne OL_FRAME
OL_OFF:         ldx #$00                ; off the ladder
                beq OL_SET

;-----------------------------------------------------------------------------
;  CHECK_LEFT / CHECK_RIGHT - may Bob move to x = X?  Out: A = 0 (Z set) if blocked.
;  The screen edges ($30 and $C9), the walls of station 6's waste box (x $43/$BD and
;  $3B/$B5 below line $8A), the TNT store on station 10 (x $31/$5D, lines $4B-$A8), and
;  on station 10 inside the cannon (x $71-$A5).
;-----------------------------------------------------------------------------
CHECK_LEFT:     cpx #$30                ; left edge
                bcc CK_BLOCKED
                lda CANNON_ST           ; inside the cannon?
                bne CK_CANNON_L
                lda STATION
                cmp #$0A                ; if A == $0A goto CK_TNT_L
                beq CK_TNT_L
                cmp #$06                ; if A <> 6 goto CK_RTS
                bne CK_RTS
                cpx #$43                ; station 6: the waste box's walls
                bcc CK_RTS
                beq CK_WASTE_Y
                cpx #$BE                ; if X >= $BE goto CK_OK
                bcs CK_OK
                cpx #$BD                ; if X <> $BD goto CK_RTS
                bne CK_RTS
CK_WASTE_Y:     lda BOB_Y               ; only at the box's height
                cmp #$8A                ; if A < $8A goto CK_RTS
                bcc CK_RTS
                cmp #$C0                ; if A >= $C0 goto CK_RTS
                bcs CK_RTS
CK_BLOCKED:     lda #$00
                rts
CK_CANNON_L:    cpx #$71                ; if X >= $71 goto CK_OK
                bcs CK_OK
                bcc CK_BLOCKED
CK_TNT_L:       lda BOB_Y               ; station 10: the TNT store's walls
                cpx #$31                ; if X == $31 goto CK_TNT_Y
                beq CK_TNT_Y
                cpx #$65                ; if X <> $65 goto CK_RTS
                bne CK_RTS
                cmp #$A9                ; if A >= $A9 goto CK_OK
                bcs CK_OK
CK_TNT_Y:       cmp #$4B                ; if A < $4B goto CK_OK
                bcc CK_OK
                bcs CK_TNT_WALL
CHECK_RIGHT:    cpx #$CA                ; right edge
                bcs CK_BLOCKED
                lda CANNON_ST           ; if CANNON_ST <> 0 goto CK_CANNON_R
                bne CK_CANNON_R
                lda STATION
                cmp #$0A                ; if A == $0A goto CK_TNT_R
                beq CK_TNT_R
                cmp #$06                ; if A <> 6 goto CK_RTS
                bne CK_RTS
                cpx #$B6                ; if X >= $B6 goto CK_OK
                bcs CK_OK
                cpx #$3B                ; if X < $3B goto CK_RTS
                bcc CK_RTS
                beq CK_WASTE_Y
                cpx #$B5                ; if X == $B5 goto CK_WASTE_Y
                beq CK_WASTE_Y
CK_OK:          lda #$01
CK_RTS:         rts
CK_TNT_R:       cpx #$5D                ; if X <> $5D goto CK_RTS
                bne CK_RTS
                lda BOB_Y
                cmp #$A9                ; if A >= $A9 goto CK_OK
                bcs CK_OK
                cmp #$4B                ; if A < $4B goto CK_OK
                bcc CK_OK
CK_TNT_WALL:    lda #$00                ; blocked, and a jump stops moving sideways
                sta MOVE_B
                rts
CK_CANNON_R:    cpx #$A6                ; if X >= $A6 goto CK_BLOCKED
                bcs CK_BLOCKED
                bcc CK_OK

;-----------------------------------------------------------------------------
;  START_JUMP - button pressed: begin a jump. MOVE_A = 0 (position in JUMP_ARC), MOVE_B =
;  -1/0/+1 from the stick, frame 11 or 12 depending on the way he faces.
;-----------------------------------------------------------------------------
START_JUMP:     ldx #$00
                stx FALL_LEN
                stx MOVE_A
                lda #$5A                ; jump sound
                sta SND3_F
                sta (pAUDF3,x)
                lda #$AA
                sta (pAUDC3,x)
                jsr READ_STICK          ; direction from the stick: left -1, right +1, else 0
                lsr a
                lsr a
                ldx #$FF
                lsr a
                bcc SJ_DIR
                inx
                lsr a
                bcs SJ_DIR
                inx
SJ_DIR:         stx MOVE_B
                ldx #$0B                ; frame 11, or 12 if facing left
                lda BOB_FRAME
                cmp #$04                ; if A < 4 goto SJ_FRAME
                bcc SJ_FRAME
                inx
SJ_FRAME:       stx BOB_FRAME

;-----------------------------------------------------------------------------
;  JUMPING - every other frame move MOVE_B sideways (unless blocked); every frame move
;  vertically by JUMP_ARC[MOVE_A]: 16 lines up with two short hovers, then down. Past
;  the end of the table Bob falls one line per frame until he lands.
;  On station 10 two spots jump straight to the falling part (index $29): the top of
;  the TNT store and the cannon's platform, so Bob cannot jump out of them.
;-----------------------------------------------------------------------------
JUMPING:        lda FRAMES
                and #$01                ; test bits $01
                bne JP_VERTICAL
                lda BOB_X
                clc
                adc MOVE_B
                tax
                lda MOVE_B              ; if MOVE_B bit 7 clear goto JP_RIGHT
                bpl JP_RIGHT
                jsr CHECK_LEFT          ; may Bob move left to x = X?
                jmp JP_MOVE
JP_RIGHT:       jsr CHECK_RIGHT         ; may Bob move right to x = X?
JP_MOVE:        beq JP_VERTICAL
                stx BOB_X
JP_VERTICAL:    ldx MOVE_A
                lda STATION
                cmp #$0A                ; if A <> $0A goto JP_ARC
                bne JP_ARC
                lda BOB_Y
                cmp #$A8                ; if A == $A8 goto JP_TNT
                beq JP_TNT
                cmp #$65                ; if A <> $65 goto JP_ARC
                bne JP_ARC
                lda BOB_X
                cmp #$5D                ; if A >= $5D goto JP_ARC
                bcs JP_ARC
                ldx #$29
                bne JP_ARC
JP_TNT:         lda BOB_X
                cmp #$5D                ; if A < $5D goto JP_ARC
                bcc JP_ARC
                cmp #$66                ; if A >= $66 goto JP_ARC
                bcs JP_ARC
                ldx #$29
JP_ARC:         lda JUMP_ARC,x
                cpx #$20                ; past the table: +1
                bcc JP_APPLY
                lda #$01
JP_APPLY:       inx
                stx MOVE_A
                clc
                adc BOB_Y
                sta BOB_Y
                ldy SND3_F              ; sound: pitch up while rising (index < $16) ...
                cpx #$16                ; if X < $16 goto JP_RISING
                bcc JP_RISING
                cpx #$2A                ; ... falling whistle after $2A ...
                bcs FA_SOUND
                iny                     ; ... else pitch down
                iny
                iny
                tya
                ldy #$00
                sta SND3_F
                sta (pAUDF3),y          ; AUDF3 = A
                lda #$AA                ; AUDC3 = $AA
                sta (pAUDC3),y          ; AUDC3 = A
                bcc LAND_CHECK
JP_RISING:      dey
                dey
                dey
                tya
                sta SND3_F
                ldy #$00
                sta (pAUDF3),y          ; AUDF3 = A
                bcc LC_SHOW

;-----------------------------------------------------------------------------
;  FALLING - one line down per frame with a falling whistle; then the landing test.
;-----------------------------------------------------------------------------
FALLING:        inc BOB_Y
FA_SOUND:       lda #$AA
                ldy #$00
                sta (pAUDC3),y          ; AUDC3 = A
                lda FRAMES
                and #$01                ; test bits $01
                bne LAND_CHECK
                inc SND3_F
                lda SND3_F              ; AUDF3 = SND3_F
                sta (pAUDF3),y          ; AUDF3 = A

;-----------------------------------------------------------------------------
;  LAND_CHECK - count the fall; if there is girder under x+3 or x+4 (and not 2 lines
;  higher, which would mean his feet are already inside it), land, lifting Bob one line
;  if needed. Forty or more frames of falling (FALL_LEN) kill him.
;-----------------------------------------------------------------------------
LAND_CHECK:     inc FALL_LEN
                jsr PROBE_FEET3         ; is there girder under Bob's feet at x = BOB_X + 3?
                beq LC_SOLID
                ldx PROBE_Y
                ldy PROBE_X
                iny
                jsr PROBE_AT_Y          ; girder at x = Y, line PROBE_Y?
                bne LC_SHOW
LC_SOLID:       ldx PROBE_Y             ; solid 2 lines up as well? still going through: carry on
                ldy PROBE_X
                dex
                dex
                jsr PROBE_AT            ; girder at x = Y, line X?
                beq LC_SHOW
                ldx PROBE_Y             ; solid 1 line below the feet as well? then he is a line too low: up one
                ldy PROBE_X
                inx
                jsr PROBE_AT            ; girder at x = Y, line X?
                bne LC_LANDED
                dec BOB_Y
LC_LANDED:      ldx #$00
                stx BOB_FALL
                lda FALL_LEN            ; fallen for 40 frames or more?
                cmp #$28                ; if A < $28 goto LC_SAFE
                bcc LC_SAFE
                jsr SHOW_BOB            ; draw Bob (upside down once he has been fired from the cannon), and on

;-----------------------------------------------------------------------------
;  START_DEATH - Bob dies: SPECIAL = 1 (MELT_BOB), melt starts at his top line, with a
;  decaying tone on voice 3.
;-----------------------------------------------------------------------------
START_DEATH:    ldx #$01                ; X = 1 for the (pointer,x) tricks below
                stx SPECIAL
                lda BOB_Y               ; MOVE_B = BOB_Y
                sta MOVE_B
                lda #$8F                ; (pAUDF3+1,x) = (pAUDC3): pure tone, volume 15
                sta (pAUDF3+1,x)
                lda #$0F                ; decays via SND3_VOL
                sta SND3_VOL
                lda #$96                ; (pAUDC2+1,x) = (pAUDF3)
                sta (pAUDC2+1,x)
SD_RTS:         rts
LC_SAFE:        lda #$00                ; meant to silence voice 3 like START_DEATH, but X = 0 here, so (pAUDF3+1,x)
                tax                     ; takes bytes $59/$5A (AUDF3's high byte, AUDC3's low byte) as the pointer:
                                        ;   $05D2
                sta (pAUDF3+1,x)        ; ($05E8 on the 5200), a line of player 1 - harmless, Bob is redrawn every
                                        ;   frame
                lda BOB_FRAME           ; standing frame facing the same way
                cmp #$05                ; if A < 5 goto LC_SHOW
                bcc LC_SHOW
                ldx #$01
                cmp #$0B                ; if A == $0B goto LC_FRAME
                beq LC_FRAME
                ldx #$04
LC_FRAME:       stx BOB_FRAME
LC_SHOW:        jmp SHOW_BOB            ; draw Bob (upside down once he has been fired from the cannon), and on

;-----------------------------------------------------------------------------
;  UPDATE_LIFTS - move the moving platforms (LIFT_TAB records, see INIT_LIFTS).
;  Each platform moves one pixel each time its timer runs out: the column at the leading
;  edge is drawn and the one at the trailing edge erased, so only 6 pixels change. After
;  "travel" steps it turns round. A platform carries Bob with it when his feet are on it.
;  Station 9's platforms wait at each end until Bob steps onto them.
;  On station 9 the column erased behind a platform between x $1E-$25 is redrawn in colour 2:
;  that is where a ladder passes behind it.
;-----------------------------------------------------------------------------
UPDATE_LIFTS:   ldy #$00
UL_LOOP:        sty CNT1
                lda LIFT_TAB,y          ; timer (0 = end of list)
                beq SD_RTS
                tya
                tax
                dec LIFT_TAB,x          ; count down
                beq UL_MOVE             ; time to move
UL_NEXT_X:      txa
UL_NEXT:        clc                     ; next record
                adc #$06
                tay
                jmp UL_LOOP
UL_MOVE:        lda (LIFTS),y           ; reload the timer from the station data
                sta LIFT_TAB,y
                lda STATION             ; station 8's lift is handled elsewhere
                cmp #$08                ; if A == 8 goto UL_STEP
                beq UL_STEP
                lda BOB_Y               ; Bob's feet on the platform's line ...
                clc
                adc #$15
                cmp LIFT_TAB+3,y        ; if A <> LIFT_TAB+3[Y] goto UL_STATION9
                bne UL_STATION9
                lda BOB_FALL            ; ... not falling ...
                bne UL_STATION9
                lda SPECIAL             ; ... walking or standing (or in a special state) ...
                bne UL_ON_X
                lda BOB_FRAME
                cmp #$07                ; if A >= 7 goto UL_STATION9
                bcs UL_STATION9
UL_ON_X:        lda LIFT_TAB+1,y        ; ... and within its width?
                clc
                adc #$05
                sta PLOT_X
                lda LIFT_TAB+2,y
                adc #$2E
                adc LIFT_TAB+1,y
                sec
                sbc BOB_X
                cmp PLOT_X              ; if A >= PLOT_X goto UL_STATION9
                bcs UL_STATION9
                lda BOB_X               ; yes: carry Bob along
                adc LIFT_TAB+5,y
                sta BOB_X
                jmp UL_STEP
UL_STATION9:    lda STATION             ; station 9: a platform at the start of its run waits for Bob
                cmp #$09                ; if A <> 9 goto UL_STEP
                bne UL_STEP
                tya
                clc
                adc #$04
                tay
                lda (LIFTS),y
                cmp LIFT_TAB+4,x        ; if A == LIFT_TAB+4[X] goto UL_NEXT_X
                beq UL_NEXT_X
                txa
                tay
UL_STEP:        lda LIFT_TAB+5,y        ; moving left or right?
                bpl UL_RIGHT
                dec LIFT_TAB+2,x        ; left: x - 1; draw at x, erase at x + width
                lda LIFT_TAB+2,y        ; PLOT_X = LIFT_TAB+2[Y]
                sta PLOT_X
                clc
                adc LIFT_TAB+1,y
                sta CNT2
                jmp UL_DRAW
UL_RIGHT:       lda LIFT_TAB+2,y        ; right: draw at x + width, erase at x; x + 1
                sta CNT2
                clc
                adc LIFT_TAB+1,y
                sta PLOT_X
                inc LIFT_TAB+2,x
UL_DRAW:        ldx #$08                ; leading column in colour 3 (colour 1 on station 8)
                lda STATION
                cmp #$08                ; if A <> 8 goto UL_DRAW2
                bne UL_DRAW2
                ldx #$00
UL_DRAW2:       jsr LIFT_COLUMN         ; 3 pixels down from the platform's line at x = PLOT_X, colour X
                lda CNT2                ; trailing column in the background colour ...
                sta PLOT_X
                ldx #$0C
                cmp #$1E                ; if A < $1E goto UL_ERASE
                bcc UL_ERASE
                cmp #$26                ; if A >= $26 goto UL_ERASE
                bcs UL_ERASE
                lda STATION             ; ... or colour 2 where station 9's ladder is
                cmp #$09                ; if A <> 9 goto UL_ERASE
                bne UL_ERASE
                ldx #$04
UL_ERASE:       jsr LIFT_COLUMN         ; 3 pixels down from the platform's line at x = PLOT_X, colour X
                tya                     ; end of the run?
                tax
                dec LIFT_TAB+4,x        ; LIFT_TAB+4[X] -= 1, goto UL_TURN if 0
                beq UL_TURN
                jmp UL_NEXT
UL_TURN:        lda #$00                ; reverse the direction and reload the run length
                sec
                sbc LIFT_TAB+5,y
                sta LIFT_TAB+5,y
                tya
                clc
                adc #$04
                tay
                lda (LIFTS),y           ; LIFT_TAB[Y] = (LIFTS)[Y]
                sta LIFT_TAB,y
                iny
                iny
                jmp UL_LOOP

;-----------------------------------------------------------------------------
;  LIFT_COLUMN - 3 pixels down from the platform's line at x = PLOT_X, colour X.
;-----------------------------------------------------------------------------
LIFT_COLUMN:    stx PLOT_COLOR
                ldx #$03
                stx CNT3
                lda LIFT_TAB+3,y        ; PLOT_Y = LIFT_TAB+3[Y]
                sta PLOT_Y
LC_LOOP:        ldy PLOT_X
                ldx PLOT_Y
                jsr PLOT_XY             ; set pixel (x = Y, line = X) to PLOT_COLOR
                inc PLOT_Y
                dec CNT3                ; CNT3 -= 1, until 0
                bne LC_LOOP
                ldy CNT1
CF_RTS:         rts

;-----------------------------------------------------------------------------
;  CLAIM_FLOOR - the heart of the game: the girder section under Bob's feet becomes his.
;
;  Runs every frame while Bob walks or stands (not on the bottom floor, not during the
;  start-up second, not dying, falling, sliding or in a special state). For the current
;  animation frame, FEET_OFFSETS gives the x of his two feet. Under each foot:
;    * the feet line must be girder (colour 3);
;    * an unclaimed section is striped, so one of the next two lines is background:
;      if the line below the feet is background, the gaps are at +1, +3, +5 (3 rows),
;      otherwise at +2, +4 (2 rows); if both lines are solid it is already claimed.
;    * claim it: SECTIONS - 1, score + 5, find the section's left edge (the stripe
;      pattern changes between neighbouring sections), and fill its gap rows with
;      colour 3, so the 4-pixel section turns solid.
;  The station is complete when SECTIONS reaches 0.
;-----------------------------------------------------------------------------
CLAIM_FLOOR:    ldy BOB_Y               ; not on the bottom floor
                cpy #$AA                ; if Y == $AA goto CF_RTS
                beq CF_RTS
                lda MOVE_OK             ; not before Bob may move
                beq CF_RTS
                lda KILLED              ; not when killed
                bne CF_RTS
                lda DYING               ; not when dying
                bne CF_RTS
                lda BOB_FALL            ; not when falling
                bne CF_RTS
                lda SLIDE_LEN           ; not when sliding
                bne CF_RTS
                lda SPECIAL             ; not in a special state
                bne CF_RTS
                lda BOB_FRAME           ; walking or standing only
                cmp #$07                ; if A >= 7 goto CF_RTS
                bcs CF_RTS
                asl a                   ; the two foot positions for this frame
                tax
                lda FEET_OFFSETS,x
                pha
                inx
                lda FEET_OFFSETS,x
                jsr CLAIM_AT            ; second foot
                pla                     ; first foot
                jmp CLAIM_AT
CLAIM_AT:       clc                     ; x = BOB_X + offset
                adc BOB_X
                sta PLOT_X
                lda BOB_Y               ; y = feet line
                clc
                adc #$15
                sta PLOT_Y
                jsr READ_PIXEL          ; girder under the foot?
                bne CF_RTS
                inc PLOT_Y              ; line below solid?
                jsr READ_PIXEL          ; colour of the pixel at P/M x = PLOT_X, line y = PLOT_Y (0 = background
                bne CA_THREE
                inc PLOT_Y              ; and the one after: if solid too, already claimed
                jsr READ_PIXEL          ; colour of the pixel at P/M x = PLOT_X, line y = PLOT_Y (0 = background
                beq CF_RTS
                ldx #$02                ; 2 gap rows (at +2, +4)
                bne CA_CLAIM
CA_THREE:       ldx #$03                ; 3 gap rows (at +1, +3, +5)
CA_CLAIM:       stx CNT0
                dec SECTIONS            ; one section fewer to go
                ldx #$06                ; 5 points (digit 6 = units)
                lda #$05
                jsr ADD_SCORE           ; add A to score digit X (1 = 100,000s
                dec PLOT_X              ; find the left edge of the section: solid just left of here (in a gap row)?
                jsr READ_PIXEL          ; colour of the pixel at P/M x = PLOT_X, line y = PLOT_Y (0 = background
                beq CA_FILL
                ldy #$03                ; no: look up to 3 more pixels left
                sty CNT1
CA_LEFT:        dec PLOT_X
                ldy PLOT_X
                cpy #$2F                ; left edge of the screen
                beq CA_EDGE
                jsr READ_PIXEL_PTR      ; colour of pixel x = Y on the line in PIX_PTR
                beq CA_FILL
                dec CNT1                ; CNT1 -= 1, until 0
                bne CA_LEFT
                inc PLOT_X              ; none: the section starts further right; step 4 right, then scan right
                inc PLOT_X
                inc PLOT_X
                inc PLOT_X
CA_RIGHT:       inc PLOT_X
CA_RIGHT_CHK:   ldy PLOT_X
                jsr READ_PIXEL_PTR      ; colour of pixel x = Y on the line in PIX_PTR
                bne CA_RIGHT
                lda PLOT_X              ; PLOT_X = PLOT_X - 5
                sec
                sbc #$05
                sta PLOT_X
CA_FILL:        inc PLOT_X              ; first pixel of the section
                ldy #$08                ; fill in colour 3
                sty PLOT_COLOR
                lda PLOT_X              ; P/M x -> pixel x
                sec
                sbc #$30
                sta PLOT_X
CA_ROW:         ldy #$03                ; 4 pixels in this gap row
                sty CNT1
                ldx PLOT_Y
                ldy PLOT_X
                jsr PLOT_XY             ; set pixel (x = Y, line = X) to PLOT_COLOR
CA_PIX:         inc PLOT_X
                ldy PLOT_X
                jsr PLOT_PTR            ; set pixel x = Y on the line already in PTR
                dec CNT1                ; CNT1 -= 1, until 0
                bne CA_PIX
                inc PLOT_Y              ; next gap row (2 lines down)
                inc PLOT_Y
                dec PLOT_X
                dec PLOT_X
                dec PLOT_X
                dec CNT0                ; CNT0 -= 1, until 0
                bne CA_ROW
                rts
CA_EDGE:        lda #$05                ; reached the left edge of the screen
                sec
                sbc CNT1
                clc
                adc PLOT_X
                sta PLOT_X
                jmp CA_RIGHT_CHK

;-----------------------------------------------------------------------------
;  READ_HITS - save the collision registers for band X: any missile touching a player
;  (M0PL..M3PL) in HIT_M, player 3 touching a player (P3PL) in HIT_P3. Bob is players
;  0-2, so bits 0-2 mean "touched Bob".
;-----------------------------------------------------------------------------
READ_HITS:      ldy #$00
                lda (pSIZEP0),y         ; A = M0PL
                ora (pSIZEP1),y         ; A |= M1PL
                ora (pSIZEP2),y         ; A |= M2PL
                ora (pSIZEP3),y         ; A |= M3PL
                sta MUT_SCORE,x
                lda (pGRAFP2),y         ; A = P3PL
                sta HIT_P3-1,x
                rts

;-----------------------------------------------------------------------------
;  DLI_MUTANTS - one DLI at the end of the status line and three more down the playfield
;  (bitmap lines 46, 93 and 140) divide the screen into four bands. Eight mutants share
;  two sprites: in each band one is drawn with player 3 and one with the four missiles
;  side by side (fifth-player mode, colour COLPF3). Each DLI:
;    * saves and clears the collisions of the band just finished (READ_HITS);
;    * re-positions player 3 and the missiles for this band's two mutants;
;    * sets band-specific things: the real playfield colours below the status line, the
;      transporter booth colour (green, or red while it recharges), the lift (station 8,
;      band 3) or the cannon (station 10, bottom band) which also use player 3 and the
;      missiles, and a flickering colour 1 in the bottom band on stations 5, 6, 8 and 9
;      (the radioactive waste glows);
;    * moves two mutants and draws their shapes (the work is spread over the four DLIs).
;-----------------------------------------------------------------------------
DLI_MUTANTS:    pha                     ; save A, X, Y
                txa
                pha
                tya
                pha
                lda DLI_BAND            ; first DLI of the frame (status line): no band finished yet
                cmp #$04                ; if A == 4 goto DM_HITCLR
                beq DM_HITCLR
                lda #$04                ; band index 1-4
                sec
                sbc DLI_BAND
                tax
                jsr READ_HITS           ; save the collision registers for band X
DM_HITCLR:      ldy #$00
                sta (pHITCLR),y         ; clear the collision registers
                lda SPECIAL             ; transporter state 5: Bob's colours flash in the booths involved
                cmp #$05                ; if A <> 5 goto DM_BAND
                bne DM_BAND
                ldx DLI_BAND
                cpx TRANS_SRC           ; if X == TRANS_SRC goto DM_FLASH
                beq DM_FLASH
                cpx TRANS_DEST          ; if X <> TRANS_DEST goto DM_BAND
                bne DM_BAND
                lda #$0E
                sec
                sbc MOVE_A
                bcs DM_FLASH_SET
DM_FLASH:       lda MOVE_A
DM_FLASH_SET:   sta (pCOLPM2),y         ; COLPM2 = A
                cmp #$0B                ; if A < $0B goto DM_FLASH2
                bcc DM_FLASH2
                lda #$0A
DM_FLASH2:      ora #$30
                sta (pCOLPM1),y         ; COLPM1 = A
                adc #$50
                sta (pCOLPM0),y         ; COLPM0 = A
DM_BAND:        lda DLI_BAND            ; which band?
                cmp #$04                ; if A == 4 goto DM_TOP
                beq DM_TOP
                cmp #$03                ; if A <> 3 goto DM_BAND1
                bne DM_BAND1
                lda STATION             ; band 3 on station 8: player 3 is the lift
                cmp #$08                ; if A <> 8 goto DM_BAND_J
                bne DM_BAND_J
                lda LIFT_X              ; HPOSP3 = LIFT_X
                sta (pHPOSP3),y         ; HPOSP3 = A
                lda #$0E                ; COLPM3 = $0E
                sta (pCOLPM3),y         ; COLPM3 = A
                lda #$01                ; double width
                sta (pSIZEP3),y         ; SIZEP3 = A
DM_BAND_J:      jmp DM_POSITION
DM_BAND1:       cmp #$01                ; if A <> 1 goto DM_POSITION
                bne DM_POSITION
                lda STATION             ; bottom band on station 10: the cannon (missiles + player 3)
                cmp #$0A                ; if A <> $0A goto DM_GLOW
                bne DM_GLOW
                lda CANNON_X
                ldx #$06
                clc
DM_CANNON:      sta (pHPOSM0,x)         ; HPOSM3 = x, M2 = x+2, M1 = x+4, M0 = x+6
                adc #$02
                dex
                dex
                bpl DM_CANNON
                sta (pHPOSP3),y         ; player 3 to the right of them
                lda #$04                ; COLPF3 = 4
                sta (pCOLPF3),y         ; COLPF3 = A
                sta (pCOLPM3),y         ; COLPM3 = A
                bne DM_POSITION
DM_GLOW:        cmp #$08                ; stations 5, 6, 8, 9: colour 1 flickers in the bottom band
                beq DM_GLOW_SET
                cmp #$09                ; if A == 9 goto DM_GLOW_SET
                beq DM_GLOW_SET
                cmp #$05                ; if A == 5 goto DM_GLOW_SET
                beq DM_GLOW_SET
                cmp #$06                ; if A <> 6 goto DM_POSITION
                bne DM_POSITION
DM_GLOW_SET:    ldx TRANS_LOCK
                lda FRAMES              ; a new random colour every 4 frames
                and #$03                ; test bits $03
                bne DM_COLPF0
                lda (pSKRES),y          ; A = RANDOM
                and #$F6
                clc
                adc #$06
                sta TRANS_LOCK
                tax
                bne DM_COLPF0
DM_TOP:         lda COLPF1_V            ; below the status line: the station's own colours 2 and 3
                sta (pCOLPF1),y         ; COLPF1 = A
                lda COLPF2_V            ; COLPF2 = COLPF2_V
                sta (pCOLPF2),y         ; COLPF2 = A
                lda #$00                ; missiles normal width (they are double width for the bonus box)
                sta (pSIZEM),y          ; SIZEM = A
                lda SPECIAL_X           ; transporter booths?
                beq DM_POSITION
                ldx #$C6                ; green ...
                lda TRANS_LOCK          ; if TRANS_LOCK == 0 goto DM_COLPF0
                beq DM_COLPF0
                lda FRAMES              ; ... red while it recharges: one step per 64 frames (128 from zone 5)
                and #$3F
                ora PAUSED
                bne DM_RED
                lda ZONE
                cmp #$05                ; if A < 5 goto DM_RECHARGE
                bcc DM_RECHARGE
                lda FRAMES
                and #$7F                ; test bits $7F
                bne DM_RED
DM_RECHARGE:    dec TRANS_LOCK          ; TRANS_LOCK -= 1, goto DM_COLPF0 if 0
                beq DM_COLPF0
DM_RED:         ldx #$42
DM_COLPF0:      txa
                sta (pCOLPF0),y         ; COLPF0 = A
DM_POSITION:    ldx MUT_IDX             ; the missile mutant of this band (the record after MUT_IDX)
                lda MUT_TAB+11,x        ; if MUT_TAB+11[X] == 0 goto DM_PLAYER3
                beq DM_PLAYER3
                ldx #$06                ; four missiles side by side, 2 apart
                clc
DM_MISSILES:    sta (pHPOSM0,x)
                adc #$02
                dex
                dex
                bpl DM_MISSILES
                ldx MUT_IDX             ; its colour
                lda MUT_TAB+14,x        ; COLPF3 = MUT_TAB+14[X]
                sta (pCOLPF3),y         ; COLPF3 = A
DM_PLAYER3:     lda MUT_TAB,x           ; the player-3 mutant of this band
                beq DM_LOGIC
                sta (pHPOSP3),y         ; HPOSP3 = A
                lda MUT_TAB+3,x         ; COLPM3 = MUT_TAB+3[X]
                sta (pCOLPM3),y         ; COLPM3 = A
DM_LOGIC:       lda #$02                ; update two mutants: the first drawn into the missiles ($0300) ...
                sta MUT_LOOP
                lda #$00                ; MUT_PM = 0
                sta MUT_PM
                lda #$03

;-----------------------------------------------------------------------------
;  MUT_UPDATE - move and animate one mutant; its record is at MUT_TAB + $4D - MUT_IDX.
;  Record (11 bytes, set up from the station's mutant list):
;    0 x (0 = none, 1 = eaten)    1 normal colour      2 state: bit 0 step, bit 1 facing,
;    3 colour now                 4 colour timer         bit 2 edible, 8/9 = eaten (the
;                                                        shape becomes "80" or "90")
;    5 brightness step (+/-2)     6 steps left in this direction
;    7 dx (+/-1)                  8 frames per step      9 animation timer
;   10 edible time
;  The station's list gives y, the step timer, the patrol length and the colour timer.
;-----------------------------------------------------------------------------
MUT_UPDATE:     sta MUT_PM+1
                ldy #$00
                lda #$4D
                sec
                sbc MUT_IDX
                tax
                lda MUT_TAB,x           ; nobody there (0) or eaten (1)?
                cmp #$02                ; if A < 2 goto MU_SKIP
                bcc MU_SKIP
                lda PAUSED              ; paused?
                bne MU_SKIP
                lda ALIVE               ; turn over?
                beq MU_SKIP
                lda SECTIONS            ; station cleared?
                bne MU_ACTIVE
MU_SKIP:        jmp MU_NEXT
MU_ACTIVE:      lda MUT_TAB+2,x         ; being eaten?
                cmp #$08                ; if A < 8 goto MU_HIT
                bcc MU_HIT
                lda (pSKRES),y          ; flashing random colour
                ora #$08
                sta MUT_TAB+3,x
                lda MUT_TAB+9,x         ; rising tone on voice 2 (AUDF2 counts down)
                sta (pAUDF2),y          ; AUDF2 = A
                lda #$8A                ; AUDC2 = $8A
                sta (pAUDC2),y          ; AUDC2 = A
                dec MUT_TAB+9,x
                jmp MU_ANIM
MU_HIT:         lda MUT_PM+1            ; did it touch Bob in its band? (collision bits 0-2 = players 0-2)
                clc
                adc DLI_BAND
                tay
                lda a:$00E2,y
                and MOVE_OK
                beq MU_COLOUR
                lda MUT_TAB+10,x        ; edible?
                beq MU_KILL
                lda #$FA                ; yes: Bob eats it: 80 or 90 points (added by GAME_VBI), then it flashes and
                                        ;   disappears
                sta MUT_TAB+9,x
                ldy #$00
                lda (pSKRES),y          ; A = RANDOM
                and #$01
                ora #$08
                sta MUT_SCORE
                jmp MU_SHAPE
MU_KILL:        sty KILLED              ; no: Bob is killed
MU_COLOUR:      dec MUT_TAB+4,x         ; colour timer
                bne MU_MOVE
                lda MUT_TAB+10,x        ; edible: blink green ($C6) / purple ($5A) ...
                beq MU_SHIMMER
                lda MUT_TAB+3,x
                eor #$9C
                sta MUT_TAB+3,x
                cmp #$C6                ; if A == $C6 goto MU_EDIBLE_TICK
                beq MU_EDIBLE_TICK
                lda #$05
                bne MU_BLINK
MU_EDIBLE_TICK: lsr MUT_TAB+10,x        ; ... and each green blink halves the time left
                lda MUT_TAB+10,x        ; if MUT_TAB+10[X] <> 0 goto MU_BLINK
                bne MU_BLINK
                lda MUT_TAB+1,x         ; edible time over: back to its own colour
                sta MUT_TAB+3,x
                lda MUT_TAB+2,x
                and #$03
                sta MUT_TAB+2,x
                lda #$02
MU_BLINK:       sta MUT_TAB+4,x
                bne MU_MOVE
MU_SHIMMER:     txa                     ; normal: brightness pulses up and down by 2
                clc
                adc #$04
                tay
                lda (MUTANTS),y         ; MUT_TAB+4[X] = (MUTANTS)[Y]
                sta MUT_TAB+4,x
                lda MUT_TAB+5,x         ; MUT_TAB+3[X] = MUT_TAB+5[X] + MUT_TAB+3[X]
                clc
                adc MUT_TAB+3,x
                sta MUT_TAB+3,x
                and #$0F                ; test bits $0F
                beq MU_STEP_UP
                cmp #$0E                ; if A <> $0E goto MU_MOVE
                bne MU_MOVE
                lda #$FE
                bne MU_STEP_SET
MU_STEP_UP:     lda #$02
MU_STEP_SET:    sta MUT_TAB+5,x
MU_MOVE:        dec MUT_TAB+8,x         ; time for a step?
                bne MU_ANIM
                txa                     ; next step after (list value + 1 - zone) frames, at least 1
                clc
                adc #$08
                tay
                lda (MUTANTS),y
                clc
                adc #$01
                sec
                sbc ZONE
                beq MU_FASTEST
                bcs MU_DELAY
MU_FASTEST:     lda #$01
MU_DELAY:       sta MUT_TAB+8,x
                lda MUT_TAB+7,x         ; x = x + dx
                clc
                adc MUT_TAB,x
                sta MUT_TAB,x
                dec MUT_TAB+6,x         ; end of the patrol?
                bne MU_ANIM
                dey                     ; turn round: reload the patrol length, negate dx, face the other way
                dey
                lda (MUTANTS),y         ; MUT_TAB+6[X] = (MUTANTS)[Y]
                sta MUT_TAB+6,x
                lda #$00                ; MUT_TAB+7[X] = 0 - MUT_TAB+7[X]
                sec
                sbc MUT_TAB+7,x
                sta MUT_TAB+7,x
                lda MUT_TAB+2,x
                eor #$02
                sta MUT_TAB+2,x
                jmp MU_ANIM_NOW
MU_ANIM:        dec MUT_TAB+9,x         ; animation timer
                bne MU_NEXT
MU_ANIM_NOW:    lda #$0A                ; MUT_TAB+9[X] = $0A
                sta MUT_TAB+9,x
                lda MUT_TAB+2,x         ; eaten and finished?
                cmp #$08                ; if A < 8 goto MU_NEXT_STEP
                bcc MU_NEXT_STEP
                lda #$00                ; voice 2 off, mutant gone
                tay
                sta (pAUDC2),y          ; AUDC2 = A
                lda #$01                ; MUT_TAB[X] = 1
                sta MUT_TAB,x
                bne MU_NEXT
MU_NEXT_STEP:   eor #$01                ; toggle the walking step
MU_SHAPE:       sta MUT_TAB+2,x         ; draw shape (state * 12) at the mutant's y + $20 in its P/M memory
                asl a
                asl a
                sta TMPEF
                asl a
                adc TMPEF
                pha
                txa
                tay
                iny
                lda (MUTANTS),y
                adc #$20
                tay
                pla
                tax
                lda #$0A                ; 10 lines
                sta TMPEF
MU_COPY:        lda MUTANT_SHAPES-2,x   ; (MUT_PM)[Y] = MUTANT_SHAPES-2[X]
                sta (MUT_PM),y
                inx
                iny
                dec TMPEF               ; TMPEF -= 1, until 0
                bne MU_COPY
MU_NEXT:        lda MUT_IDX             ; next record; the second one goes into player 3 ($0700)
                clc
                adc #$0B
                sta MUT_IDX
                lda #$07
                dec MUT_LOOP            ; MUT_LOOP -= 1, goto MU_DONE if 0
                beq MU_DONE
                jmp MUT_UPDATE          ; move and animate one mutant; its record is at MUT_TAB + $4D - MUT_IDX
MU_DONE:        dec DLI_BAND            ; next band
                jmp NMI_EXIT            ; common tail of every interrupt handler

;-----------------------------------------------------------------------------
;  READ_BUTTON - fire button into bit 0 of A (0 = pressed): TRIG0, or bit 4 of the
;  current demo input.
;-----------------------------------------------------------------------------
READ_BUTTON:    lda DEMO_PTR+1          ; demo?
                bne RB_DEMO
                sty SAVE_Y2
                ldy #$00
                lda (pTRIG0),y          ; A = TRIG0
                ldy SAVE_Y2
                rts
RB_DEMO:        jsr DEMO_INPUT          ; current byte of the demo recording
                and #$10
                lsr a
                lsr a
                lsr a
                lsr a
                rts

;-----------------------------------------------------------------------------
;  READ_STICK - joystick in the PORTA format (bit 0 up, 1 down, 2 left, 3 right; 0 means
;  pushed), from the demo recording, PORTA (400/800) or the 5200's analog stick.
;  The 5200 stick is turned into the same four bits: below $30 or above $B4 on either
;  pot counts as pushed.
;-----------------------------------------------------------------------------
READ_STICK:     lda DEMO_PTR+1          ; if DEMO_PTR+1 <> 0 goto RS_DEMO
                bne RS_DEMO
                lda IS5200              ; if IS5200 <> 0 goto RS_5200
                bne RS_5200
                lda PORTA               ; 400/800: stick 0 is the low nibble of PORTA
                rts
RS_DEMO:        jsr DEMO_INPUT          ; current byte of the demo recording
                and #$0F
                rts
RS_5200:        sty SAVE_Y2
                ldy POT_X
                lda #$0F
                cpy #$B4                ; far right
                bcc RS_LEFT
                eor #$08
RS_LEFT:        cpy #$30                ; far left
                bcs RS_Y
                eor #$04
RS_Y:           ldy POT_Y
                cpy #$B4                ; far down
                bcc RS_UP
                eor #$02
RS_UP:          cpy #$30                ; far up
                bcs RS_DONE
                eor #$01
                jmp RS_DONE
DEMO_INPUT:     sty SAVE_Y2             ; current byte of the recording
                ldy #$00
                lda (DEMO_PTR),y
RS_DONE:        ldy SAVE_Y2
                rts

;-----------------------------------------------------------------------------
;  CANNON - station 10, every frame.
;    state 0: the cannon rolls back to its rest position ($A1). If Bob, carrying TNT, steps
;             into its mouth he gets in (state 1).
;    state 1: the cannon follows Bob as he walks; the button fires it (state 2).
;    state 2: Bob flies up two lines a frame to a height set by the charge:
;             1 ton $5D, 2 tons $33, 3 tons $09 (the three upper platforms), 4 or more
;             and he is blown off the top of the screen (to $DF), turning upside down -
;             hence the "DANGER" warning.
;-----------------------------------------------------------------------------
CANNON:         ldx CANNON_ST
                dex
                beq CN_AIM
                dex
                beq CN_FLY
                lda CANNON_X            ; state 0: roll back one pixel every 4 frames
                cmp #$A1                ; if A == $A1 goto CN_REST
                beq CN_REST
                lda FRAMES
                and #$03                ; test bits $03
                bne CN_REST
                inc CANNON_X
CN_REST:        lda CANNON_X            ; Bob in the mouth (x = cannon + 4, y = $8F, on his feet)?
                clc
                adc #$04
                cmp BOB_X               ; if A <> BOB_X goto CN_EXIT
                bne CN_EXIT
                lda BOB_Y
                cmp #$8F                ; if A <> $8F goto CN_EXIT
                bne CN_EXIT
                lda BOB_FRAME
                cmp #$07                ; if A >= 7 goto CN_EXIT
                bcs CN_EXIT
                lda #$02                ; FALL_LEN = 2
                sta FALL_LEN
                lda TNT                 ; only with TNT on board
                beq CN_EXIT
                lda #$00                ; in he goes: state 1
                sta BOB_FALL
                inc CANNON_ST
CN_EXIT:        jmp NMI_EXIT            ; common tail of every interrupt handler
CN_AIM:         lda BOB_X               ; state 1: the cannon moves with Bob
                sec
                sbc #$04
                sta CANNON_X
                lda DYING               ; if DYING <> 0 goto CN_EXIT
                bne CN_EXIT
                lda SPECIAL             ; if SPECIAL <> 0 goto CN_EXIT
                bne CN_EXIT
                lda (pTRIG0,x)          ; fire?
                and #$01                ; test bits $01
                bne CN_EXIT
                ldx #$FF                ; fire: state 2, jump frame
                stx SND3_F
                inx
                stx MOVE_A
                stx FALL_LEN
                stx MOVE_B
                lda #$02                ; CANNON_ST = 2
                sta CANNON_ST
                ldx #$0B
                lda BOB_FRAME
                cmp #$04                ; if A < 4 goto CN_FRAME
                bcc CN_FRAME
                inx
CN_FRAME:       stx BOB_FRAME
                ldy #$00
CN_SOUND:       tya
                clc
                adc SND3_F
                sta SND3_F
                ldy #$00
                sta (pAUDF3),y          ; AUDF3 = A
                lda #$8F                ; AUDC3 = $8F
                sta (pAUDC3),y          ; AUDC3 = A
                jmp NMI_EXIT            ; common tail of every interrupt handler
CN_FLY:         dec BOB_Y               ; state 2: up 2 lines per frame
                dec BOB_Y
                ldy #$FE                ; target height from the charge
                lda #$5D
                ldx TNT
                dex
                beq CN_TARGET
                lda #$33
                dex
                beq CN_TARGET
                lda #$09
                dex
                beq CN_TARGET
                ldy #$FC                ; too much TNT: 4 lines per frame, to $DF (off the top)
                lda #$DF
                dec BOB_Y
                dec BOB_Y
CN_TARGET:      cmp BOB_Y               ; if A <> BOB_Y goto CN_SOUND
                bne CN_SOUND
                cmp #$DF                ; if A <> $DF goto CN_LAND
                bne CN_LAND
                sta CANNON_DONE         ; upside down from now on
CN_LAND:        inc BOB_Y
                inc BOB_Y
                lda #$00                ; cannon empty and unloaded
                sta CANNON_ST
                sta TNT
                jmp NMI_EXIT            ; common tail of every interrupt handler

;-----------------------------------------------------------------------------
;  VBI_TAIL - end of GAME_VBI: advance the demo recording, then station 10's cannon or
;  station 8's lift, then return from the interrupt.
;-----------------------------------------------------------------------------
VBI_TAIL:       lda DEMO_PTR+1          ; demo: count down the current input ...
                beq VT_STATION
                dec DEMO_CNT            ; DEMO_CNT -= 1, until 0
                bne VT_STATION
                lda DEMO_PTR            ; ... and move to the next (input, frames) pair
                clc
                adc #$02
                sta DEMO_PTR
                bcc VT_COUNT
                inc DEMO_PTR+1
VT_COUNT:       ldy #$01
                lda (DEMO_PTR),y        ; DEMO_CNT = (DEMO_PTR)[Y]
                sta DEMO_CNT
VT_STATION:     lda STATION
                cmp #$0A                ; if A <> $0A goto LIFT_CONTROL
                bne LIFT_CONTROL
                jmp CANNON              ; station 10, every frame

;-----------------------------------------------------------------------------
;  LIFT_CONTROL - station 8. Standing on the lift, SPACE (or the 5200's # key) hands the
;  joystick to the lift; SPACE or the button hands it back. While in control the stick
;  drives the lift (and Bob on it): left/right within x $67-$9B, up/down within lines
;  $59-$B3. It rises at half the speed it falls (a line every 4
;  frames up, every 2 down). The scissor arms are extended or
;  folded by one line each time the platform moves, and a motor hum plays on voice 3.
;-----------------------------------------------------------------------------
LIFT_CONTROL:   ldx LIFT_X              ; no lift?
                beq LC_EXIT
                ldx ON_LIFT             ; Bob not on it?
                bne LC_EXIT
                ldx LIFT_DLY
                lda LIFT_ON             ; already driving?
                bne LC_DRIVE
                lda BOB_FRAME           ; only when walking or standing ...
                cmp #$07                ; if A >= 7 goto LC_EXIT
                bcs LC_EXIT
                lda SPECIAL             ; if SPECIAL <> 0 goto LC_EXIT
                bne LC_EXIT
                lda DYING               ; if DYING <> 0 goto LC_EXIT
                bne LC_EXIT
                jsr LIFT_SPACE          ; ... and SPACE pressed
                bne LC_EXIT
                ldx #$05                ; take control
                stx JUMP_LOCK
                stx LIFT_DLY
LC_ON:          stx LIFT_ON
LC_EXIT:        jmp NMI_EXIT            ; common tail of every interrupt handler
LC_DRIVE:       jsr LIFT_KEY            ; SPACE or button again?
                bne LC_STICK
                ldx #$05                ; give control back, motor off
                stx LIFT_DLY
                lda #$00
                tax
                sta (pAUDC3,x)
                beq LC_ON
LC_STICK:       ldy #$00                ; motor hum
                lda #$4F                ; AUDC3 = $4F
                sta (pAUDC3),y          ; AUDC3 = A
                ldx #$00                ; direction from the stick
                jsr READ_STICK          ; joystick in the PORTA format (bit 0 up, 1 down, 2 left, 3 right; 0 mea
                lsr a
                bcs LC_DOWN
                ldy #$FF
LC_DOWN:        lsr a
                bcs LC_LEFT
                ldy #$01
LC_LEFT:        lsr a
                bcs LC_RIGHT
                ldx #$FF
LC_RIGHT:       lsr a
                bcs LC_PITCH
                ldx #$01
LC_PITCH:       lda #$5F                ; motor note: idle, or higher when moving sideways
                dex
                inx
                beq LC_UP
                lda #$17
LC_UP:          cpy #$FF                ; going up: only one frame in four
                bne LC_DOWN_NOTE
                lda FRAMES
                and #$03                ; test bits $03
                beq LC_UP_NOTE
                ldy #$00
LC_UP_NOTE:     lda #$1A
LC_DOWN_NOTE:   cpy #$01                ; if Y <> 1 goto LC_SET_NOTE
                bne LC_SET_NOTE
                lda #$17
LC_SET_NOTE:    sty SAVE_Y2
                ldy #$00
                sta (pAUDF3),y          ; AUDF3 = A
                lda FRAMES              ; move on even frames only
                and #$01                ; test bits $01
                bne LC_DONE
                txa                     ; sideways, within limits
                clc
                adc LIFT_X
                cmp #$67                ; if A == $67 goto LC_VERT
                beq LC_VERT
                cmp #$9B                ; if A == $9B goto LC_VERT
                beq LC_VERT
                sta LIFT_X
                txa                     ; Bob moves with it
                clc
                adc BOB_X
                sta BOB_X
                sta (pHPOSP0),y         ; HPOSP0 = A
                sta (pHPOSP1),y         ; HPOSP1 = A
                sta (pHPOSP2),y         ; HPOSP2 = A
LC_VERT:        ldy SAVE_Y2             ; up or down, within limits
                beq LC_DONE
                tya
                clc
                adc LIFT_Y
                cmp #$59                ; if A == $59 goto LC_DONE
                beq LC_DONE
                cmp #$B3                ; if A == $B3 goto LC_DONE
                beq LC_DONE
                sta LIFT_Y
                lda SAVE_Y2             ; Bob too
                clc
                adc BOB_Y
                sta BOB_Y
                ldx LIFT_ANIM           ; scissor phase +1 going down, -1 going up (cycle of 7)
                dey                     ; loop until Y = 0
                bne LC_PHASE_UP
                inx
                cpx #$07                ; if X <> 7 goto LC_PHASE
                bne LC_PHASE
                ldx #$00
                beq LC_PHASE
LC_PHASE_UP:    dex
                bpl LC_PHASE
                ldx #$06
LC_PHASE:       stx LIFT_ANIM
                ldy LIFT_Y              ; redraw the top of the lift in player 3: clear above, platform, scissor
                                        ;   line
                lda #$00                ; PM_P3+31[Y] = 0
                sta PM_P3+31,y
                lda #$FF                ; PM_P3+32[Y] = $FF
                sta PM_P3+32,y
                sta PM_P3+33,y
                lda LIFT_SCISSOR,x      ; PM_P3+34[Y] = LIFT_SCISSOR[X]
                sta PM_P3+34,y
                jsr SHOW_BOB            ; draw Bob (upside down once he has been fired from the cannon), and on
LC_DONE:        jmp NMI_EXIT            ; common tail of every interrupt handler

;-----------------------------------------------------------------------------
;  LIFT_KEY - Z set if the button (LIFT_KEY) or SPACE (LIFT_SPACE) has just been pressed:
;  LIFT_DLY must have counted down to 0 while nothing was pressed.
;-----------------------------------------------------------------------------
LIFT_KEY:       ldy #$00
                lda (pTRIG0),y          ; A = TRIG0
                and #$01                ; test bits $01
                beq LK_PRESSED
LIFT_SPACE:     lda KEYCODE
                cmp #$21                ; if A <> $21 goto LK_UP
                bne LK_UP
                lda #$FF                ; consume the key
                sta KEYCODE
LK_PRESSED:     dex                     ; pressed: Z set only if the delay had run out
                inx
                bne LK_RESTART
                rts
LK_UP:          dex                     ; not pressed: count the delay down
                bpl LK_SET
                rts
LK_RESTART:     ldx #$05
LK_SET:         stx LIFT_DLY
                inx
                rts

;-----------------------------------------------------------------------------
;  READ_POTS - 5200 analog stick: POT0 -> POT_X, POT1 -> POT_Y, start the next scan.
;-----------------------------------------------------------------------------
READ_POTS:      ldy #$00
                lda (pAUDF1),y          ; A = POT0
                sta POT_X
                lda (pAUDC1),y          ; A = POT1
                sta POT_Y
                sta (pPOTGO),y          ; POTGO = A
                rts

;-----------------------------------------------------------------------------
;  GAME_VBI - the game. Everything that moves runs here, once per frame:
;    frame counter, display list, the bonus box (missiles), P/M DMA, mutant band setup,
;    colours, 5200 pots, mutants turning edible, "time running out" warnings, pause,
;    status-line blink, Bob touching deadly scenery, dying, the extra-life jingle,
;    MOVE_BOB, moving platforms, Bob's sprite position and size, CLAIM_FLOOR,
;    pulverizers, end-of-turn timing, the credits reveal, status line, items, the bonus
;    timer, the end-of-station bonus count and screen wipe, mutant points, the phone-number
;    code, and finally VBI_TAIL (demo, cannon, lift).
;-----------------------------------------------------------------------------
GAME_VBI:       jsr POLL_KEYS           ; called at the start of every VBI handler
                inc FRAMES
                lda #$20                ; display list at $2000 (Y = 0 after POLL_KEYS)
                sta DLISTH
                sty DLISTL
                lda #$55                ; missiles double width: the box behind the bonus
                sta (pSIZEM),y          ; SIZEM = A
                lda #$84                ; HPOSM3 = $84, M2 = $80, M1 = $7C (M0 = $78, or $7C below 1000)
                ldx #$06
                sec
GV_BOX:         sta (pHPOSM0,x)
                sbc #$04
                dex
                dex                     ; loop until X = 0
                bne GV_BOX
                ldx STATUS+18           ; narrower box when the bonus is under 1000
                bne GV_BOX0
                lda #$7C
GV_BOX0:        sta (pHPOSM0),y         ; HPOSM0 = A
                ldx #$3E                ; DMACTL: normal width, players + missiles, single-line, display list
                stx DMACTL
                lda #$03                ; X = $3E: ($0C,x) = (pGRACTL): players and missiles on
                sta (pGRACTL-$3E,x)
                ldx #$04                ; the first DLI handles band 4
                stx DLI_BAND
                jsr READ_HITS           ; collisions of the last band of the previous frame
                tya
                sta (pSIZEP3),y         ; player 3 normal width, first mutant record
                sta MUT_IDX
                lda COLPF0_V            ; status line colours
                sta (pCOLPF0),y         ; COLPF0 = A
                lda COLBK_V             ; COLBK = COLBK_V
                sta (pCOLBK),y          ; COLBK = A
                sta (pCOLPF2),y         ; COLPF2 = A
                lda #$0C                ; COLPF1 = $0C
                sta (pCOLPF1),y         ; COLPF1 = A
                jsr READ_POTS           ; 5200 stick
                ldx ITEM_GOT            ; an item was picked up: every mutant still alive turns edible
                beq GV_WARN
                lda ZONE                ; edible time = $AF - 16 * min(zone, 9) (no SEC: carry is clear)
                cmp #$0A                ; if A < $0A goto GV_EDIBLE_TIME
                bcc GV_EDIBLE_TIME
                lda #$09
GV_EDIBLE_TIME: asl a
                asl a
                asl a
                asl a
                sta ITEM_GOT
                lda #$B0
                sbc ITEM_GOT
                sta ITEM_GOT
                ldx #$00
                ldy #$08
GV_EDIBLE:      lda MUT_TAB+2,x
                cmp #$08                ; if A >= 8 goto GV_EDIBLE_NEXT
                bcs GV_EDIBLE_NEXT
                ora #$04                ; edible, green, start blinking
                sta MUT_TAB+2,x
                lda #$01                ; MUT_TAB+9[X] = 1
                sta MUT_TAB+9,x
                lda #$C6                ; MUT_TAB+3[X] = $C6
                sta MUT_TAB+3,x
                lda ITEM_GOT            ; MUT_TAB+10[X] = ITEM_GOT
                sta MUT_TAB+10,x
                sta MUT_TAB+4,x
GV_EDIBLE_NEXT: txa
                clc
                adc #$0B
                tax
                dey                     ; loop until Y = 0
                bne GV_EDIBLE
                sty ITEM_GOT
GV_WARN:        ldy #$84                ; bonus box colour
                lda DYING               ; time running out (bonus under 700, Bob alive, station not done)?
                ora PAUSED
                bne GV_BOX_COL
                lda STATION
                cmp #$0B                ; if A == $0B goto GV_BOX_COL
                beq GV_BOX_COL
                lda ALIVE               ; if ALIVE == 0 goto GV_BOX_COL
                beq GV_BOX_COL
                ldx SPECIAL
                dex
                cpx #$02                ; if X < 2 goto GV_BOX_COL
                bcc GV_BOX_COL
                lda SECTIONS            ; if SECTIONS == 0 goto GV_BOX_COL
                beq GV_BOX_COL
                lda STATUS+18
                cmp #$11                ; if A >= $11 goto GV_BOX_COL
                bcs GV_BOX_COL
                ldx STATUS+19
                cpx #$17                ; if X >= $17 goto GV_BOX_COL
                bcs GV_BOX_COL
                ldx #$00                ; Bob's face colour flickers
                lda (pSKRES,x)
                and #$0A
                ora #$30
                sta (pCOLPM1,x)
                ldx STATUS+19           ; the box blinks (8 frames on, 8 off)
                lda FRAMES
                and #$0F
                cmp #$08                ; if A < 8 goto GV_TICK
                bcc GV_TICK
                ldy #$00
GV_TICK:        and #$03                ; a tick every 4 frames ...
                bne GV_BOX_COL
                lda SECTIONS            ; if SECTIONS == 0 goto GV_BOX_COL
                beq GV_BOX_COL
                cpx #$10                ; if X == $10 goto GV_BOX_COL
                beq GV_BOX_COL
                txa
                ldx #$00
                dec TICK_SND            ; ... with gaps that shrink as the bonus falls
                bne GV_TICK_VOL
                sec
                sbc #$11
                asl a
                adc #$02
                sta TICK_SND
                lda #$DC
                sta (pAUDF1,x)
                ldx #$AD
GV_TICK_VOL:    txa
                ldx #$00
                sta (pAUDC1,x)
GV_BOX_COL:     tya
                ldy #$00
                sta (pCOLPF3),y         ; COLPF3 = A
                lda ALIVE               ; turn over: nothing more
                beq GV_EXIT
                lda PAUSED              ; paused?
                beq GV_RUN
                jsr CHECK_PAUSE         ; ESC (5200
                lda PAUSED              ; if PAUSED == 0 goto GV_RUN
                beq GV_RUN
                jsr SILENCE             ; still paused: keep quiet
GV_EXIT:        jmp NMI_EXIT            ; common tail of every interrupt handler
GV_RUN:         dec BLINK_TMR           ; every 30 frames toggle CHACTL bit 0 (blank bit-7 characters): the score
                                        ;   blinks
                bne GV_TOUCH
                lda #$1E                ; BLINK_TMR = $1E
                sta BLINK_TMR
                lda #$01                ; BLINK_ON = 1 - BLINK_ON
                sec
                sbc BLINK_ON
                sta BLINK_ON
                sta CHACTL
GV_TOUCH:       lda DYING               ; already dying?
                bne GV_DYING
                lda #$00                ; Bob (players 0-2) touching pixel colour 1?
                ldx #$04
GV_TOUCH_LOOP:  ora (pHPOSM0,x)         ; (pHPOSM2,x) .. (pHPOSM0,x) read P2PF, P1PF, P0PF
                dex
                dex
                bpl GV_TOUCH_LOOP
                ldy STATION
                and #$01                ; test bits $01
                beq GV_KILLED
                cpy #$06                ; deadly on station 6 (the waste), 8 (its moving bar) ...
                beq GV_DIE
                cpy #$08                ; if Y == 8 goto GV_DIE
                beq GV_DIE
                cpy #$09                ; ... and 9 (a pulverizer: a jump is stopped dead)
                bne GV_KILLED
                lda BOB_FRAME
                cmp #$0B                ; if A < $0B goto GV_DIE
                bcc GV_DIE
                lda #$20                ; MOVE_A = $20
                sta MOVE_A
                lda #$00                ; MOVE_B = 0
                sta MOVE_B
                beq GV_DIE
GV_KILLED:      lda KILLED              ; touched by a mutant or out of time?
                beq GV_XLIFE
GV_DIE:         ldx #$01                ; Bob starts dying
                stx DYING
                dex
                stx LIFT_ON
                lda STATION             ; station 10: inside or beside the cannon he melts at once
                cmp #$0A                ; if A <> $0A goto GV_DIE_POSE
                bne GV_DIE_POSE
                ldx CANNON_ST
                dex
                beq GV_MELT
                dex
                beq GV_DIE_POSE
                lda TNT                 ; if TNT == 0 goto GV_DIE_POSE
                beq GV_DIE_POSE
                lda BOB_FRAME
                cmp #$07                ; if A >= 7 goto GV_DIE_POSE
                bcs GV_DIE_POSE
                lda CANNON_X
                clc
                adc #$04
                cmp BOB_X               ; if A <> BOB_X goto GV_DIE_POSE
                bne GV_DIE_POSE
                lda BOB_Y
                cmp #$7C                ; if A < $7C goto GV_DIE_POSE
                bcc GV_DIE_POSE
                cmp #$92                ; if A < $92 goto GV_MELT
                bcc GV_MELT
GV_DIE_POSE:    lda BOB_FRAME           ; in the air: wait until he lands
                cmp #$0B                ; if A >= $0B goto GV_THROB
                bcs GV_THROB
                cmp #$07                ; on a ladder: he lets go and falls (a fatal fall)
                bcc GV_DYING2
                sta BOB_FALL
                dec BOB_Y
                ldx #$1E
                stx SND3_F
                ldx #$32
                stx FALL_LEN
                bne GV_THROB
GV_DYING:       lda BOB_FRAME           ; dying and in the air: wait
                cmp #$0B                ; if A >= $0B goto GV_THROB
                bcs GV_THROB
GV_DYING2:      lda SPECIAL             ; on the ground and not yet melting: melt
                bne GV_THROB
                lda BOB_FALL            ; if BOB_FALL <> 0 goto GV_THROB
                bne GV_THROB
GV_MELT:        jsr START_DEATH         ; Bob dies
GV_THROB:       lda FRAMES              ; every 4 frames: noise, and Bob's size pulses (DYING 4,3,2,1,4 ...)
                and #$03                ; test bits $03
                bne GV_XLIFE
                ldx #$00
                lda (pSKRES,x)
                and #$0F
                sta (pAUDF1,x)
                lda #$8E
                sta (pAUDC1,x)
                ldx DYING
                dex                     ; loop until X = 0
                bne GV_THROB_SET
                ldx #$04
GV_THROB_SET:   stx DYING
GV_XLIFE:       lda XLIFE               ; extra-life jingle playing (XLIFE 1-9)?
                beq GV_XLIFE_OFF
                cmp #$0A                ; if A == $0A goto GV_XLIFE_OFF
                beq GV_XLIFE_OFF
                lda FRAMES              ; every 16 frames one note
                and #$0F                ; test bits $0F
                bne GV_XLIFE_NOTE
                dec XLIFE               ; XLIFE -= 1, until 0
                bne GV_XLIFE_NOTE
                ldx #$00                ; finished: voice 4 off
                txa
                sta (pAUDC4,x)
                beq GV_XLIFE_OFF
GV_XLIFE_NOTE:  cmp #$08                ; each 16 frames: 8 frames of note $8C on a blue background, 8 of note $64
                                        ;   on black
                bcc GV_XLIFE_ON
                lda #$00
                ldx #$64
                bne GV_XLIFE_SET
GV_XLIFE_ON:    lda #$88
                ldx #$8C
GV_XLIFE_SET:   ldy #$00
                pha
                txa
                sta (pAUDF4),y          ; AUDF4 = A
                lda #$AA                ; AUDC4 = $AA
                sta (pAUDC4),y          ; AUDC4 = A
                pla
                jmp GV_BACKGROUND
GV_XLIFE_OFF:   lda #$00
GV_BACKGROUND:  sta COLBK_V
                lda MOVE_OK             ; Bob may move, the station is not finished and he is not driving the lift?
                beq GV_POSITION
                lda SECTIONS            ; if SECTIONS == 0 goto GV_POSITION
                beq GV_POSITION
                lda LIFT_ON             ; if LIFT_ON <> 0 goto GV_POSITION
                bne GV_POSITION
                lda CANNON_ST           ; flying from the cannon: only redraw him
                cmp #$02                ; if A <> 2 goto GV_MOVE
                bne GV_MOVE
                jsr SHOW_BOB            ; draw Bob (upside down once he has been fired from the cannon), and on
                jmp GV_TRAIL
GV_MOVE:        jsr MOVE_BOB            ; move Bob
                lda STATION
                cmp #$0A                ; if A <> $0A goto GV_POSITION
                bne GV_POSITION
GV_TRAIL:       lda CANNON_DONE         ; station 10: wipe the 5 lines under Bob's sprite (he can move 2 lines a
                                        ;   frame)
                bne GV_POSITION
                ldx SPECIAL             ; if SPECIAL <> 0 goto GV_POSITION
                bne GV_POSITION
                lda BOB_Y
                clc
                adc #$30
                tax
                ldy #$05
                lda #$00
GV_TRAIL_LOOP:  sta KERNEL_DELAY1,x
                sta PM_P1,x
                sta PM_P2+6,x
                inx
                dey                     ; loop until Y = 0
                bne GV_TRAIL_LOOP
GV_POSITION:    jsr UPDATE_LIFTS        ; moving platforms
                lda SECTIONS            ; Bob's horizontal position (0 = off screen once the station is cleared) ...
                beq GV_HPOS
                ldy DYING
                lda BOB_X               ; ... offset to keep him centred while he throbs
                clc
                adc BOB_SIZE_X,y
GV_HPOS:        ldx #$00
                sta (pHPOSP0,x)
                sta (pHPOSP1,x)
                sta (pHPOSP2,x)
                lda BOB_SIZE,y          ; width of players 0-2 (normal, double, quadruple)
                sta (pSIZEP0,x)
                sta (pSIZEP1,x)
                sta (pSIZEP2,x)
                jsr CLAIM_FLOOR         ; claim girder sections
                jsr MOVE_PULVERIZERS    ; station 9's pulverizers
                lda FRAMES              ; every 4 frames voice 3 fades one step
                and #$03                ; test bits $03
                bne GV_DEAD
                tay
                ldx SND3_VOL            ; if SND3_VOL == 0 goto GV_DEAD
                beq GV_DEAD
                dex
                stx SND3_VOL
                txa
                ora #$80
                sta (pAUDC3),y          ; AUDC3 = A
GV_DEAD:        lda SPECIAL             ; dead (and not during the extra-life jingle): end the turn after two
                                        ;   seconds
                cmp #$02                ; if A <> 2 goto GV_CREDITS
                bne GV_CREDITS
                ldx XLIFE
                dex
                cpx #$09                ; if X < 9 goto GV_CREDITS
                bcc GV_CREDITS
                lda ALIVE               ; if ALIVE == 0 goto GV_CREDITS
                beq GV_CREDITS
                dec SEC_TMR             ; SEC_TMR -= 1, until 0
                bne GV_CREDITS
                ldx #$3C
                stx SEC_TMR
                dec ALIVE
GV_CREDITS:     lda STATION             ; credits screen: reveal the hidden text around Bob
                cmp #$0B                ; if A <> $0B goto GV_PLAY
                bne GV_PLAY
                lda BOB_Y               ; 30 lines from 12 above Bob's top ...
                sec
                sbc #$0C
                sta PLOT_Y
                lda #$1E                ; CNT3 = $1E
                sta CNT3
                lda BOB_X               ; ... at x = BOB_X + 3
                clc
                adc #$03
                sta PLOT_X
                lda #$04                ; recolour in colour 2
                sta PLOT_COLOR
GV_REVEAL:      ldy PLOT_Y
                cpy #$08                ; if Y < 8 goto GV_REVEAL_NEXT
                bcc GV_REVEAL_NEXT
                cpy #$BF                ; if Y >= $BF goto GV_REVEAL_NEXT
                bcs GV_REVEAL_NEXT
                jsr READ_PIXEL          ; a hidden (colour 1) pixel?
                cmp #$01                ; if A <> 1 goto GV_REVEAL_NEXT
                bne GV_REVEAL_NEXT
                lda PLOT_X
                sec
                sbc #$30
                tay
                jsr PLOT_YX_Y           ; set pixel (x = Y, line = PLOT_Y) to PLOT_COLOR
GV_REVEAL_NEXT: inc PLOT_Y
                dec CNT3                ; CNT3 -= 1, until 0
                bne GV_REVEAL
                jmp VBI_TAIL            ; end of GAME_VBI
GV_PLAY:        jsr DRAW_STATUS         ; status line
                jsr UPDATE_ITEMS        ; items
                lda DYING               ; dying or dead: no timer
                bne BD_DONE
                ldx SPECIAL
                dex
                cpx #$02                ; if X < 2 goto BD_DONE
                bcc BD_DONE
                lda SECTIONS            ; station cleared: count the bonus into the score
                beq TALLY
                dec BONUS_TMR           ; bonus timer: -100 every 180 frames (3 seconds)
                bne BD_DONE
                lda #$B4                ; BONUS_TMR = $B4
                sta BONUS_TMR
BONUS_DOWN:     dec STATUS+19           ; hundreds digit - 1
                lda STATUS+19
                cmp #$10                ; if A == $10 goto BD_ZERO
                beq BD_ZERO
                bcs BD_DONE
                lda #$19                ; borrow from the thousands
                sta STATUS+19
                dec STATUS+18
                lda STATUS+18
                cmp #$10                ; if A <> $10 goto GV_MUTSCORE
                bne GV_MUTSCORE
                lda #$00                ; (a leading zero is shown as a blank)
                sta STATUS+18
                beq GV_MUTSCORE
BD_ZERO:        ldx STATUS+18           ; bonus 0 while sections remain: out of time
                bne GV_MUTSCORE
                lda SECTIONS            ; if SECTIONS == 0 goto GV_MUTSCORE
                beq GV_MUTSCORE
                inx
                stx KILLED
                bne GV_MUTSCORE
BD_DONE:        jmp GV_MUTSCORE
TALLY:          tay                     ; station cleared: voices 2 and 3 off
                sta (pAUDC3),y          ; AUDC3 = A
                sta (pAUDC2),y          ; AUDC2 = A
                lda STATUS+18           ; bonus left?
                ora STATUS+19
                cmp #$10                ; if A == $10 goto WIPE
                beq WIPE
                lda FRAMES              ; every 4 frames: a click, +100 to the score, -100 from the bonus
                and #$03                ; test bits $03
                beq TALLY_STEP
                cmp #$02                ; if A <> 2 goto GV_MUTSCORE
                bne GV_MUTSCORE
                tya
                sta (pAUDC4),y          ; AUDC4 = A
                beq GV_MUTSCORE
TALLY_STEP:     lda #$AA
                ldx #$04
                sta (pAUDC3,x)
                lda #$01
                jsr ADD_SCORE           ; add A to score digit X (1 = 100,000s
                lda #$3F                ; X = $3F: ($1D,x) = (pAUDF4): AUDF4 = $3F
                tax
                sta (pHPOSM2+1,x)
                bne BONUS_DOWN
WIPE:           ldx XLIFE               ; bonus all counted (and no jingle playing): wipe the screen from the bottom
                dex
                cpx #$09                ; if X < 9 goto GV_MUTSCORE
                bcc GV_MUTSCORE
                ldx WIPE_LINE           ; remove the mutants' P/M data on this line
                lda #$00                ; PM_MISSILES+39[X] = 0
                sta PM_MISSILES+39,x
                sta PM_P3+39,x
                lda #$41                ; replace this display-list line by a JVB: the picture ends here
                cpx #$62                ; if X >= $62 goto WIPE_LMS
                bcs WIPE_LMS
                sta DLIST+5,x
                bcc WIPE_NEXT
WIPE_LMS:       sta DLIST+7,x           ; (lines after the LMS sit 2 bytes further on)
WIPE_NEXT:      dex
                stx WIPE_LINE
                txa                     ; rising tone
                ldx #$00
                sta (pAUDF4,x)
                lda #$AA
                sta (pAUDC4,x)
GV_MUTSCORE:    lda MUT_SCORE           ; a mutant was eaten: 80 or 90 points (digit 5 = tens)
                beq GV_PAUSE
                ldx #$05
                jsr ADD_SCORE           ; add A to score digit X (1 = 100,000s
                sta MUT_SCORE
GV_PAUSE:       jsr CHECK_PAUSE         ; ESC pauses
                ldx PAUSED              ; if PAUSED == 0 goto PHONE_CODE
                beq PHONE_CODE
                jsr SILENCE             ; all four voices off (SILENCE_234 leaves voice 1 alone; A must be 0)
                jmp NMI_EXIT            ; common tail of every interrupt handler

;-----------------------------------------------------------------------------
;  PHONE_CODE - the famous cheat: type Big Five's phone number, 213-782-6861, during a
;  game, then a station number with SHIFT, and that station starts at once. The code is
;  checked against the number as printed in the credits text, "(213) 782-6861", skipping
;  ")", the space and "-". A wrong digit starts the count again; holding a key (the same
;  digit repeating) is ignored. Once all 13 positions are matched, SHIFT + digit warps.
;-----------------------------------------------------------------------------
PHONE_CODE:     jsr READ_DIGIT          ; a digit key?
                beq PC_EXIT
                ldx CHEAT_IDX           ; whole number typed?
                cpx #$0D                ; if X >= $0D goto PC_WARP
                bcs PC_WARP
                tya                     ; digit -> screen code
                clc
                adc #$10
                cmp CHEAT_CODE,x        ; the next digit of the number?
                beq PC_MATCH
                cmp LASTCHAR            ; the same key still repeating?
                beq PC_EXIT
                ldx #$FF                ; wrong: start again
PC_MATCH:       sta LASTCHAR
                inx
                lda CHEAT_CODE,x        ; skip ") " and "-"
                cmp #$09                ; if A <> 9 goto PC_DASH
                bne PC_DASH
                inx
                inx
PC_DASH:        cmp #$0D                ; if A <> $0D goto PC_SET
                bne PC_SET
                inx
PC_SET:         stx CHEAT_IDX
PC_EXIT:        jmp VBI_TAIL            ; end of GAME_VBI
PC_WARP:        ldx #$00                ; code complete: SHIFT held (SKSTAT bit 3 = 0)?
                lda (pSKCTL,x)
                and #$08                ; test bits $08
                bne PC_EXIT
                sty STATION             ; station = the digit (0 means 10), and start it
                jmp PLAY_STATION        ; build STATION and run it until the turn ends

;-----------------------------------------------------------------------------
;  SILENCE - all four voices off (SILENCE_234 leaves voice 1 alone; A must be 0).
;-----------------------------------------------------------------------------
SILENCE:        lda #$00
                tay
                sta (pAUDC1),y          ; AUDC1 = A
SILENCE_234:    tay
                sta (pAUDC2),y          ; AUDC2 = A
                sta (pAUDC3),y          ; AUDC3 = A
                sta (pAUDC4),y          ; AUDC4 = A
                rts

;-----------------------------------------------------------------------------
;  CHECK_PAUSE - ESC (5200: PAUSE) toggles PAUSED, with a debounce. Not in the demo.
;-----------------------------------------------------------------------------
CHECK_PAUSE:    lda DEMO_PTR+1          ; if DEMO_PTR+1 <> 0 goto PAUSE_RTS
                bne PAUSE_RTS
                lda KEYCODE
                cmp #$1C                ; if A == $1C goto PAUSE_KEY
                beq PAUSE_KEY
                ldx PAUSE_DLY           ; if PAUSE_DLY == 0 goto PAUSE_RTS
                beq PAUSE_RTS
                dec PAUSE_DLY
PAUSE_RTS:      rts
PAUSE_KEY:      lda #$FF                ; KEYCODE = $FF
                sta KEYCODE
                ldy #$1E
                ldx PAUSE_DLY
                sty PAUSE_DLY
                bne PAUSE_RTS
                lda #$01                ; toggle
                sec
                sbc PAUSED
                sta PAUSED
                rts

;-----------------------------------------------------------------------------
;  JUMP_ARC - vertical movement per frame of a jump: 11 lines up, a pause, 3 up, pause,
;  2 up, pause, then down again; after index $1F Bob simply falls 1 line per frame.
;  (Indexes 30 and 31 read the zeros at the start of BOB_SIZE.)
;-----------------------------------------------------------------------------
JUMP_ARC:       .byte $FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF,$FF
                .byte $FF,$00,$00,$FF,$FF,$FF,$00,$00,$FF,$FF
                .byte $00,$00,$00,$01,$01,$00,$00,$01,$01,$01

;-----------------------------------------------------------------------------
;  BOB_SIZE / BOB_SIZE_X - while dying, DYING (1-4) picks the players' width (SIZEP:
;  0 normal, 1 double, 3 quadruple) and an x offset that keeps Bob centred: he throbs.
;-----------------------------------------------------------------------------
BOB_SIZE:       .byte $00,$00,$01,$03,$01
BOB_SIZE_X:     .byte $00,$00,$FC,$F8,$FC

;-----------------------------------------------------------------------------
;  FEET_OFFSETS - for walking/standing frames 0-6, the x offsets of Bob's two feet
;  (the pixels CLAIM_FLOOR looks under).
;-----------------------------------------------------------------------------
FEET_OFFSETS:   .byte $01,$06
                .byte $03,$05
                .byte $03,$06
                .byte $02,$06
                .byte $02,$04
                .byte $01,$04
                .byte $01,$05

;-----------------------------------------------------------------------------
;  Unused.
;-----------------------------------------------------------------------------
UNUSED_END:     .byte $05,$00,$00,$00,$00,$00,$00

;-----------------------------------------------------------------------------
;  The cartridge trailer. On the 400/800:
;    $BFFA start address (RESTART)         $BFFC 0 = a cartridge is present
;    $BFFD option byte $FF: bit 7 "diagnostic cartridge" = jump to the init address
;          straight after RESET, before the OS initialises anything
;    $BFFE init address (COLD_START)
;  On the 5200 the BIOS reads $BFFD = $FF as "skip the title screen" and starts the game
;  through $BFFE: the same bytes serve both machines.
;-----------------------------------------------------------------------------
CART_TRAILER:   .word RESTART
                .byte $00,$FF
                .word COLD_START
