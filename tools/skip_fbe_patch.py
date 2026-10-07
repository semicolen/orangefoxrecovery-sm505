#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Preserve encrypted-data state when OrangeFox skips FBE decryption.

The upstream OF_SKIP_FBE_DECRYPTION branch returns before correcting the state
set by Set_FBE_Status(). That leaves userdata marked decrypted and can cause
startup to recreate its media directory. Correct that state and prevent later
automatic, metadata, and explicit FBE decryption attempts while the skip
property is active. Unencrypted data and ordinary builds retain their behavior.

Usage: python3 tools/skip_fbe_patch.py /path/to/orangefox-source

All three replacements are checked before any file is changed. Each replacement
must match the expected upstream source or the exact already-patched source;
unexpected or partially modified snippets cause an error. Repeated runs are
safe and make no further changes.
"""

import argparse
from pathlib import Path
import sys


SKIP_OLD = '''\tif (TWFunc::Fox_Property_Get("of_skip_fbe_decryption") == "true") {
\t\tgui_print_color("warning", "Skip FBE decryption is triggered. I will not try to decrypt...\\n");
\t\treturn false;
\t}'''

SKIP_NEW = '''\tif (TWFunc::Fox_Property_Get("of_skip_fbe_decryption") == "true") {
\t\t// Keep skipped FBE data locked and avoid recreating its media directory.
\t\tIs_FBE = true;
\t\tIs_Encrypted = true;
\t\tIs_Decrypted = false;
\t\tDataManager::SetValue(TW_IS_DECRYPTED, 0);
\t\tDataManager::SetValue(TW_IS_ENCRYPTED, 1);
\t\tDataManager::SetValue(FOX_ENCRYPTED_DEVICE, "1");
\t\tDataManager::SetValue(TW_CRYPTO_PWTYPE, 0);
\t\tgui_print_color("warning", "Skip FBE decryption is triggered. I will not try to decrypt...\\n");
\t\treturn false;
\t}'''

AUTO_OLD = '''void TWPartitionManager::Decrypt_Data() {
\t#ifdef TW_INCLUDE_CRYPTO
\tTWPartition* Decrypt_Data = Find_Partition_By_Path("/data");
\tif (Decrypt_Data && Decrypt_Data->Is_Encrypted && !Decrypt_Data->Is_Decrypted) {'''

AUTO_NEW = '''void TWPartitionManager::Decrypt_Data() {
\t#ifdef TW_INCLUDE_CRYPTO
\tTWPartition* Decrypt_Data = Find_Partition_By_Path("/data");
\t// Skip metadata and default-password attempts when FBE is deliberately locked.
\tif (TWFunc::Fox_Property_Get("of_skip_fbe_decryption") == "true" &&
\t\tDecrypt_Data && (Decrypt_Data->Is_FBE || !Decrypt_Data->Key_Directory.empty())) {
\t\tLOGINFO("FBE decryption disabled for this build: skipping automatic FBE and metadata decryption\\n");
\t\treturn;
\t}
\tif (Decrypt_Data && Decrypt_Data->Is_Encrypted && !Decrypt_Data->Is_Decrypted) {'''

DEVICE_OLD = '''int TWPartitionManager::Decrypt_Device(string Password, int user_id) {
#ifdef TW_INCLUDE_CRYPTO
  char crypto_blkdev[PROPERTY_VALUE_MAX];'''

DEVICE_NEW = '''int TWPartitionManager::Decrypt_Device(string Password, int user_id) {
#ifdef TW_INCLUDE_CRYPTO
  // Explicit FBE requests must also respect the build's skip-decryption policy.
  if (TWFunc::Fox_Property_Get("of_skip_fbe_decryption") == "true" &&
      DataManager::GetIntValue(TW_IS_FBE)) {
    LOGINFO("Skipping explicit FBE decryption\\n");
    return -1;
  }
  char crypto_blkdev[PROPERTY_VALUE_MAX];'''


def replace_exact(source: str, old: str, new: str, label: str) -> tuple[str, bool]:
    old_count = source.count(old)
    new_count = source.count(new)
    if old_count == 1 and new_count == 0:
        return source.replace(old, new, 1), True
    if old_count == 0 and new_count == 1:
        return source, False
    raise ValueError(
        f"Source mismatch for {label}: expected one upstream or one patched "
        f"snippet, found {old_count} upstream and {new_count} patched."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_root", type=Path, help="OrangeFox source checkout")
    args = parser.parse_args()
    recovery = args.build_root.resolve() / "bootable" / "recovery"
    replacements = {
        recovery / "partition.cpp": [(SKIP_OLD, SKIP_NEW, "FBE skip state")],
        recovery / "partitionmanager.cpp": [
            (AUTO_OLD, AUTO_NEW, "automatic FBE decryption guard"),
            (DEVICE_OLD, DEVICE_NEW, "explicit FBE decryption guard"),
        ],
    }

    prepared = []
    try:
        for path, edits in replacements.items():
            original = path.read_bytes()
            source = original.decode("utf-8")
            changed = False
            for old, new, label in edits:
                source, edit_changed = replace_exact(source, old, new, label)
                changed = changed or edit_changed
            prepared.append((path, original, source.encode("utf-8"), changed))

        # Ensure preflight did not race with another writer before applying edits.
        for path, original, _, _ in prepared:
            if path.read_bytes() != original:
                raise ValueError(f"Source changed during preflight: {path}")
        for path, _, patched, changed in prepared:
            if changed:
                path.write_bytes(patched)
                print(f"Patched {path}")
            else:
                print(f"Already patched {path}")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"FBE skip patch failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
