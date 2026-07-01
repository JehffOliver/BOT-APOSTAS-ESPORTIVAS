try {
    $response = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 3
    if ($response.status -eq 'online') {
        Write-Host 'Aplicacao online: http://127.0.0.1:8000' -ForegroundColor Green
        exit 0
    }
}
catch {
    Write-Host 'Aplicacao offline' -ForegroundColor Red
    exit 1
}
