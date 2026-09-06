$ErrorActionPreference = 'Stop'
$pidPath = Join-Path $PSScriptRoot 'data/server.pid'
if (-not (Test-Path -LiteralPath $pidPath)) { Write-Output '没有找到该项目的后台进程记录。'; exit 0 }
$serverPid = [int](Get-Content -LiteralPath $pidPath)
$process = Get-Process -Id $serverPid -ErrorAction SilentlyContinue
if ($process) {
    $expected = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '.venv/Scripts/python.exe'))
    $startedPath = Join-Path $PSScriptRoot 'data/server.started'
    if (-not (Test-Path -LiteralPath $startedPath)) { throw '缺少进程启动时间记录，已拒绝停止。' }
    $expectedTicks = [long](Get-Content -LiteralPath $startedPath)
    if ($process.Path -ne $expected -or $process.StartTime.ToUniversalTime().Ticks -ne $expectedTicks) { throw '进程身份不匹配，已拒绝停止。' }
    Stop-Process -Id $serverPid
}
Remove-Item -LiteralPath $pidPath
Write-Output '星源服务已停止。'
