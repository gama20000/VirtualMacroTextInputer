@echo off
rem Arranca o Macropad a partir do codigo, com uma configuracao de teste separada
rem (%TEMP%\MacropadTeste). Nao mexe nas macros reais em %APPDATA%\Macropad.
rem Usa python.exe (com consola) para os erros ficarem visiveis.
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Falta o ambiente .venv. Corra primeiro run-dev.ps1.
  pause
  exit /b 1
)
start "Macropad (teste)" ".venv\Scripts\python.exe" -m macropad --show-config --config-dir "%TEMP%\MacropadTeste"
