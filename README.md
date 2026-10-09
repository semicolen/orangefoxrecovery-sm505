# OrangeFox for Samsung Galaxy Tab A7 LTE SM-T505

Unofficial OrangeFox **R12.0_3** for `gta4l`, using the matching Samsung
Android 12 `T505XXS8CXG1` stock recovery kernel, DTB and recovery DTBO.

[Recovery releases](https://github.com/semicolen/orangefoxrecovery-sm505/releases)
include an Odin tar, raw recovery image, native OrangeFox installer ZIP,
SHA-256 checksums and a verification report. See [release notes](RELEASE_NOTES.md)
and [source provenance](NOTICE.md).

## Installation
To install, first flash the included `vbmeta_disabled_R.tar` under the AP slot in the latest version of Odin. Reboot directly back into Download Mode, then flash `OrangeFox-R12.0_3-SM-T505.tar` under AP with Auto Reboot disabled in Odin. Once the flash is complete, manually reboot the device into recovery by holding `Down button`, `Power button` for 7s. 

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
