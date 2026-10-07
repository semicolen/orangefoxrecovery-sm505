#!/bin/bash
# OrangeFox configuration for the Galaxy Tab A7 LTE (SM-T505).
export FOX_BUILD_DEVICE=gta4l
export FOX_VARIANT=SM-T505
export FOX_MAINTAINER_PATCH_VERSION=3
export OF_MAINTAINER=LocalBuild
export OF_DISABLE_MIUI_SPECIFIC_FEATURES=1
export FOX_USE_SAMSUNG_SPECIAL=1
export OF_FORCE_PREBUILT_KERNEL=1
export OF_DEFAULT_KEYMASTER_VERSION=4.0
# Bring up the UI without waiting for unverified Samsung FBE services.
export OF_SKIP_FBE_DECRYPTION=1
# Use the unlock method confirmed working on this tablet.
export OF_USE_LOCKSCREEN_BUTTON=1
export OF_NO_SPLASH_CHANGE=1
export OF_SCREEN_H=2000
export FOX_DELETE_MAGISK_ADDON=1
export FOX_RECOVERY_INSTALL_PARTITION=/dev/block/by-name/recovery
