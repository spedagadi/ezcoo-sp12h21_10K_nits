#!/usr/bin/env python3
import sys


def mfg(d):
    v = (d[8] << 8) | d[9]
    return ''.join(chr(((v >> s) & 0x1f) + 64) for s in (10, 5, 0))


def le16(d, o):
    return d[o] | (d[o + 1] << 8)


def be16(d, o):
    return (d[o] << 8) | d[o + 1]


def hexs(b):
    return ' '.join('%02x' % x for x in b)


def parse(path):
    d = open(path, 'rb').read()
    print('== %s (%d bytes) ==' % (path, len(d)))
    if len(d) < 128 or d[:8] != b'\x00\xff\xff\xff\xff\xff\xff\x00':
        print('   bad EDID header')
        return
    print('   mfg=%s product=0x%04x serial=0x%08x week=%d year=%d edid=%d.%d'
          % (mfg(d), be16(d, 10), le16(d, 12), d[16], 1990 + d[17], d[18], d[19]))
    print('   size=%dx%dcm gamma=%s features=0x%02x ext=%d'
          % (d[21], d[22], 'defined' if d[23] == 0xff else '%.2f' % ((d[23] + 100) / 100.0),
             d[24], d[126]))
    for i in range(4):
        o = 54 + i * 18
        pc = le16(d, o)
        if not pc:
            continue
        ha = d[o + 2] | ((d[o + 4] & 0xf0) << 4)
        va = d[o + 5] | ((d[o + 7] & 0xf0) << 4)
        print('   DTD%d: %dx%d pclk=%dkHz' % (i, ha, va, pc * 10))
    for e in range(d[126]):
        off = 128 + e * 128
        ext = d[off:off + 128]
        if len(ext) < 128:
            break
        print('   -- ext %d: tag=0x%02x' % (e, ext[0]))
        if ext[0] != 0x02:
            continue
        start = ext[2]
        end = start if 4 <= start <= 127 else 127
        print('      CEA rev=%d dtd_start=%d' % (ext[1], start))
        i = 4
        while i < end:
            tag = ext[i] >> 5
            ln = ext[i] & 0x1f
            p = ext[i + 1:i + 1 + ln]
            if tag == 3 and len(p) >= 3:
                oui = (p[0] << 16) | (p[1] << 8) | p[2]
                print('      VSDB len=%d OUI=%06x %s' % (ln, oui, hexs(p)))
                if oui == 0x00d046:
                    print('      *** DOLBY VSVDB ***')
            elif tag == 7 and len(p) >= 1:
                print('      EXT tag=0x%02x len=%d %s' % (p[0], ln, hexs(p)))
            else:
                print('      block tag=%d len=%d %s' % (tag, ln, hexs(p)))
            i += 1 + ln
            if ln == 0:
                break
    for sig, name in ((b'\x00\xd0\x46', 'Dolby OUI'), (b'\x00\x0c\x03', 'HDMI OUI')):
        pos = d.find(sig)
        while pos >= 0:
            lo = max(0, pos - 4)
            print('   raw %s @ %d: %s' % (name, pos, hexs(d[lo:pos + 24])))
            pos = d.find(sig, pos + 1)


for p in sys.argv[1:]:
    parse(p)