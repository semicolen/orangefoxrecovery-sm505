#!/usr/bin/env python3
"""Convert Android sparse super and extract its vendor logical partition."""
from pathlib import Path
import argparse
import struct

p = argparse.ArgumentParser()
p.add_argument("super_image", type=Path)
p.add_argument("output", type=Path)
a = p.parse_args()
raw_path = a.output / "super.raw.img"
a.output.mkdir(parents=True, exist_ok=True)
with a.super_image.open("rb") as src, raw_path.open("wb") as dst:
    hdr = src.read(28)
    magic, major, minor, fh, ch, block, blocks, chunks, checksum = struct.unpack("<IHHHHIIII", hdr)
    if magic != 0xED26FF3A or major != 1:
        raise SystemExit("Expected Android sparse image")
    src.seek(fh)
    for _ in range(chunks):
        typ, reserved, nblocks, total = struct.unpack("<HHII", src.read(12))
        src.seek(ch - 12, 1)
        size = nblocks * block
        if typ == 0xCAC1:
            if total != ch + size:
                raise SystemExit("Bad raw chunk length")
            left = size
            while left:
                data = src.read(min(left, 4 * 1024 * 1024))
                if not data:
                    raise SystemExit("Truncated sparse image")
                dst.write(data)
                left -= len(data)
        elif typ == 0xCAC2:
            pattern = src.read(4)
            if pattern == b"\0" * 4:
                dst.seek(size, 1)
            else:
                chunk = pattern * (1024 * 1024)
                while size:
                    n = min(size, len(chunk))
                    dst.write(chunk[:n])
                    size -= n
        elif typ == 0xCAC3:
            dst.seek(size, 1)
        elif typ == 0xCAC4:
            src.read(4)
        else:
            raise SystemExit(f"Unknown sparse chunk {typ:x}")
    dst.truncate(blocks * block)
with raw_path.open("rb") as src:
    src.seek(12288)
    hdr = src.read(128)
    magic, major, minor, header_size = struct.unpack_from("<IHHI", hdr)
    if magic != 0x414C5030 or major != 10:
        raise SystemExit("Invalid logical partition metadata")
    tables_size = struct.unpack_from("<I", hdr, 44)[0]
    src.seek(12288 + header_size)
    tables = src.read(tables_size)
    po, pn, ps = struct.unpack_from("<III", hdr, 80)
    eo, en, es = struct.unpack_from("<III", hdr, 92)
    for idx in range(pn):
        record = tables[po + idx * ps:po + (idx + 1) * ps]
        name = record[:36].split(b"\0")[0].decode()
        if name not in ("vendor", "vendor_a"):
            continue
        attrs, first, count, group = struct.unpack_from("<IIII", record, 36)
        with (a.output / "vendor.img").open("wb") as dst:
            for ext in range(first, first + count):
                sectors, typ, sector, source = struct.unpack_from("<QIQI", tables, eo + ext * es)
                if typ != 0 or source != 0:
                    raise SystemExit("Expected linear extent on super")
                src.seek(sector * 512)
                left = sectors * 512
                while left:
                    data = src.read(min(left, 4 * 1024 * 1024))
                    if not data:
                        raise SystemExit("Truncated extent")
                    dst.write(data)
                    left -= len(data)
        print(a.output / "vendor.img")
        break
    else:
        raise SystemExit("No vendor partition found")
