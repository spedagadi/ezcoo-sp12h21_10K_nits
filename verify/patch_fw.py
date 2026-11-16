import sys

SIG = bytes.fromhex('eb0146d000450b908660768f')
HDR = b'\x00\xff\xff\xff\xff\xff\xff\x00'
NEW_MAX_BYTE = 0xF8  # max lum index 31 -> PQ 4070 -> 9434 nits


def main(inp, outp):
    with open(inp, 'r', newline='', errors='ignore') as f:
        raw_text = f.read()
    crlf = '\r\n' in raw_text
    lines = raw_text.replace('\r\n', '\n').split('\n')

    recs = []
    base = 0
    for i, line in enumerate(lines):
        if not line.startswith(':'):
            continue
        raw = bytes.fromhex(line[1:])
        n = raw[0]
        addr = (raw[1] << 8) | raw[2]
        typ = raw[3]
        if typ == 0:
            recs.append((i, base + addr, n))
        elif typ == 2:
            base = ((raw[4] << 8) | raw[5]) << 4
        elif typ == 4:
            base = ((raw[4] << 8) | raw[5]) << 16

    mem = {}
    for (i, a, n) in recs:
        raw = bytes.fromhex(lines[i][1:])
        for k in range(n):
            mem[a + k] = raw[4 + k]

    addrs = sorted(mem)
    matches = []
    for idx in range(len(addrs) - len(SIG) + 1):
        a = addrs[idx]
        if all(a + k in mem for k in range(len(SIG))) and \
           bytes(mem[a + k] for k in range(len(SIG))) == SIG:
            matches.append(a)

    print('VSVDB occurrences:', len(matches))
    for p in matches:
        print('  0x%08x' % p)
        mem[p + 7] = NEW_MAX_BYTE

    for p in matches:
        hdr = None
        for h in range(p - 255, p - 127):
            if all(h + k in mem for k in range(8)) and \
               bytes(mem[h + k] for k in range(8)) == HDR:
                hdr = h
        if hdr is not None and hdr + 128 <= p < hdr + 255:
            s = sum(mem[hdr + 128 + k] for k in range(127)) & 0xff
            mem[hdr + 255] = (0x100 - s) & 0xff
            print('  EDID @0x%08x ext checksum -> 0x%02x' % (hdr, mem[hdr + 255]))
        else:
            print('  no EDID checksum for 0x%08x (template/string)' % p)

    for (i, a, n) in recs:
        raw = bytearray(bytes.fromhex(lines[i][1:]))
        for k in range(n):
            raw[4 + k] = mem[a + k]
        raw[-1] = (0x100 - (sum(raw[:-1]) & 0xff)) & 0xff
        lines[i] = ':' + raw.hex().upper()

    eol = '\r\n' if crlf else '\n'
    with open(outp, 'w', newline='') as f:
        f.write(eol.join(lines))
    print('wrote', outp)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])