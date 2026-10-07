# OrangeFox for Samsung Galaxy Tab A7 LTE SM-T505

Unofficial OrangeFox **R12.0_3** for `gta4l`, using the matching Samsung
Android 12 `T505XXS8CXG1` stock recovery kernel, DTB and recovery DTBO.

[Recovery releases](https://github.com/semicolen/orangefoxrecovery-sm505/releases)
include an Odin tar, raw recovery image, native OrangeFox installer ZIP,
SHA-256 checksums and a verification report. See [release notes](RELEASE_NOTES.md)
and [source provenance](NOTICE.md).

## Changes and validation

The inactivity lock screen uses an **Unlock button by default**. The tablet
owner confirmed the equivalent live setting works in TEST2. Previously saved
preferences can override the default.

Automatic file-based data decryption is disabled to avoid the startup hang.
Encrypted internal storage is unavailable. The included source patch keeps
skipped FBE data marked locked and prevents subsequent decryption attempts.

| Check | Result |
| --- | --- |
| Main UI, ADB and basic touch | Confirmed on TEST2 / R12.0_2 |
| Inactivity swipe unlock | Failed on the tablet |
| Unlock button | User-confirmed working in TEST2; enabled by default in R12.0_3 |
| R12.0_3 boot on the tablet | Not yet tested |
| Stock encrypted-data decryption | Disabled |
| Backup/restore and other recovery operations | Not validated |

Static checks verify the stock kernel/DTB/DTBO bytes, Android v2 boot header,
load addresses, Samsung footer and recovery partition size. Packaging verifies
that the Odin tar and installer ZIP contain the same image. Crypto dependency
checks cover required ARM64 ELF files; they do not prove Samsung decryption works.

No unlock, format, bootloader flash or vbmeta replacement is performed by these
build scripts. No other Tab A7 model has been validated.

## Build

Use a Linux host or WSL and prepare the official OrangeFox `fox_12.1` /
minimal `twrp-12.1` sources using the
[official build guide](https://wiki.orangefox.tech/dev/building) and
[sync project](https://gitlab.com/OrangeFox/sync). Source revisions used for
this build are recorded in [source-revisions.json](source-revisions.json).

Clone this project separately from the Android checkout. From this project's
root, set the location of that checkout and run:

```bash
export BUILD_ROOT="$HOME/orangefox-gta4l"
BUILD_JOBS=4 bash tools/build.sh
```

The script copies the device tree into `device/samsung/gta4l`, applies the
idempotent FBE skip-state patch, selects `twrp_gta4l-eng` and builds
`adbd recoveryimage`. Outputs are in
`$BUILD_ROOT/out/target/product/gta4l`. The default job count is 2.

On a host with limited RAM, apply the optional Blueprint graph-generator patch
before building:

```bash
python3 tools/low_memory_build.py "$BUILD_ROOT"
```

The patch limits graph-generation garbage collection and concurrency; it does
not change recovery code. The official sync patches must also be applied.
The local build required the sync project's
`patches/patch-vendor-twrp-fox_12.1.diff` patch in `vendor/twrp` because
the sync script initially skipped it.

## Package and inspect

After a successful build:

```bash
python3 tools/verify_runtime.py "$BUILD_ROOT/out/target/product/gta4l/recovery/root"
python3 tools/package.py \
  "$BUILD_ROOT/out/target/product/gta4l/recovery.img" \
  device/samsung/gta4l out/R12.0_3 \
  --name OrangeFox-R12.0_3-SM-T505 \
  --expected-version R12.0_3 --unlock-button \
  --build-ninja "$BUILD_ROOT/out/build-twrp_gta4l.ninja" \
  --installer "$BUILD_ROOT/out/target/product/gta4l/OrangeFox-R12.0_3_SM-T505-Unofficial-gta4l.zip"
```

The Odin archive contains only `recovery.img`. Installing the ZIP requires an
already working compatible recovery. Formatting data is not needed for the
unlock-button change.

`tools/collect-recovery-logs.ps1` collects recovery logs through ADB on Windows.
Startup snapshots, logcat and kernel logs are stored in RAM under `/tmp` and
must be collected before rebooting. Logs, settings backups, full stock firmware,
Android source checkouts and build outputs are excluded from Git.

## History

The initial build reached the OrangeFox splash but not the UI. TEST2 skipped
FBE startup and added crypto HAL declarations and RAM diagnostics. On
7 October 2026, TEST2 reached the UI and its ADB version was verified. Swipe
unlock failed; enabling `lock_btn=1` showed a working Unlock button. That
preference was saved on the tablet. R12.0_3 embeds the same option as the
default for new installations.
