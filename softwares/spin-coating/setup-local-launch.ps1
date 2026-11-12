# 一次性注册 spin-coating:// 启动协议（仅写入当前用户 HKCU，无需管理员）。
# 注册后，软件介绍页上的“启动本地服务”按钮即可拉起本机 Flask 服务并自动打开软件页面。
#
# 用法（在本文件所在目录）：
#   powershell -ExecutionPolicy Bypass -File setup-local-launch.ps1 -AppDir "D:\...\webapp"
# 卸载：
#   powershell -ExecutionPolicy Bypass -File setup-local-launch.ps1 -Uninstall
param(
    [string]$AppDir,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$protocol = 'spin-coating'
$key = 'HKCU:\Software\Classes\' + $protocol

if ($Uninstall) {
    if (Test-Path $key) {
        Remove-Item -Path $key -Recurse -Force
        Write-Host "已移除启动协议 $protocol."
    } else {
        Write-Host "启动协议 $protocol 未注册，无需移除。"
    }
    exit 0
}

if ([string]::IsNullOrWhiteSpace($AppDir)) {
    throw '请用 -AppDir 指定软件的 webapp 目录（含 app.py），例如：-AppDir "D:\...\webapp"'
}
$AppDir = (Resolve-Path $AppDir).Path
if (-not (Test-Path (Join-Path $AppDir 'app.py'))) {
    throw ("AppDir 下未找到 app.py：{0}" -f $AppDir)
}

$startScript = Join-Path $PSScriptRoot 'start-local.ps1'
if (-not (Test-Path $startScript)) {
    throw ("未找到 start-local.ps1：{0}" -f $startScript)
}

$psExe = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$command = '"{0}" -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{1}" -AppDir "{2}"' -f `
    $psExe, $startScript, $AppDir

New-Item -Path $key -Force | Out-Null
Set-ItemProperty -Path $key -Name '(default)' -Value 'URL:Spin-Coating Planarization Local Launcher'
New-ItemProperty -Path $key -Name 'URL Protocol' -Value '' -PropertyType String -Force | Out-Null
New-Item -Path ($key + '\shell\open\command') -Force | Out-Null
Set-ItemProperty -Path ($key + '\shell\open\command') -Name '(default)' -Value $command

Write-Host '已注册启动协议。'
Write-Host ("  协议：{0}://start" -f $protocol)
Write-Host ("  脚本：{0}" -f $startScript)
Write-Host ("  软件目录：{0}" -f $AppDir)
Write-Host ''
Write-Host '现在可在软件介绍页点击“启动本地服务”（浏览器首次会询问是否打开，选择“打开”）。'
