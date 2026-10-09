"""Atari hardware register names (400/800 addresses) and the game's zero-page pointer table."""
import os as _os, sys as _sys
REPO = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
for _d in ('tools', 'emulator', 'web/tools'):
    if _os.path.join(REPO, _d) not in _sys.path: _sys.path.insert(0, _os.path.join(REPO, _d))

GTIA_W = ['HPOSP0', 'HPOSP1', 'HPOSP2', 'HPOSP3', 'HPOSM0', 'HPOSM1', 'HPOSM2', 'HPOSM3',
          'SIZEP0', 'SIZEP1', 'SIZEP2', 'SIZEP3', 'SIZEM', 'GRAFP0', 'GRAFP1', 'GRAFP2',
          'GRAFP3', 'GRAFM', 'COLPM0', 'COLPM1', 'COLPM2', 'COLPM3', 'COLPF0', 'COLPF1',
          'COLPF2', 'COLPF3', 'COLBK', 'PRIOR', 'VDELAY', 'GRACTL', 'HITCLR', 'CONSOL']
GTIA_R = ['M0PF', 'M1PF', 'M2PF', 'M3PF', 'P0PF', 'P1PF', 'P2PF', 'P3PF',
          'M0PL', 'M1PL', 'M2PL', 'M3PL', 'P0PL', 'P1PL', 'P2PL', 'P3PL',
          'TRIG0', 'TRIG1', 'TRIG2', 'TRIG3', 'PAL', None, None, None,
          None, None, None, None, None, None, None, 'CONSOL']
POKEY_W = ['AUDF1', 'AUDC1', 'AUDF2', 'AUDC2', 'AUDF3', 'AUDC3', 'AUDF4', 'AUDC4',
           'AUDCTL', 'STIMER', 'SKRES', 'POTGO', None, 'SEROUT', 'IRQEN', 'SKCTL']
POKEY_R = ['POT0', 'POT1', 'POT2', 'POT3', 'POT4', 'POT5', 'POT6', 'POT7',
           'ALLPOT', 'KBCODE', 'RANDOM', None, None, 'SERIN', 'IRQST', 'SKSTAT']
ANTIC_W = ['DMACTL', 'CHACTL', 'DLISTL', 'DLISTH', 'HSCROL', 'VSCROL', None, 'PMBASE',
           None, 'CHBASE', 'WSYNC', None, None, None, 'NMIEN', 'NMIRES']
ANTIC_R = [None] * 11 + ['VCOUNT', 'PENH', 'PENV', None, 'NMIST']
PIA = ['PORTA', 'PORTB', 'PACTL', 'PBCTL']

def hwname(a, write):
    if 0xD000 <= a < 0xD100:
        r = a & 0x1F
        n = (GTIA_W if write else GTIA_R)[r]
        return n
    if 0xD200 <= a < 0xD300:
        return (POKEY_W if write else POKEY_R)[a & 0x0F]
    if 0xD300 <= a < 0xD400:
        return PIA[a & 3]
    if 0xD400 <= a < 0xD500:
        return (ANTIC_W if write else ANTIC_R)[a & 0x0F]
    return None

def zpptr(z, write):
    """The game's pointer table: $10+2r -> GTIA register r (r<32), $50+2r -> POKEY register r."""
    if 0x10 <= z < 0x50 and z % 2 == 0:
        r = (z - 0x10) // 2
        return (GTIA_W if write else GTIA_R)[r]
    if 0x50 <= z < 0x70 and z % 2 == 0:
        r = (z - 0x50) // 2
        return (POKEY_W if write else POKEY_R)[r]
    return None

OSVEC = {0x0200: 'VDSLST', 0x0201: 'VDSLST+1', 0x0222: 'VVBLKI', 0x0223: 'VVBLKI+1',
         0x0202: 'VVBLKI5200', 0x0203: 'VVBLKI5200+1', 0x0204: 'VVBLKD5200', 0x0205: 'VVBLKD5200+1',
         0x0206: 'VDSLST5200', 0x0207: 'VDSLST5200+1'}
