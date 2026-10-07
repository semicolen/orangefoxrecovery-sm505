#!/usr/bin/env python3
"""Check the built recovery against the stock header, then create an Odin tar."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tarfile
import zipfile

p = argparse.ArgumentParser()
p.add_argument("image", type=Path)
p.add_argument("device_tree", type=Path)
p.add_argument("output", type=Path)
p.add_argument("--name", default="OrangeFox-unofficial-SM-T505")
p.add_argument("--test2", action="store_true")
p.add_argument("--installer", type=Path)
p.add_argument("--expected-version")
p.add_argument("--unlock-button", action="store_true")
p.add_argument("--build-ninja", type=Path)
a = p.parse_args()
d = a.image.read_bytes()
stock = json.loads((a.device_tree / "prebuilt/stock-boot.json").read_text())
assert d[:8] == b"ANDROID!", "Missing Android boot magic"
ks, ka, rs, ra, ss, sa, ta, page, ver, osv = struct.unpack_from("<10I", d, 8)
assert (ver, page, ka, ra, ta) == (2, 4096, stock["kernel_addr"], stock["ramdisk_addr"], stock["tags_addr"]), "Boot header does not match stock"
board = d[48:64].split(b"\0")[0].decode()
assert board == stock["board"], f"Wrong board: {board}"
rdtos, rdtoo, hs = struct.unpack_from("<IQI", d, 1632)
ds, da = struct.unpack_from("<IQ", d, 1648)
assert da == stock["dtb_addr"], "Wrong DTB load address"
align = lambda n: (n + page - 1) // page * page
dto = page + align(ks) + align(rs) + align(ss) + align(rdtos)
for name, data in (("Image.gz", d[page:page + ks]), ("dtb.img", d[dto:dto + ds]), ("recovery-dtbo.img", d[rdtoo:rdtoo + rdtos])):
    assert data == (a.device_tree / "prebuilt" / name).read_bytes(), f"{name} differs from stock"
assert len(d) <= 103546880, "Image exceeds recovery partition"
ro = page + align(ks)
ramdisk = gzip.decompress(d[ro:ro + rs])
files = {}
pos = 0
while pos + 110 <= len(ramdisk):
    hdr = ramdisk[pos:pos + 110]
    assert hdr[:6] in (b"070701", b"070702"), "Invalid CPIO header"
    fields = [int(hdr[6 + n * 8:14 + n * 8], 16) for n in range(13)]
    size, namesize = fields[6], fields[11]
    name = ramdisk[pos + 110:pos + 110 + namesize - 1].decode().lstrip("./")
    start = (pos + 110 + namesize + 3) & ~3
    assert start + size <= len(ramdisk), "Truncated CPIO record"
    if name == "TRAILER!!!":
        break
    files[name] = ramdisk[start:start + size]
    pos = (start + size + 3) & ~3
fstab = files.get("system/etc/recovery.fstab", b"")
assert fstab, "Missing fstab"
assert b"/external_sd auto" in fstab and b"/usb_otg auto" in fstab, "Missing removable storage entries"
assert "init.recovery.usb.rc" in files, "Missing USB init"
for service in ("qseecomd", "android.hardware.keymaster@4.0-service", "android.hardware.gatekeeper@1.0-service"):
    binary = files.get("system/bin/" + service, b"")
    assert binary[:4] == b"\x7fELF", f"Missing crypto service: {service}"
assert b"OrangeFox" in ramdisk or b"orangefox" in ramdisk, "Missing OrangeFox content"
assert b"SEANDROIDENFORCE" in d[-4096:], "Missing Samsung footer"
if a.test2 or a.expected_version:
    assert "vendor/etc/vintf/manifest/gta4l-crypto.xml" in files, "Missing crypto manifest"
    assert "system/bin/gta4l-startup-log.sh" in files, "Missing startup diagnostics"
    assert b"start gta4l-startup-log" in files["init.recovery.qcom.rc"], "Startup diagnostics not enabled"
    expected_version = a.expected_version or "R12.0_2"
    assert expected_version.encode() in files["system/bin/recovery"], "Wrong build version"
    assert b"FBE decryption disabled for this build" in files["system/bin/recovery"], "Missing skipped-decryption state guard"
if a.unlock_button:
    assert a.build_ninja, "Pass --build-ninja to verify compiled unlock-button defaults"
    with a.build_ninja.open() as ninja:
        compiled_flags = next((line for line in ninja if "-DOF_USE_LOCKSCREEN_BUTTON" in line
                               and "-DOF_SKIP_FBE_DECRYPTION=" in line), None)
    assert compiled_flags, "Missing unlock-button or FBE-skip compiler flag"
a.output.mkdir(parents=True, exist_ok=True)
image = a.output / (a.name + ".img")
shutil.copyfile(a.image, image)
archive = a.output / (a.name + ".tar")
with tarfile.open(archive, "w", format=tarfile.USTAR_FORMAT) as tar:
    info = tarfile.TarInfo("recovery.img")
    info.size = image.stat().st_size
    info.mode = 0o644
    info.mtime = 0
    with image.open("rb") as f:
        tar.addfile(info, f)
with tarfile.open(archive, "r") as tar:
    assert tar.getnames() == ["recovery.img"], "Unexpected Odin tar contents"
    assert tar.extractfile("recovery.img").read() == d, "Odin image does not match"
artifacts = [image, archive]
if a.installer:
    with zipfile.ZipFile(a.installer) as installer:
        assert installer.testzip() is None, "Installer ZIP CRC failure"
        assert installer.read("recovery.img") == d, "Installer image does not match"
    installer_copy = a.output / (a.name + ".zip")
    shutil.copyfile(a.installer, installer_copy)
    artifacts.append(installer_copy)
report = {"image_bytes": len(d), "partition_bytes": 103546880, "header_version": ver,
          "board": board, "stock_kernel_version": stock["kernel_version"],
          "hardware_tested": False, "decryption_tested": False,
          "files": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in artifacts}}
if a.installer:
    report["installer_crc_valid"] = True
    report["installer_embedded_image_matches"] = True
if a.test2 or a.expected_version:
    report.update({"build": a.expected_version or "TEST2", "fbe_decryption_skipped": True,
                   "startup_logs": ["/tmp/recovery.log", "/tmp/gta4l-startup.log", "/tmp/logcat.log", "/tmp/kernel.log"]})
if a.unlock_button:
    report["unlock_button_default"] = True
    report["compiled_unlock_and_fbe_skip_flags_verified"] = True
(a.output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
(a.output / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in report["files"].items()))
print(json.dumps(report, indent=2))
