# Gera a distribuição Windows.
# Uso (PowerShell, na pasta do projeto):
#   .\build.ps1            -> pasta dist\VirtualMacroTextInputer\ (arranque rápido)
#   .\build.ps1 -OneFile   -> um só ficheiro dist\VirtualMacroTextInputer.exe
#                             (descompacta-se para uma pasta temporária a cada
#                             arranque: 1-3 s mais lento)
# Requer Python 3.11+ no PATH (ou indique-o: .\build.ps1 -Python "C:\caminho\python.exe").
param([string]$Python = "python", [switch]$OneFile)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .venv)) { & $Python -m venv .venv }
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install --upgrade pip
& $py -m pip install -e ".[dev]"

Write-Host "== Testes =="
& $py -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Os testes falharam (código de saída $LASTEXITCODE)." }

Write-Host "== PyInstaller =="
$mode = if ($OneFile) { "--onefile" } else { "--onedir" }
& $py -m PyInstaller --noconfirm --clean --windowed $mode `
    --name VirtualMacroTextInputer `
    --icon assets\macropad.ico `
    --paths src `
    --add-data "src\macropad\ui\assets;macropad\ui\assets" `
    --add-data "src\macropad\locales;macropad\locales" `
    --exclude-module tkinter `
    launcher.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou (código de saída $LASTEXITCODE)." }

if ($OneFile) {
    $exe = "dist\VirtualMacroTextInputer.exe"
    $hash = (Get-FileHash $exe -Algorithm SHA256).Hash.ToLower()
    "$hash  VirtualMacroTextInputer.exe" | Set-Content -Encoding ascii "$exe.sha256"
    Write-Host ""
    Write-Host "Pronto: $exe ($([math]::Round((Get-Item $exe).Length / 1MB)) MB)"
    Write-Host "SHA-256: $hash"
    return
}

Copy-Item README.md, ARCHITECTURE.md, EXAMPLES.md dist\VirtualMacroTextInputer\ -Force
Copy-Item docs\pt\README.md dist\VirtualMacroTextInputer\LEIA-ME.md -Force
Copy-Item examples\conjunto-exemplo.toml dist\VirtualMacroTextInputer\ -Force
Write-Host ""
Write-Host "Pronto: dist\VirtualMacroTextInputer\VirtualMacroTextInputer.exe"
Write-Host "Copie a pasta dist\VirtualMacroTextInputer para onde quiser (ex.: %LOCALAPPDATA%\Programs\VirtualMacroTextInputer) e execute VirtualMacroTextInputer.exe."
