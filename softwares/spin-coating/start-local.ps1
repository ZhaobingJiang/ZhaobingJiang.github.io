# 启动“旋涂平坦化计算平台”的本地服务（Flask，默认 8765）。
# 由 setup-local-launch.ps1 注册的 spin-coating:// 协议调用，也可手动运行：
#   powershell -NoProfile -ExecutionPolicy Bypass -File start-local.ps1 -AppDir "D:\...\webapp"
param(
    [Parameter(Mandatory = $true)][string]$AppDir,
    [int]$Port = 8765,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$logDir = Join-Path $env:LOCALAPPDATA 'spin-coating-platform'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir 'launch.log'

function Write-Log([string]$Message) {
    $line = '{0}  {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    Add-Content -Path $logFile -Value $line -Encoding UTF8
}

function Test-ServiceUp {
    try {
        $resp = Invoke-WebRequest -Uri ("http://127.0.0.1:{0}/api/health" -f $Port) `
            -UseBasicParsing -TimeoutSec 2
        return ($resp.StatusCode -eq 200)
    } catch {
        return $false
    }
}

function Show-ErrorBox([string]$Message) {
    try {
        Add-Type -AssemblyName PresentationFramework
        [System.Windows.MessageBox]::Show($Message, '旋涂平坦化计算平台') | Out-Null
    } catch {
        # 无桌面环境时仅写日志
    }
}

try {
    Write-Log ("launch requested: AppDir={0} Port={1}" -f $AppDir, $Port)

    if (Test-ServiceUp) {
        Write-Log 'service already running; opening page'
        if (-not $NoBrowser) { Start-Process ("http://127.0.0.1:{0}/" -f $Port) }
        exit 0
    }

    if (-not (Test-Path (Join-Path $AppDir 'app.py'))) {
        throw ("未找到 app.py：{0}" -f $AppDir)
    }

    $python = $null
    foreach ($name in @('python', 'python3', 'py')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { $python = $cmd.Source; break }
    }
    if (-not $python) { throw '未在 PATH 中找到 python，无法启动服务。' }

    Write-Log ("starting: {0} -u app.py (cwd={1})" -f $python, $AppDir)
    Start-Process -FilePath $python -ArgumentList '-u', 'app.py' `
        -WorkingDirectory $AppDir -WindowStyle Hidden

    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Milliseconds 1000
        if (Test-ServiceUp) {
            Write-Log ("service up after {0}s" -f ($i + 1))
            if (-not $NoBrowser) { Start-Process ("http://127.0.0.1:{0}/" -f $Port) }
            exit 0
        }
    }

    throw '服务在 60 秒内未就绪，请查看日志或手动运行 python app.py。'
} catch {
    Write-Log ('ERROR: ' + $_.Exception.Message)
    Show-ErrorBox ("本地服务启动失败：`n" + $_.Exception.Message + "`n`n日志：" + $logFile)
    exit 1
}
