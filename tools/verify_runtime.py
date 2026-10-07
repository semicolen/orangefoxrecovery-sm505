#!/usr/bin/env python3
"""Check ARM64 crypto-service ELF dependencies in the assembled ramdisk."""
import argparse
import json
from pathlib import Path
import re
import subprocess

p = argparse.ArgumentParser()
p.add_argument("root", type=Path)
a = p.parse_args()
dirs = [a.root / d for d in ("vendor/lib64", "vendor/lib64/hw", "system/lib64", "system/lib64/bootstrap")]
pending = [a.root / "system/bin" / n for n in
           ("qseecomd", "android.hardware.keymaster@4.0-service", "android.hardware.gatekeeper@1.0-service")]
checked = set()
missing = set()
while pending:
    binary = pending.pop()
    if binary in checked:
        continue
    if not binary.is_file():
        missing.add(str(binary.relative_to(a.root)))
        continue
    checked.add(binary)
    hdr = binary.read_bytes()[:20]
    if hdr[:4] != b"\x7fELF" or hdr[4] != 2 or int.from_bytes(hdr[18:20], "little") != 183:
        raise SystemExit(f"Not an ARM64 ELF: {binary}")
    result = subprocess.run(["readelf", "-d", str(binary)], check=True, text=True, capture_output=True)
    for name in re.findall(r"\(NEEDED\).*?\[(.*?)\]", result.stdout):
        dependency = next((d / name for d in dirs if (d / name).is_file()), None)
        if dependency:
            pending.append(dependency)
        else:
            missing.add(name)
report = {"checked_elf_files": len(checked), "missing": sorted(missing)}
print(json.dumps(report, indent=2))
if missing:
    raise SystemExit(1)
