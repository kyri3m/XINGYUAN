param([int]$Port = 8080)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw '请先按照 README.md 创建 .venv 并安装 requirements.txt。' }
$healthUrl = "http://127.0.0.1:$Port/api/health"
try {
    $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
    if ($health.version -eq '2.0.0') { Write-Output "星源已运行：http://127.0.0.1:$Port"; exit 0 }
} catch { }
$logDir = Join-Path $projectRoot 'data'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$server = Start-Process -FilePath $pythonPath -ArgumentList @('-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', "$Port") -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDir 'server.log') -RedirectStandardError (Join-Path $logDir 'server-error.log') -PassThru
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 500
    $server.Refresh()
    if ($server.HasExited) { throw '服务启动失败，请查看 data/server-error.log，确认端口是否被占用。' }
    try {
        $health = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 1
        if ($health.version -eq '2.0.0') {
            $server.Id | Set-Content -LiteralPath (Join-Path $logDir 'server.pid')
            $server.StartTime.ToUniversalTime().Ticks | Set-Content -LiteralPath (Join-Path $logDir 'server.started')
            Write-Output "星源已启动：http://127.0.0.1:$Port"
            exit 0
        }
    } catch { }
}
throw '服务健康检查超时，请查看 data/server-error.log。'
