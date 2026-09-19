$ErrorActionPreference = "Stop"
$app = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:SRAI_OPERATIONS_ROOT = if ($env:SRAI_OPERATIONS_ROOT) { $env:SRAI_OPERATIONS_ROOT } else { "C:\SRAI_GitHub\SRAI_Operations" }
Set-Location $app
Write-Host "Registry: $env:SRAI_OPERATIONS_ROOT"
Write-Host "Dashboard: http://127.0.0.1:8010/"
& ".\.venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8010
