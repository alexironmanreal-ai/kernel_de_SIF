# Firma Inteligencia — Kernel Empresarial v3.0

**Sistema de control de acceso empresarial (RBAC) listo para VM.**

No es un script suelto: es un servicio con API HTTP, CLI de administración, sesiones, bloqueo por intentos, bcrypt y unit de systemd.

---

## Arranque rápido (desarrollo / Windows)

```bash
cd firma_kernel
python -m pip install -r requirements.txt
python -m kernel status
python -m kernel cli
```

Login inicial:
```
Usuario:    ceo
Contraseña: FirmaCEO2026!ChangeMe
```

**Cambiá la contraseña del CEO de inmediato** (`passwd` en la CLI).

---

## Modos de ejecución

| Comando | Uso |
|---------|-----|
| `python -m kernel cli` | Consola interactiva de administración |
| `python -m kernel serve` | API HTTP (puerto 8741 por defecto) |
| `python -m kernel status` | Estado del sistema |

Equivalente: `python run.py [cli|serve|status]`

---

## Instalación en VM Linux (producción)

```bash
sudo bash scripts/install_vm.sh
```

Esto:
1. Crea usuario de sistema `firma`
2. Instala en `/opt/firma_kernel` con venv
3. Registra e inicia el servicio systemd `firma-kernel`
4. Expone la API en el puerto 8741

Comandos post-instalación:
```bash
systemctl status firma-kernel
systemctl restart firma-kernel
journalctl -u firma-kernel -f

# CLI como el usuario del servicio
sudo -u firma /opt/firma_kernel/venv/bin/python -m kernel cli
```

---

## API (cuando corre `serve`)

| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/health` | No | Healthcheck |
| POST | `/auth/login` | No | `{username, password}` → token |
| POST | `/auth/logout` | Bearer | Cierra sesión |
| GET | `/me` | Bearer | Info del usuario |
| POST | `/check` | Bearer | Verifica permiso |
| GET | `/roles` | Bearer | Lista roles |
| GET | `/users` | Bearer | Lista usuarios |
| POST | `/users` | Bearer | Crea usuario |

Ejemplo login:
```bash
curl -X POST http://127.0.0.1:8741/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ceo","password":"FirmaCEO2026!ChangeMe"}'
```

---

## Seguridad v3

- Hash de contraseñas con **bcrypt** (cost 12)
- Política de contraseña (12+ chars, mayúscula, minúscula, dígito, especial)
- Bloqueo de cuenta tras 5 intentos fallidos (15 min)
- Sesiones con token y expiración (8 h por defecto)
- CEO = root (bypass total)
- Auditoría en DB + archivo `logs/audit.log`
- systemd con `ProtectSystem`, `NoNewPrivileges`, paths restringidos

---

## Estructura

```
firma_kernel/
├── kernel/           # Código del sistema
│   ├── __main__.py   # Entrada
│   ├── core.py       # Núcleo
│   ├── rbac.py       # Roles y permisos
│   ├── db.py         # SQLite + sesiones
│   ├── security.py   # bcrypt / políticas
│   ├── api.py        # FastAPI
│   └── cli.py        # Consola
├── config/kernel.yaml
├── roles/roles.json
├── data/             # DB (no versionar en prod sensible)
├── logs/
├── systemd/          # Unit para VM
├── scripts/install_vm.sh
├── requirements.txt
└── run.py
```

---

## Roles (resumen)

CEO (0) · CTO · COO · CFO · CISO · Director Inteligencia · Analista Senior · Analista · Investigador OSINT · Comercial · RRHH · Auditor · Administrativo · Invitado

El **CEO** tiene acceso total a todas las áreas y clasificaciones.

---

Firma Inteligencia — Kernel v3.0  
*Diseñado para correr como servicio en VM, no como script de escritorio.*
