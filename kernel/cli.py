# -*- coding: utf-8 -*-
"""CLI de administración del Kernel."""
from __future__ import annotations
import getpass
import sys

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init()
    GREEN, RED, YELLOW, CYAN, RESET, BOLD = (
        Fore.GREEN, Fore.RED, Fore.YELLOW, Fore.CYAN, Style.RESET_ALL, Style.BRIGHT
    )
except ImportError:
    GREEN = RED = YELLOW = CYAN = RESET = BOLD = ""

from .core import FirmaKernel
from . import __version__


def banner():
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════╗
║         FIRMA INTELIGENCIA  —  KERNEL EMPRESARIAL v{__version__}        ║
║              Sistema de control de acceso (RBAC)                 ║
║                   CEO = ROOT  |  VM-ready                        ║
╚══════════════════════════════════════════════════════════════════╝{RESET}
""")


def run_cli():
    banner()
    k = FirmaKernel()
    print(f"  Kernel v{__version__} | Empresa: {k.config.get('empresa')}")
    print(f"  Roles cargados: {len(k.roles.roles)}")
    print()

    while True:
        if not k.usuario:
            print(f"{YELLOW}─ Login requerido (o 'salir'){RESET}")
            user = input("  Usuario: ").strip()
            if user.lower() in ("salir", "exit", "q"):
                print("  Kernel detenido.")
                break
            try:
                pwd = getpass.getpass("  Contraseña: ")
            except Exception:
                pwd = input("  Contraseña: ")
            ok, msg = k.login(user, pwd)
            if ok:
                print(f"\n  {GREEN}✓ Bienvenido, {k.usuario.nombre_completo}{RESET}")
                print(f"  Roles: {', '.join(k.usuario.roles)}")
                if k.es_ceo():
                    print(f"  {BOLD}★ MODO CEO — acceso total{RESET}")
            else:
                print(f"  {RED}✗ {msg}{RESET}")
            continue

        print(f"\n{CYAN}─ {k.usuario.username} | {k.usuario.roles}{RESET}")
        print("  info | roles | users | check | crear | passwd | logout | salir")
        cmd = input("  > ").strip().lower()

        if cmd in ("salir", "exit", "q"):
            k.logout()
            print("  Sesión cerrada. Kernel detenido.")
            break
        elif cmd == "logout":
            k.logout()
            print("  Sesión cerrada.")
        elif cmd == "info":
            for key, val in k.info().items():
                print(f"  {key}: {val}")
        elif cmd == "roles":
            print(f"\n  {'ID':<25} {'Nivel':<6} Nombre")
            print("  " + "─" * 55)
            for r in k.roles.listar():
                print(f"  {r.id:<25} {r.nivel:<6} {r.nombre}")
        elif cmd == "users":
            try:
                for u in k.listar_usuarios():
                    st = "ACTIVO" if u.activo else "INACTIVO"
                    print(f"  • {u.username:<16} {u.nombre_completo:<28} {u.roles} [{st}]")
            except PermissionError as e:
                print(f"  {RED}✗ {e}{RESET}")
        elif cmd.startswith("check"):
            parts = cmd.split()
            if len(parts) >= 3:
                area, accion = parts[1], parts[2]
                clasif = parts[3] if len(parts) > 3 else "INTERNO"
                ok = k.check(area, accion, clasif)
                mark = f"{GREEN}✓ PERMITIDO" if ok else f"{RED}✗ DENEGADO"
                print(f"  {mark}{RESET}: {accion} en {area} ({clasif})")
            else:
                print("  Uso: check <area> <accion> [clasificacion]")
        elif cmd == "crear":
            try:
                uname = input("    username: ").strip()
                nombre = input("    nombre: ").strip()
                email = input("    email: ").strip()
                roles = [r.strip() for r in input("    roles (coma): ").split(",") if r.strip()]
                pwd = getpass.getpass("    password: ")
                ok, msg = k.crear_usuario(uname, nombre, email, roles, pwd)
                print(f"  {GREEN if ok else RED}{'✓' if ok else '✗'} {msg}{RESET}")
            except PermissionError as e:
                print(f"  {RED}✗ {e}{RESET}")
        elif cmd == "passwd":
            target = input("    username (Enter = vos): ").strip() or k.usuario.username
            pwd = getpass.getpass("    nueva contraseña: ")
            ok, msg = k.cambiar_password(target, pwd)
            print(f"  {GREEN if ok else RED}{'✓' if ok else '✗'} {msg}{RESET}")
        else:
            print("  Comando no reconocido.")
