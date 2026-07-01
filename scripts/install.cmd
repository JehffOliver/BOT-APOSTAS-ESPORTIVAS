@echo off
setlocal
cd /d "%~dp0.."

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual .venv...
  python -m venv .venv
)

echo Atualizando pip dentro do .venv...
.venv\Scripts\python.exe -m pip install --upgrade pip

echo Instalando dependencias dentro do .venv...
.venv\Scripts\python.exe -m pip install -r requirements.txt

echo.
echo Instalacao concluida.
echo Agora rode: scripts\start.cmd
