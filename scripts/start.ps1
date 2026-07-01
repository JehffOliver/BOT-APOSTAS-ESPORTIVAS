$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root '.venv\Scripts\python.exe'

if (!(Test-Path $Python)) {
    Write-Host 'Ambiente virtual nao encontrado. Rode os comandos de instalacao primeiro.' -ForegroundColor Yellow
    exit 1
}

Set-Location $Root
Write-Host 'Iniciando aplicacao em http://127.0.0.1:8000'
& $Python -m uvicorn src.web:app --host 127.0.0.1 --port 8000
