#!/usr/bin/env python3
"""Extract and record a Samsung v2 boot image without modifying the input."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct

p = argparse.ArgumentParser()
p.add_argument("image", type=Path)
p.add_argument("output", type=Path)
a = p.parse_args()
d = a.image.read_bytes()
if d[:8] != b"ANDROID!":
    raise SystemExit("Not an Android boot image")
ks, ka, rs, ra, ss, sa, ta, page, ver, osv = struct.unpack_from("<10I", d, 8)
if ver != 2 or page != 4096:
    raise SystemExit(f"Expected header v2, page 4096; got {ver}, {page}")
align = lambda n: (n + page - 1) // page * page
rdtos, rdtoo, hs = struct.unpack_from("<IQI", d, 1632)
ds, da = struct.unpack_from("<IQ", d, 1648)
ko = page
dto = ko + align(ks) + align(rs) + align(ss) + align(rdtos)
kernel = d[ko:ko + ks]
dtb = d[dto:dto + ds]
if len(kernel) != ks or len(dtb) != ds or dtb[:4] != b"\xd0\x0d\xfe\xed":
    raise SystemExit("Invalid kernel or DTB bounds/magic")
raw = gzip.decompress(kernel) if kernel[:2] == b"\x1f\x8b" else kernel
pos = raw.find(b"Linux version ")
version = raw[pos:raw.find(b"\0", pos)].decode(errors="replace") if pos >= 0 else "unknown"
a.output.mkdir(parents=True, exist_ok=True)
(a.output / "Image.gz").write_bytes(kernel)
(a.output / "dtb.img").write_bytes(dtb)
if rdtos:
    recovery_dtbo = d[rdtoo:rdtoo + rdtos]
    if len(recovery_dtbo) != rdtos or recovery_dtbo[:4] != b"\xd7\xb7\xab\x1e":
        raise SystemExit("Invalid recovery DTBO bounds/magic")
    (a.output / "recovery-dtbo.img").write_bytes(recovery_dtbo)
info = dict(source=a.image.name, sha256=hashlib.sha256(d).hexdigest(),
            header_version=ver, page_size=page, kernel_size=ks, ramdisk_size=rs,
            recovery_dtbo_size=rdtos, dtb_size=ds, kernel_addr=ka,
            ramdisk_addr=ra, tags_addr=ta, dtb_addr=da,
            board=d[48:64].split(b"\0")[0].decode(), kernel_version=version,
            cmdline=(d[64:576] + d[608:1632]).split(b"\0")[0].decode())
(a.output / "stock-boot.json").write_text(json.dumps(info, indent=2) + "\n")
print(json.dumps(info, indent=2))
