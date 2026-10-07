# Source and prebuilt provenance

- The device configuration started from
  [SeifHossam17's Android 12.1 gta4l tree](https://github.com/SeifHossam17/twrp_device_samsung_gta4l-android-12.1)
  at the revision recorded in `source-revisions.json`. Existing Apache 2.0
  copyright and license notices are retained in the configuration files.
- OrangeFox recovery and vendor sources come from the official
  [OrangeFox sync project](https://gitlab.com/OrangeFox/sync), using `fox_12.1`
  with the minimal `twrp-12.1` manifest. They are fetched separately and are
  not included in this repository. Follow their respective upstream licenses.
- `tools/skip_fbe_patch.py` embeds and modifies OrangeFox C++ source snippets;
  it is marked GPL-3.0-or-later, matching their upstream notice.
- Kernel, DTB, recovery DTBO and Samsung crypto prebuilts were extracted from
  matching `T505XXS8CXG1` firmware. Firmware payloads originally in the base
  device tree remain present. These binary files retain their original
  ownership and licensing; configuration-file notices are not a blanket
  license for the prebuilts.
- `prebuilt/stock-boot.json` and `prebuilt/vendor-blobs.json` in the device tree
  record the stock component metadata and imported vendor dependency list.

Source revisions and local patches are documented alongside the build scripts.
Device logs, settings backups, full stock firmware and build outputs are excluded
from Git. Recovery packages are intended to be distributed as release assets.
