import sys

SIG = bytes.fromhex('eb0146d000')      # Dolby VSVDB block: eb 01 46 d0 00
HDR = b'\x00\xff\xff\xff\xff\xff\xff\x00'


def main(inp, old_hex, new_hex, outp):
    old = bytes.fromhex(old_hex)
    new = bytes.fromhex(new_hex)
    if len(old) != 7 or len(new) != 7:
        raise SystemExit('payloads must be 7 bytes')
    needle = SIG + old

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
    for idx in range(len(addrs) - len(needle) + 1):
        a = addrs[idx]
        if all(a + k in mem for k in range(len(needle))) and \
           bytes(mem[a + k] for k in range(len(needle))) == needle:
            matches.append(a)

    print('matches:', len(matches))
    for p in matches:
        print('  0x%08x' % p)
        for k in range(7):
            mem[p + 5 + k] = new[k]

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
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])