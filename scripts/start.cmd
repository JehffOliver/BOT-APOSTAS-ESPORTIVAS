@echo off
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual nao encontrado. Criando agora...
  python -m venv .venv
)

.venv\Scripts\python.exe -c "import uvicorn" >nul 2>nul
if errorlevel 1 (
  echo Dependencias nao encontradas dentro do .venv.
  echo Instalando dependencias agora...
  .venv\Scripts\python.exe -m pip install -r requirements.txt
)

echo Iniciando aplicacao em http://127.0.0.1:8000
.venv\Scripts\python.exe -m uvicorn src.web:app --host 127.0.0.1 --port 8000
