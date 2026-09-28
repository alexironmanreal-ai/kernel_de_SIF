# Kernel SIF v3.0 — Firma Inteligencia

Sistema de control de acceso empresarial (RBAC) con **panel web**, API HTTP y CLI.
Compatible con **Windows 10/11** y **Linux (VM)**.

## Windows (recomendado)

1. Instalá Python 3.10+ desde python.org (**Add Python to PATH**)
2. En PowerShell o CMD:

```text
cd kernel_de_SIF
python -m pip install -r requirements.txt
python -m kernel serve --host 127.0.0.1 --port 8741
```

3. Abrí el navegador en **http://127.0.0.1:8741/**

Instalador con acceso directo:

```powershell
Set-ExecutionPolicy -Scope CurrentUser Bypass -Force
.\windows\install.ps1
```

## Linux / VM

```bash
pip install -r requirements.txt
python3 -m kernel serve --host 0.0.0.0 --port 8741
# servicio:
sudo bash scripts/install_vm.sh
```

## Login inicial

```
Usuario:    ceo
Contraseña: FirmaCEO2026!ChangeMe
```

**Cambiá la contraseña en el primer acceso.**

## Componentes

| Componente | Descripción |
|------------|-------------|
| Panel web | Dashboard, roles, usuarios, check de permisos |
| API REST | Autenticación Bearer |
| CLI | Consola de administración |
| RBAC | 14 roles, CEO = root |
| Seguridad | bcrypt, bloqueo de intentos, sesiones |

## Estructura

- `kernel/` — núcleo Python
- `web/` — interfaz web
- `windows/` — instalador y scripts Windows
- `scripts/` — instalador VM Linux
- `systemd/` — unit systemd
- `roles/` — roles.json
- `config/` — kernel.yaml
