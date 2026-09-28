# -*- coding: utf-8 -*-
"""API HTTP local del Kernel (para VM / integraciones)."""
from __future__ import annotations
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from .core import FirmaKernel

app = FastAPI(
    title="Firma Inteligencia Kernel",
    description="API de control de acceso y gestión empresarial",
    version="3.0.0",
)
_kernel: Optional[FirmaKernel] = None


def get_kernel() -> FirmaKernel:
    global _kernel
    if _kernel is None:
        _kernel = FirmaKernel()
    return _kernel


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    ok: bool
    token: Optional[str] = None
    message: str = ""
    roles: List[str] = []


class CheckIn(BaseModel):
    area: str
    accion: str
    clasificacion: str = "INTERNO"


class UserCreate(BaseModel):
    username: str
    nombre: str
    email: str = ""
    roles: List[str]
    password: str = Field(..., min_length=12)


def auth_user(authorization: Optional[str] = Header(None)) -> FirmaKernel:
    k = get_kernel()
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Token requerido (Bearer <token>)")
    token = authorization[7:].strip()
    if not k.restore_session(token):
        raise HTTPException(401, "Sesión inválida o expirada")
    return k


@app.get("/health")
def health():
    return {"status": "ok", "service": "firma-kernel", "version": "3.0.0"}


@app.post("/auth/login", response_model=LoginOut)
def login(body: LoginIn):
    k = get_kernel()
    ok, result = k.login(body.username, body.password)
    if not ok:
        return LoginOut(ok=False, message=result)
    return LoginOut(ok=True, token=result, message="OK", roles=k.usuario.roles if k.usuario else [])


@app.post("/auth/logout")
def logout(k: FirmaKernel = Depends(auth_user)):
    k.logout()
    return {"ok": True}


@app.get("/me")
def me(k: FirmaKernel = Depends(auth_user)):
    return k.info()


@app.post("/check")
def check_perm(body: CheckIn, k: FirmaKernel = Depends(auth_user)):
    allowed = k.check(body.area, body.accion, body.clasificacion)
    return {"allowed": allowed, "area": body.area, "accion": body.accion}


@app.get("/roles")
def roles(k: FirmaKernel = Depends(auth_user)):
    return [
        {"id": r.id, "nombre": r.nombre, "nivel": r.nivel, "descripcion": r.descripcion}
        for r in k.roles.listar()
    ]


@app.get("/users")
def users(k: FirmaKernel = Depends(auth_user)):
    try:
        us = k.listar_usuarios()
        return [
            {"username": u.username, "nombre": u.nombre_completo, "roles": u.roles, "activo": u.activo}
            for u in us
        ]
    except PermissionError as e:
        raise HTTPException(403, str(e))


@app.post("/users")
def create_user(body: UserCreate, k: FirmaKernel = Depends(auth_user)):
    try:
        ok, msg = k.crear_usuario(body.username, body.nombre, body.email, body.roles, body.password)
        if not ok:
            raise HTTPException(400, msg)
        return {"ok": True, "message": msg}
    except PermissionError as e:
        raise HTTPException(403, str(e))
