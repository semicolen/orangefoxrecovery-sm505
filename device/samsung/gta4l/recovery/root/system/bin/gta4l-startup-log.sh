#!/system/bin/sh
# RAM-only snapshots survive a recovery UI hang, until the next reboot.
snapshot=0
while [ "$snapshot" -lt 12 ]; do
    {
        echo "=== startup snapshot $snapshot ==="
        cat /proc/uptime
        for prop in ro.orangefox.release.version of_skip_fbe_decryption ro.crypto.state ro.crypto.type crypto.ready hwservicemanager.ready keymaster_ver vendor.sys.listeners.registered sys.listeners.registered; do
            echo "$prop=$(getprop "$prop")"
        done
        getprop | grep '^\[init.svc.'
        ps -A
    } >> /tmp/gta4l-startup.log 2>&1
    logcat -b all -d -v threadtime > /tmp/logcat.log 2>&1
    dmesg > /tmp/kernel.log 2>&1
    snapshot=$((snapshot + 1))
    sleep 5
done
