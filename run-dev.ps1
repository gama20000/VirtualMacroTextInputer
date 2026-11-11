# Executa o Macropad a partir do código-fonte (com consola, para ver erros).
# Uso: .\run-dev.ps1            (cria .venv na primeira vez)
param([string]$Python = "python")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path .venv)) {
    & $Python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
}
.\.venv\Scripts\python.exe -m macropad --show-config @args
