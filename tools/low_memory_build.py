#!/usr/bin/env python3
"""Keep the local Blueprint graph generator within this workstation's RAM."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
patches = {
    "build/blueprint/bootstrap/bootstrap.go": ("env -i \"$$BUILDER\"", "env -i GOGC=20 \"$$BUILDER\""),
    "build/blueprint/bootstrap/command.go": ("runtime.GOMAXPROCS(runtime.NumCPU())", "runtime.GOMAXPROCS(2)"),
}
for rel, (old, new) in patches.items():
    p = root / rel
    text = p.read_text()
    if new in text:
        continue
    assert old in text, f"Upstream changed: {rel}"
    p.write_text(text.replace(old, new))
    print(f"Patched {rel}")
