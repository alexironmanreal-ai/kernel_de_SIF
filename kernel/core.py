# -*- coding: utf-8 -*-
"""Núcleo del Kernel Empresarial."""
from __future__ import annotations
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

from . import __version__
from .rbac import RoleEngine
from .db import KernelDB, Usuario
from .security import PasswordPolicy

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "kernel.yaml"
ROLES_PATH = ROOT / "roles" / "roles.json"
DB_PATH = ROOT / "data" / "firma_kernel.db"
AUDIT_FILE = ROOT / "logs" / "audit.log"


class FirmaKernel:
    """Sistema operativo empresarial — control de acceso, usuarios, auditoría."""

    def __init__(self, root: Optional[Path] = None):
        self.root = root or ROOT
        self.config = self._load_config()
        self.roles = RoleEngine(self.root / "roles" / "roles.json")
        self.db = KernelDB(self.root / "data" / "firma_kernel.db")
        self.policy = PasswordPolicy()
        self.usuario: Optional[Usuario] = None
        self.token: Optional[str] = None
        self._ensure_ceo()
        AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _load_config(self) -> dict:
        path = self.root / "config" / "kernel.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            default = {
                "empresa": "Firma Inteligencia / Mi Firma SRL",
                "version_kernel": __version__,
                "idioma": "es",
                "timezone": "America/Argentina/Buenos_Aires",
                "seguridad": {
                    "max_intentos_login": 5,
                    "bloqueo_minutos": 15,
                    "sesion_horas": 8,
                    "ceo_bypass": True,
                },
                "api": {"host": "0.0.0.0", "port": 8741},
                "modulos_habilitados": [
                    "OSINT", "FININT", "CYBERINT", "SOCMINT", "HUMINT", "GEOINT",
                    "AML", "DUE_DILIGENCE", "ESG", "ISO27001", "SOC2",
                    "LITIGATION_SUPPORT", "RIESGO_PAIS", "SEGURIDAD_CORPORATIVA",
                ],
            }
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(default, f, allow_unicode=True, default_flow_style=False)
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _ensure_ceo(self):
        if self.db.obtener_por_username("ceo"):
            return
        u = Usuario(
            id="usr-ceo-001",
            username="ceo",
            nombre_completo="Director General / CEO",
            email="ceo@firmainteligencia.com",
            roles=["CEO"],
            creado=datetime.now(timezone.utc).isoformat(),
            metadata={"cargo": "CEO", "nivel": 0},
        )
        self.db.crear_usuario(u, "FirmaCEO2026!ChangeMe")
        self._log("sistema", "BOOT", detalle="Usuario CEO inicial creado")

    def _log(self, username: str, accion: str, **kw):
        uid = self.usuario.id if self.usuario else "sistema"
        self.db.audit(uid, username, accion, **kw)
        line = (
            f"{datetime.now(timezone.utc).isoformat()} | {username} | {accion} | "
            f"{kw.get('area','')}/{kw.get('recurso','')} | {kw.get('resultado','OK')} | {kw.get('detalle','')}\n"
        )
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(line)

    def login(self, username: str, password: str, ip: str = "local") -> tuple:
        sec = self.config.get("seguridad", {})
        u, msg = self.db.autenticar(
            username, password,
            max_intentos=sec.get("max_intentos_login", 5),
            bloqueo_minutos=sec.get("bloqueo_minutos", 15),
        )
        if not u:
            self._log(username, "LOGIN", resultado="FALLIDO", detalle=msg, ip=ip)
            return False, msg
        self.usuario = u
        self.token = self.db.crear_sesion(u, horas=sec.get("sesion_horas", 8), ip=ip)
        self._log(username, "LOGIN", resultado="OK", detalle=f"roles={u.roles}", ip=ip)
        return True, self.token

    def logout(self):
        if self.token:
            self.db.cerrar_sesion(self.token)
        if self.usuario:
            self._log(self.usuario.username, "LOGOUT")
        self.usuario = None
        self.token = None

    def restore_session(self, token: str) -> bool:
        u = self.db.validar_sesion(token)
        if not u:
            return False
        self.usuario = u
        self.token = token
        return True

    def check(self, area: str, accion: str, clasificacion: str = "INTERNO") -> bool:
        if not self.usuario:
            return False
        ok = self.roles.tiene_permiso(self.usuario.roles, area, accion, clasificacion)
        self._log(
            self.usuario.username, f"CHECK_{accion.upper()}",
            area=area, resultado="PERMITIDO" if ok else "DENEGADO",
            detalle=f"clasif={clasificacion}",
        )
        return ok

    def require(self, area: str, accion: str, clasificacion: str = "INTERNO"):
        if not self.check(area, accion, clasificacion):
            raise PermissionError(
                f"Denegado: {self.usuario.username if self.usuario else 'anon'} "
                f"no puede '{accion}' en '{area}' ({clasificacion})"
            )

    def es_ceo(self) -> bool:
        return bool(self.usuario and "CEO" in self.usuario.roles)

    def crear_usuario(self, username: str, nombre: str, email: str,
                      roles: List[str], password: str) -> tuple:
        self.require("14_Recursos_Humanos", "crear", "RESTRINGIDO")
        for r in roles:
            if r not in self.roles.roles:
                return False, f"Rol inexistente: {r}"
        if "CEO" in roles and not self.es_ceo():
            return False, "Solo el CEO puede asignar rol CEO"
        ok_pwd, msg = self.policy.validate(password)
        if not ok_pwd:
            return False, f"Contraseña débil: {msg}"
        u = Usuario(
            id=f"usr-{username}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            username=username, nombre_completo=nombre, email=email, roles=roles,
            creado=datetime.now(timezone.utc).isoformat(),
        )
        if not self.db.crear_usuario(u, password):
            return False, "Username ya existe"
        self._log(self.usuario.username, "CREAR_USUARIO", recurso=username, detalle=f"roles={roles}")
        return True, "Usuario creado"

    def cambiar_password(self, username: str, new_password: str) -> tuple:
        if not self.usuario:
            return False, "No autenticado"
        if username != self.usuario.username and not self.es_ceo():
            return False, "Solo podés cambiar tu propia contraseña (o ser CEO)"
        ok_pwd, msg = self.policy.validate(new_password)
        if not ok_pwd:
            return False, f"Contraseña débil: {msg}"
        self.db.cambiar_password(username, new_password)
        self._log(self.usuario.username, "CAMBIAR_PASSWORD", recurso=username)
        return True, "Contraseña actualizada"

    def listar_usuarios(self) -> List[Usuario]:
        self.require("14_Recursos_Humanos", "leer", "CONFIDENCIAL")
        return self.db.listar_usuarios()

    def info(self) -> Dict[str, Any]:
        return {
            "kernel": f"Firma Inteligencia Kernel v{__version__}",
            "empresa": self.config.get("empresa"),
            "usuario": self.usuario.username if self.usuario else None,
            "roles": self.usuario.roles if self.usuario else [],
            "es_ceo": self.es_ceo(),
            "token_activo": bool(self.token),
            "modulos": self.config.get("modulos_habilitados", []),
        }
