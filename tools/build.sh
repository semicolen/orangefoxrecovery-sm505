#!/usr/bin/env bash
set -o pipefail
WORKSPACE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_ROOT="${BUILD_ROOT:-$HOME/orangefox-gta4l}"
export PATH="$HOME/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export LC_ALL=C
export ALLOW_MISSING_DEPENDENCIES=true
export GOGC=20
export GOMAXPROCS=2
export FOX_BUILD_DEVICE=gta4l
mkdir -p "$BUILD_ROOT/device/samsung/gta4l" "$WORKSPACE/logs"
rsync -a --delete --exclude=.git "$WORKSPACE/device/samsung/gta4l/" "$BUILD_ROOT/device/samsung/gta4l/" || exit $?
python3 - "$BUILD_ROOT/device/samsung/gta4l" <<'PY'
from pathlib import Path
import sys
for path in Path(sys.argv[1]).rglob('*'):
    if path.is_file() and path.suffix in ('.mk', '.rc', '.sh', '.prop', '.fstab'):
        before = path.read_bytes()
        after = before.replace(b'\r\n', b'\n')
        if before != after:
            path.write_bytes(after)
PY
if [ $? -ne 0 ]; then exit 1; fi
cd "$BUILD_ROOT"
python3 "$WORKSPACE/tools/skip_fbe_patch.py" "$BUILD_ROOT" || exit $?
source device/samsung/gta4l/vendorsetup.sh
source build/envsetup.sh
lunch twrp_gta4l-eng || exit $?
mka -j"${BUILD_JOBS:-2}" adbd recoveryimage
