#!/usr/bin/env python3
"""Decode the Dolby Vision VSVDB from an EDID binary.

Usage:
    python decode_edid.py splitter_edid.bin

Reads the CEA extension, finds the Vendor-Specific Video Data Block with
OUI 00-D0-46 (Dolby), and prints the VSVDB fields. Handles the 7-byte
version 1 and version 2 payloads used by the EZCOO SP12H21 family.
"""
import sys


def pq2nits(code):
    pq = code / 4095.0
    m1 = 2610.0 / 16384.0
    m2 = 128.0 * (2523.0 / 4096.0)
    c1 = 3424.0 / 4096.0
    c2 = 32.0 * (2413.0 / 4096.0)
    c3 = 32.0 * (2392.0 / 4096.0)
    e = pq ** (1.0 / m2)
    v = max(0.0, e - c1) / (c2 - c3 * e)
    return (v ** (1.0 / m1)) * 10000.0


def decode_v2(b):
    labels = ["Low-Latency", "Low-Latency + LLDV-HDMI",
              "Standard + Low-Latency", "Standard + Low-Latency + LLDV-HDMI"]
    minpq = 20 * ((b[1] >> 3) & 0x1F)
    maxpq = 2055 + 65 * ((b[2] >> 3) & 0x1F)
    return {
        'version': (b[0] >> 5) & 7,
        'dm': ((b[0] >> 2) & 7) + 2,
        'yuv12': b[0] & 1,
        'gdim': (b[1] >> 2) & 1,
        'iface': labels[b[2] & 3],
        'minpq': minpq,
        'maxpq': maxpq,
        'minnits': pq2nits(minpq),
        'maxnits': pq2nits(maxpq),
        'rx': 0.625 + (((b[5] >> 3) & 0x1F) / 256.0),
        'ry': 0.25 + (((b[6] >> 3) & 0x1F) / 256.0),
        'gx': ((b[3] >> 1) & 0x7F) / 256.0,
        'gy': 0.5 + (((b[4] >> 1) & 0x7F) / 256.0),
        'bx': 0.125 + ((b[5] & 7) / 256.0),
        'by': 0.03125 + ((b[6] & 7) / 256.0),
    }


def decode_v1(b):
    mn = (b[2] >> 1) / 127.0
    return {
        'version': (b[0] >> 5) & 7,
        'dm': ((b[0] >> 2) & 7) + 2,
        'yuv12': b[0] & 1,
        'p60': b[0] & 2,
        'gdim': b[1] & 1,
        'p3': b[2] & 1,
        'low': b[3] & 1,
        'minnits': mn * mn,
        'maxnits': 100 + (b[1] >> 1) * 50,
    }


def find_dolby(edid):
    if len(edid) < 256:
        return None
    ext = edid[128:256]
    if ext[0] != 0x02:
        return None
    start = ext[2]
    end = start if 4 <= start <= 127 else 127
    i = 4
    while i < end:
        tag = ext[i] >> 5
        ln = ext[i] & 0x1F
        p = ext[i + 1:i + 1 + ln]
        if tag == 7 and ln >= 5 and p[0] == 0x01:
            oui = p[1] | (p[2] << 8) | (p[3] << 16)
            if oui == 0x00D046:
                return p[4:11], p
        if ln == 0:
            break
        i += 1 + ln
    return None


def main(path):
    data = open(path, 'rb').read()
    print('file: %s (%d bytes)' % (path, len(data)))
    if len(data) < 128 or data[:8] != b'\x00\xff\xff\xff\xff\xff\xff\x00':
        print('not an EDID')
        return 1
    found = find_dolby(data)
    if not found:
        print('no Dolby VSVDB (OUI 00-D0-46) found')
        return 1
    payload, full = found
    print('Dolby block: %s' % ' '.join('%02x' % x for x in full))
    print('payload:     %s' % ' '.join('%02x' % x for x in payload))
    version = (payload[0] >> 5) & 7
    if version == 2:
        x = decode_v2(payload)
        print('version:     2')
        print('DM:          %d.x' % x['dm'])
        print('YUV 4:2:2 12-bit: %s' % ('yes' if x['yuv12'] else 'no'))
        print('global dimming:    %s' % ('yes' if x['gdim'] else 'no'))
        print('interface:   %s' % x['iface'])
        print('target min:  PQ %d = %.8f cd/m^2' % (x['minpq'], x['minnits']))
        print('target max:  PQ %d = %.2f cd/m^2' % (x['maxpq'], x['maxnits']))
        print('primaries:   R(%.6f,%.6f) G(%.6f,%.6f) B(%.6f,%.6f)' % (
            x['rx'], x['ry'], x['gx'], x['gy'], x['bx'], x['by']))
    elif version == 1:
        x = decode_v1(payload)
        print('version:     1')
        print('DM:          %d.x' % x['dm'])
        print('YUV 4:2:2 12-bit: %s' % ('yes' if x['yuv12'] else 'no'))
        print('2160p60:     %s' % ('yes' if x['p60'] else 'no'))
        print('colorimetry: %s' % ('P3-D65' if x['p3'] else 'BT.709'))
        print('low latency: %s' % ('yes' if x['low'] else 'no'))
        print('target min:  %.8f cd/m^2' % x['minnits'])
        print('target max:  %.0f cd/m^2' % x['maxnits'])
    else:
        print('version %d not decoded' % version)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))