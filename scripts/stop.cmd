@echo off
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
  echo Encerrando processo PID %%a
  taskkill /PID %%a /F
  exit /b 0
)
echo Aplicacao ja esta offline.
