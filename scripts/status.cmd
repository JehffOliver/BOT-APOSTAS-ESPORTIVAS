@echo off
curl -s http://127.0.0.1:8000/health >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  echo Aplicacao online: http://127.0.0.1:8000
  exit /b 0
) else (
  echo Aplicacao offline
  exit /b 1
)
