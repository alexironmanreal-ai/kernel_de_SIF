# -*- coding: utf-8 -*-
"""Motor RBAC con herencia de roles."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

CLASIFICACION_ORDEN = {
    "PUBLICO": 0, "INTERNO": 1, "CONFIDENCIAL": 2,
    "RESTRINGIDO": 3, "CEO_ONLY": 4,
}

@dataclass
class Permiso:
    area: str
    acciones: List[str]
    clasificacion_max: str = "CONFIDENCIAL"

@dataclass
class Rol:
    id: str
    nombre: str
    descripcion: str
    nivel: int
    permisos: List[Permiso] = field(default_factory=list)
    hereda_de: List[str] = field(default_factory=list)
    es_sistema: bool = False

class RoleEngine:
    def __init__(self, roles_path: Path):
        self.roles_path = roles_path
        self.roles: Dict[str, Rol] = {}
        self.reload()

    def reload(self):
        if not self.roles_path.exists():
            raise FileNotFoundError(f"roles no encontrado: {self.roles_path}")
        with open(self.roles_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.roles.clear()
        for rid, rdata in data.items():
            self.roles[rid] = Rol(
                id=rid,
                nombre=rdata["nombre"],
                descripcion=rdata["descripcion"],
                nivel=rdata["nivel"],
                permisos=[Permiso(**p) for p in rdata.get("permisos", [])],
                hereda_de=rdata.get("hereda_de", []),
                es_sistema=rdata.get("es_sistema", False),
            )

    def permisos_efectivos(self, roles_ids: List[str]) -> List[Permiso]:
        visitados, out = set(), []
        def resolver(rid):
            if rid in visitados or rid not in self.roles:
                return
            visitados.add(rid)
            rol = self.roles[rid]
            for h in rol.hereda_de:
                resolver(h)
            out.extend(rol.permisos)
        for rid in roles_ids:
            resolver(rid)
        return out

    def tiene_permiso(self, roles_ids: List[str], area: str, accion: str, clasificacion: str = "INTERNO") -> bool:
        if "CEO" in roles_ids:
            return True
        nivel_req = CLASIFICACION_ORDEN.get(clasificacion, 1)
        for p in self.permisos_efectivos(roles_ids):
            if p.area in ("*", area):
                if "todo" in p.acciones or accion in p.acciones:
                    if nivel_req <= CLASIFICACION_ORDEN.get(p.clasificacion_max, 2):
                        return True
        return False

    def listar(self) -> List[Rol]:
        return sorted(self.roles.values(), key=lambda r: r.nivel)

    def get(self, role_id: str) -> Optional[Rol]:
        return self.roles.get(role_id)
