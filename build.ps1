# Gera a distribuição Windows em dist\Macropad\Macropad.exe
# Uso (PowerShell, na pasta do projeto):   .\build.ps1
# Requer Python 3.11+ no PATH (ou indique-o: .\build.ps1 -Python "C:\caminho\python.exe").
param([string]$Python = "python")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .venv)) { & $Python -m venv .venv }
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install --upgrade pip
& $py -m pip install -e ".[dev]"

Write-Host "== Testes =="
& $py -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Os testes falharam." }

Write-Host "== PyInstaller =="
& $py -m PyInstaller --noconfirm --clean --windowed `
    --name Macropad `
    --icon assets\macropad.ico `
    --paths src `
    --add-data "src\macropad\ui\assets;macropad\ui\assets" `
    --add-data "src\macropad\locales;macropad\locales" `
    --exclude-module tkinter `
    launcher.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou." }

Copy-Item README.md dist\Macropad\ -Force
Copy-Item examples\conjunto-exemplo.toml dist\Macropad\ -Force
Write-Host ""
Write-Host "Pronto: dist\Macropad\Macropad.exe"
Write-Host "Copie a pasta dist\Macropad para onde quiser (ex.: %LOCALAPPDATA%\Programs\Macropad) e execute Macropad.exe."
