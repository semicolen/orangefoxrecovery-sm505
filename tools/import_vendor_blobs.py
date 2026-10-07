#!/usr/bin/env python3
"""Import recovery crypto services and their vendor-only ELF dependencies."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import json

p = argparse.ArgumentParser()
p.add_argument("vendor", type=Path)
p.add_argument("device_tree", type=Path)
a = p.parse_args()
root = a.device_tree / "recovery/root"
pending = ["bin/qseecomd", "bin/hw/android.hardware.keymaster@4.0-service",
           "bin/hw/android.hardware.gatekeeper@1.0-service"]
done = set()
external = set()
while pending:
    rel = pending.pop()
    if rel in done:
        continue
    source = a.vendor / rel
    if not source.is_file():
        raise SystemExit(f"Missing stock binary: {rel}")
    dest = (root / "system/bin" / source.name) if rel.startswith("bin/") else (root / "vendor" / rel)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    if rel.startswith("bin/"):
        dest.chmod(0o755)
    done.add(rel)
    elf = subprocess.run(["readelf", "-d", str(source)], check=True, text=True, capture_output=True).stdout
    for name in re.findall(r"\(NEEDED\).*?\[(.*?)\]", elf):
        found = next((f"{lib}/{name}" for lib in ("lib64", "lib64/hw") if (a.vendor / lib / name).is_file()), None)
        if found:
            pending.append(found)
        else:
            external.add(name)
report = {"stock_vendor_files": sorted(done), "system_dependencies": sorted(external)}
(a.device_tree / "prebuilt/vendor-blobs.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
