# Kernel SIF — Guía Windows

## Requisitos

- Windows 10/11
- Python 3.10 o superior ([python.org](https://www.python.org/downloads/))
  - Marcar **"Add Python to PATH"** en el instalador

## Instalación rápida

1. Abrí **PowerShell**
2. Ejecutá:

```powershell
cd ruta\al\kernel_de_SIF
Set-ExecutionPolicy -Scope CurrentUser Bypass -Force
.\windows\install.ps1
```

3. En el Escritorio aparece **Kernel SIF**
4. Abrilo y entrá a: **http://127.0.0.1:8741/**

## Arranque manual

```cmd
cd kernel_de_SIF
python -m pip install -r requirements.txt
python -m kernel serve --host 127.0.0.1 --port 8741
```

Abrí el navegador en `http://127.0.0.1:8741/`

## Credenciales iniciales

```
Usuario:    ceo
Contraseña: FirmaCEO2026!ChangeMe
```

**Cambiá la contraseña en el primer acceso.**

## Modos

| Comando | Descripción |
|---------|-------------|
| `python -m kernel serve` | API + panel web (recomendado) |
| `python -m kernel cli` | Consola de administración |
| `python -m kernel status` | Estado del sistema |
