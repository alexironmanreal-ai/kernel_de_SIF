#Requires -Version 5.1
<#
.SYNOPSIS
  Instalador del Kernel SIF para Windows
.DESCRIPTION
  Instala dependencias, crea acceso directo y opcionalmente registra el servicio.
#>
param(
  [string]$InstallDir = "$env:LOCALAPPDATA\FirmaKernel",
  [switch]$AsService,
  [int]$Port = 8741
)

$ErrorActionPreference = "Stop"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Kernel SIF — Instalador Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$python = $null
foreach ($c in @("python", "py", "python3")) {
  try {
    $v = & $c --version 2>$null
    if ($LASTEXITCODE -eq 0 -or $v) { $python = $c; break }
  } catch {}
}
if (-not $python) {
  Write-Host "ERROR: Python no encontrado. Instalá Python 3.10+ desde python.org" -ForegroundColor Red
  exit 1
}
Write-Host "[OK] Python: $python" -ForegroundColor Green

$Src = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not (Test-Path (Join-Path $Src "kernel"))) {
  $Src = Split-Path -Parent $MyInvocation.MyCommand.Path
}
if (-not (Test-Path (Join-Path $Src "kernel"))) {
  Write-Host "ERROR: No se encuentra el código del kernel junto al instalador." -ForegroundColor Red
  exit 1
}

Write-Host "[*] Instalando en: $InstallDir"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path "$InstallDir\data","$InstallDir\logs" | Out-Null

$items = @("kernel","web","config","roles","requirements.txt","run.py","README.md")
foreach ($i in $items) {
  $from = Join-Path $Src $i
  if (Test-Path $from) {
    Copy-Item -Path $from -Destination $InstallDir -Recurse -Force
  }
}
Write-Host "[OK] Archivos copiados" -ForegroundColor Green

Write-Host "[*] Instalando dependencias..."
& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $InstallDir "requirements.txt")
if ($LASTEXITCODE -ne 0) {
  Write-Host "ERROR al instalar dependencias" -ForegroundColor Red
  exit 1
}
Write-Host "[OK] Dependencias" -ForegroundColor Green

$startPs1 = @"
Set-Location '$InstallDir'
& $python -m kernel serve --host 127.0.0.1 --port $Port
"@
Set-Content -Path (Join-Path $InstallDir "start_kernel.ps1") -Value $startPs1 -Encoding UTF8

$startBat = @"
@echo off
cd /d "$InstallDir"
$python -m kernel serve --host 127.0.0.1 --port $Port
pause
"@
Set-Content -Path (Join-Path $InstallDir "start_kernel.bat") -Value $startBat -Encoding ASCII

$desktop = [Environment]::GetFolderPath("Desktop")
$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut((Join-Path $desktop "Kernel SIF.lnk"))
$sc.TargetPath = "powershell.exe"
$sc.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$InstallDir\start_kernel.ps1`""
$sc.WorkingDirectory = $InstallDir
$sc.Description = "Firma Inteligencia Kernel SIF"
$sc.Save()
Write-Host "[OK] Acceso directo en Escritorio" -ForegroundColor Green

Write-Host ""
Write-Host "Instalacion completada." -ForegroundColor Green
Write-Host "  Panel web:  http://127.0.0.1:$Port/"
Write-Host "  Usuario:    ceo"
Write-Host "  Password:   FirmaCEO2026!ChangeMe"
Write-Host "  CAMBIA LA CONTRASENA en el primer login."
