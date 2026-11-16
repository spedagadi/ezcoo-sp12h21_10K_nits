import sys


def parse_ihex(path):
    mem = {}
    base = 0
    with open(path, 'r', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line.startswith(':'):
                continue
            raw = bytes.fromhex(line[1:])
            n = raw[0]
            addr = (raw[1] << 8) | raw[2]
            typ = raw[3]
            data = raw[4:4 + n]
            if typ == 0:
                for i, b in enumerate(data):
                    mem[base + addr + i] = b
            elif typ == 2:
                base = ((data[0] << 8) | data[1]) << 4
            elif typ == 4:
                base = ((data[0] << 8) | data[1]) << 16
    return mem


def pq2nits(code):
    pq = code / 4095.0
    m1 = 2610 / 16384
    m2 = 128 * (2523 / 4096)
    c1 = 3424 / 4096
    c2 = 32 * (2413 / 4096)
    c3 = 32 * (2392 / 4096)
    e = pq ** (1 / m2)
    v = max(0.0, e - c1) / (c2 - c3 * e)
    return (v ** (1 / m1)) * 10000.0


def decode_v2(b):
    labels = ["Low-Latency", "Low-Latency + LLDV-HDMI",
              "Standard + Low-Latency", "Standard + Low-Latency + LLDV-HDMI"]
    return {
        'ver': (b[0] >> 5) & 7,
        'dm': ((b[0] >> 2) & 7) + 2,
        'yuv12': b[0] & 1,
        'gdim': (b[1] >> 2) & 1,
        'minpq': 20 * ((b[1] >> 3) & 0x1f),
        'maxpq': 2055 + 65 * ((b[2] >> 3) & 0x1f),
        'iface': labels[b[2] & 3],
    }


def main(path):
    mem = parse_ihex(path)
    if not mem:
        print('no data')
        return
    lo, hi = min(mem), max(mem)
    blob = bytearray(hi - lo + 1)
    for a, b in mem.items():
        blob[a - lo] = b
    print('firmware span 0x%08x..0x%08x (%d bytes, %d mapped)' % (lo, hi, len(blob), len(mem)))
    hdr = b'\x00\xff\xff\xff\xff\xff\xff\x00'
    pos = blob.find(hdr)
    n = 0
    while pos >= 0:
        block = bytes(blob[pos:pos + 256])
        n += 1
        print('\nEDID #%d @ 0x%08x' % (n, lo + pos))
        if len(block) >= 128:
            print('  mfg=%s product=%s ext=%d base_cs=%s' % (
                block[8:10].hex(), block[10:12].hex(), block[126],
                'ok' if (sum(block[:128]) & 0xff) == 0 else 'BAD'))
        if len(block) >= 256:
            print('  cea_cs=%s' % ('ok' if (sum(block[128:256]) & 0xff) == 0 else 'BAD'))
        for sig, name in ((b'\x01\x46\xd0\x00', 'Dolby'), (b'\x03\x0c\x00', 'HDMI')):
            p = block.find(sig)
            if p >= 0:
                print('  %s @ +%d: %s' % (name, p, block[p - 1:p + 16].hex(' ')))
                if name == 'Dolby':
                    payload = block[p + 4:p + 11]
                    if len(payload) == 7:
                        d = decode_v2(payload)
                        print('    v%d dm%d.x yuv12=%d iface=%s' % (
                            d['ver'], d['dm'], d['yuv12'], d['iface']))
                        print('    min PQ %d = %.8f nits' % (d['minpq'], pq2nits(d['minpq'])))
                        print('    max PQ %d = %.2f nits' % (d['maxpq'], pq2nits(d['maxpq'])))
        pos = blob.find(hdr, pos + 1)
    print('\n%d EDID block(s)' % n)


if __name__ == '__main__':
    main(sys.argv[1])