@echo off
title Kernel SIF - Firma Inteligencia
cd /d "%~dp0\.."
echo Iniciando Kernel SIF...
echo Panel: http://127.0.0.1:8741/
echo.
python -m kernel serve --host 127.0.0.1 --port 8741
if errorlevel 1 (
  echo.
  echo Si falla, prueba: py -m kernel serve --host 127.0.0.1 --port 8741
  pause
)
