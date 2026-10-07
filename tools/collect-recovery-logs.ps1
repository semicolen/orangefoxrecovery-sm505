$ErrorActionPreference = 'Stop'
$taskWorkspace = Split-Path -Parent $PSScriptRoot
$taskLogDirectory = Join-Path $taskWorkspace ('logs\recovery-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
$taskAdbState = & adb get-state 2>$null
if ($LASTEXITCODE -ne 0 -or $taskAdbState -ne 'recovery') {
    throw 'ADB must show the tablet in recovery. Keep it connected at the splash or recovery UI.'
}
New-Item -ItemType Directory -Path $taskLogDirectory | Out-Null
foreach ($taskLogPath in '/tmp/recovery.log', '/tmp/gta4l-startup.log', '/tmp/logcat.log', '/tmp/kernel.log') {
    & adb pull $taskLogPath $taskLogDirectory
    # The first build does not include all of the additional startup logs.
}
& adb shell 'logcat -b all -d -v threadtime' | Set-Content -LiteralPath (Join-Path $taskLogDirectory 'logcat-live.log') -Encoding utf8
& adb shell dmesg | Set-Content -LiteralPath (Join-Path $taskLogDirectory 'kernel-live.log') -Encoding utf8
& adb shell 'ps -A; getprop | grep "^\[init.svc."' | Set-Content -LiteralPath (Join-Path $taskLogDirectory 'services.log') -Encoding utf8
Write-Output $taskLogDirectory
