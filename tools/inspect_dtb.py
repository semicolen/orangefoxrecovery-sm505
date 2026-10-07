#!/usr/bin/env python3
from pathlib import Path
import struct
import sys

d = Path(sys.argv[1]).read_bytes()
i = 0
while i < len(d):
    header = struct.unpack_from(">10I", d, i)
    assert header[0] == 0xD00DFEED
    total, st, strings = header[1], header[2], header[3]
    dt = d[i:i + total]
    j = st
    while j < st + header[9]:
        token = struct.unpack_from(">I", dt, j)[0]
        j += 4
        if token == 1:
            j = (dt.index(0, j) + 4) & ~3
        elif token == 3:
            size, no = struct.unpack_from(">II", dt, j)
            j += 8
            pos = strings + no
            name = dt[pos:dt.index(0, pos)].decode()
            if any(s in name for s in ("bl-max", "brightness-max", "brightness-default")):
                print(i, name, dt[j:j + size].hex())
            j = (j + size + 3) & ~3
        elif token == 9:
            break
        elif token not in (2, 4):
            raise ValueError(f"Bad FDT token {token} at {j}")
    i += total
