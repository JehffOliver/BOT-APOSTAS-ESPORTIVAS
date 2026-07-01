@echo off
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual nao encontrado. Rode:
  echo python -m venv .venv
  echo .venv\Scripts\activate
  echo pip install -r requirements.txt
  exit /b 1
)

echo Iniciando aplicacao em http://127.0.0.1:8000
.venv\Scripts\python.exe -m uvicorn src.web:app --host 127.0.0.1 --port 8000
