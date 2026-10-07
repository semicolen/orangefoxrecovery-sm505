# OrangeFox R12.0_3 for SM-T505 (gta4l)

Unofficial recovery targeting Samsung Android 12 firmware `T505XXS8CXG1`.

The inactivity lock screen uses an Unlock button by default. The button was
confirmed working on the tablet through the equivalent live preference in
TEST2; new installations no longer need that preference changed through ADB.
Existing saved preferences can override build defaults.

Automatic file-based data decryption remains disabled to avoid the startup
hang. The local skip-path patch keeps encrypted data marked locked and prevents
later automatic or explicit FBE attempts. Encrypted internal storage is not
supported by this release.

TEST2 reached the main recovery UI; ADB, basic touch, and button unlock were
confirmed. Backup/restore and other recovery operations have not been validated.
R12.0_3 requires a separate boot test before it can be considered hardware tested.

The release bundle contains an Odin tar, raw recovery image, native OrangeFox
installer ZIP, `SHA256SUMS`, and a static verification report. The tar contains
only `recovery.img`. No bootloader or vbmeta replacement is included. Installing
the native ZIP requires an already working compatible recovery.
