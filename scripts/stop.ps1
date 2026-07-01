$port = 8000
$connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue

if (!$connections) {
    Write-Host 'Aplicacao ja esta offline.' -ForegroundColor Yellow
    exit 0
}

$processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($processId in $processIds) {
    Stop-Process -Id $processId -Force
    Write-Host "Processo encerrado. PID: $processId" -ForegroundColor Green
}
