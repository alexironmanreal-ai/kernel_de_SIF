#!/bin/bash
# ─────────────────────────────────────────────────────────────
# Firma Inteligencia — Launcher del Kernel Empresarial
# ─────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KERNEL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export PYTHONPATH="$KERNEL_ROOT:$PYTHONPATH"
cd "$KERNEL_ROOT"

echo "Iniciando Firma Inteligencia Kernel v3.0..."
echo "Directorio: $KERNEL_ROOT"
echo ""

python3 -m kernel "$@"
