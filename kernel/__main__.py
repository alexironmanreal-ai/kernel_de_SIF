# -*- coding: utf-8 -*-
"""Punto de entrada: python -m kernel [cli|serve|status]"""
from __future__ import annotations
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="firma-kernel",
        description="Firma Inteligencia — Kernel Empresarial v3.0",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="cli",
        choices=["cli", "serve", "status"],
        help="cli = consola interactiva | serve = API HTTP | status = estado",
    )
    parser.add_argument("--host", default=None, help="Host API (default config)")
    parser.add_argument("--port", type=int, default=None, help="Puerto API")
    args = parser.parse_args()

    if args.mode == "cli":
        from .cli import run_cli
        run_cli()
        return

    if args.mode == "status":
        from .core import FirmaKernel
        from . import __version__
        k = FirmaKernel()
        print(f"Kernel v{__version__}")
        print(f"Empresa: {k.config.get('empresa')}")
        print(f"Roles: {len(k.roles.roles)}")
        print(f"Usuarios: {len(k.db.listar_usuarios())}")
        print(f"DB: {k.root / 'data' / 'firma_kernel.db'}")
        print("Estado: OK")
        return

    if args.mode == "serve":
        try:
            import uvicorn
        except ImportError:
            print("Falta uvicorn. Instalá: pip install uvicorn fastapi")
            sys.exit(1)
        from .core import FirmaKernel
        k = FirmaKernel()
        host = args.host or k.config.get("api", {}).get("host", "0.0.0.0")
        port = args.port or k.config.get("api", {}).get("port", 8741)
        print(f"Iniciando API Kernel en http://{host}:{port}")
        print("Health: GET /health")
        print("Login:  POST /auth/login")
        uvicorn.run(
            "kernel.api:app",
            host=host,
            port=port,
            log_level="info",
            reload=False,
        )


if __name__ == "__main__":
    main()
