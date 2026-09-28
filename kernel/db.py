# -*- coding: utf-8 -*-
"""Capa de persistencia SQLite."""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from .security import hash_password, verify_password, generate_token

@dataclass
class Usuario:
    id: str
    username: str
    nombre_completo: str
    email: str
    roles: List[str]
    activo: bool = True
    password_hash: str = ""
    creado: str = ""
    ultimo_acceso: Optional[str] = None
    intentos_fallidos: int = 0
    bloqueado_hasta: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class KernelDB:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=DELETE")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    nombre_completo TEXT NOT NULL,
                    email TEXT DEFAULT '',
                    roles TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    activo INTEGER DEFAULT 1,
                    creado TEXT NOT NULL,
                    ultimo_acceso TEXT,
                    intentos_fallidos INTEGER DEFAULT 0,
                    bloqueado_hasta TEXT,
                    metadata TEXT DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS sesiones (
                    token TEXT PRIMARY KEY,
                    usuario_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    roles TEXT NOT NULL,
                    creada TEXT NOT NULL,
                    expira TEXT NOT NULL,
                    activa INTEGER DEFAULT 1,
                    ip TEXT DEFAULT 'local'
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    usuario_id TEXT,
                    username TEXT,
                    accion TEXT NOT NULL,
                    area TEXT DEFAULT '',
                    recurso TEXT DEFAULT '',
                    resultado TEXT DEFAULT 'OK',
                    detalle TEXT DEFAULT '',
                    ip TEXT DEFAULT 'local'
                );
                CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(timestamp);
                CREATE INDEX IF NOT EXISTS idx_sesiones_user ON sesiones(usuario_id);
            """)

    def crear_usuario(self, u: Usuario, password: str) -> bool:
        try:
            with self._conn() as c:
                c.execute(
                    """INSERT INTO usuarios
                       (id,username,nombre_completo,email,roles,password_hash,activo,creado,metadata)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (u.id, u.username, u.nombre_completo, u.email,
                     json.dumps(u.roles), hash_password(password),
                     1 if u.activo else 0,
                     u.creado or datetime.now(timezone.utc).isoformat(),
                     json.dumps(u.metadata))
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def _row_to_user(self, row) -> Usuario:
        return Usuario(
            id=row["id"], username=row["username"],
            nombre_completo=row["nombre_completo"], email=row["email"] or "",
            roles=json.loads(row["roles"]), activo=bool(row["activo"]),
            password_hash=row["password_hash"], creado=row["creado"],
            ultimo_acceso=row["ultimo_acceso"],
            intentos_fallidos=row["intentos_fallidos"] or 0,
            bloqueado_hasta=row["bloqueado_hasta"],
            metadata=json.loads(row["metadata"] or "{}"),
        )

    def obtener_por_username(self, username: str) -> Optional[Usuario]:
        with self._conn() as c:
            row = c.execute("SELECT * FROM usuarios WHERE username=?", (username,)).fetchone()
        return self._row_to_user(row) if row else None

    def listar_usuarios(self) -> List[Usuario]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM usuarios ORDER BY username").fetchall()
        return [self._row_to_user(r) for r in rows]

    def autenticar(self, username: str, password: str, max_intentos: int = 5, bloqueo_minutos: int = 15) -> tuple:
        u = self.obtener_por_username(username)
        if not u:
            return None, "Credenciales inválidas"
        if not u.activo:
            return None, "Usuario desactivado"
        ahora = datetime.now(timezone.utc)
        if u.bloqueado_hasta:
            hasta = datetime.fromisoformat(u.bloqueado_hasta)
            if ahora < hasta:
                mins = int((hasta - ahora).total_seconds() / 60) + 1
                return None, f"Cuenta bloqueada. Reintentar en {mins} min"
        if not verify_password(password, u.password_hash):
            intentos = u.intentos_fallidos + 1
            bloqueado = None
            if intentos >= max_intentos:
                bloqueado = (ahora + timedelta(minutes=bloqueo_minutos)).isoformat()
                intentos = 0
            with self._conn() as c:
                c.execute(
                    "UPDATE usuarios SET intentos_fallidos=?, bloqueado_hasta=? WHERE id=?",
                    (intentos, bloqueado, u.id)
                )
            if bloqueado:
                return None, f"Demasiados intentos. Bloqueado {bloqueo_minutos} min"
            return None, f"Credenciales inválidas ({intentos}/{max_intentos})"
        ahora_iso = ahora.isoformat()
        with self._conn() as c:
            c.execute(
                "UPDATE usuarios SET ultimo_acceso=?, intentos_fallidos=0, bloqueado_hasta=NULL WHERE id=?",
                (ahora_iso, u.id)
            )
        u.ultimo_acceso = ahora_iso
        u.intentos_fallidos = 0
        u.bloqueado_hasta = None
        return u, "OK"

    def crear_sesion(self, u: Usuario, horas: int = 8, ip: str = "local") -> str:
        token = generate_token()
        ahora = datetime.now(timezone.utc)
        expira = (ahora + timedelta(hours=horas)).isoformat()
        with self._conn() as c:
            c.execute(
                """INSERT INTO sesiones (token,usuario_id,username,roles,creada,expira,activa,ip)
                   VALUES (?,?,?,?,?,?,1,?)""",
                (token, u.id, u.username, json.dumps(u.roles), ahora.isoformat(), expira, ip)
            )
        return token

    def validar_sesion(self, token: str) -> Optional[Usuario]:
        with self._conn() as c:
            row = c.execute(
                "SELECT * FROM sesiones WHERE token=? AND activa=1", (token,)
            ).fetchone()
        if not row:
            return None
        expira = datetime.fromisoformat(row["expira"])
        if datetime.now(timezone.utc) > expira:
            with self._conn() as c:
                c.execute("UPDATE sesiones SET activa=0 WHERE token=?", (token,))
            return None
        return self.obtener_por_username(row["username"])

    def cerrar_sesion(self, token: str):
        with self._conn() as c:
            c.execute("UPDATE sesiones SET activa=0 WHERE token=?", (token,))

    def audit(self, usuario_id: str, username: str, accion: str,
              area: str = "", recurso: str = "", resultado: str = "OK",
              detalle: str = "", ip: str = "local"):
        try:
            with self._conn() as c:
                c.execute(
                    """INSERT INTO audit_log
                       (timestamp,usuario_id,username,accion,area,recurso,resultado,detalle,ip)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (datetime.now(timezone.utc).isoformat(), usuario_id, username,
                     accion, area, recurso, resultado, detalle, ip)
                )
        except Exception:
            pass

    def cambiar_password(self, username: str, new_password: str) -> bool:
        with self._conn() as c:
            c.execute(
                "UPDATE usuarios SET password_hash=? WHERE username=?",
                (hash_password(new_password), username)
            )
            return c.total_changes > 0
