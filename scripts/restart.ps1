$ScriptDir = $PSScriptRoot

& (Join-Path $ScriptDir 'stop.ps1')
Start-Sleep -Seconds 1
& (Join-Path $ScriptDir 'start.ps1')
