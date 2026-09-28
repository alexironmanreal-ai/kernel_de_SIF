#!/bin/bash
# Instalación del Kernel en VM Linux (Ubuntu/Debian/CentOS compatible)
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/firma_kernel}"
SERVICE_USER="${SERVICE_USER:-firma}"
PORT="${PORT:-8741}"

echo "════════════════════════════════════════════"
echo "  Firma Inteligencia Kernel — Instalador VM"
echo "════════════════════════════════════════════"

if [[ $EUID -ne 0 ]]; then
  echo "Ejecutá como root: sudo bash scripts/install_vm.sh"
  exit 1
fi

# Usuario del servicio
if ! id "$SERVICE_USER" &>/dev/null; then
  useradd --system --home "$INSTALL_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
  echo "✓ Usuario $SERVICE_USER creado"
fi

# Copiar
mkdir -p "$INSTALL_DIR"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KERNEL_SRC="$(cd "$SCRIPT_DIR/.." && pwd)"
rsync -a --exclude venv --exclude '__pycache__' --exclude '*.pyc' \
  "$KERNEL_SRC/" "$INSTALL_DIR/"

# venv + deps
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Permisos
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chmod 750 "$INSTALL_DIR"
chmod 700 "$INSTALL_DIR/data" "$INSTALL_DIR/logs"

# systemd
cp "$INSTALL_DIR/systemd/firma-kernel.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable firma-kernel
systemctl start firma-kernel

echo ""
echo "✓ Kernel instalado en $INSTALL_DIR"
echo "✓ Servicio: systemctl status firma-kernel"
echo "✓ API:      http://0.0.0.0:$PORT/health"
echo "✓ CLI:      sudo -u $SERVICE_USER $INSTALL_DIR/venv/bin/python -m kernel cli"
echo ""
echo "Login inicial: ceo / FirmaCEO2026!ChangeMe"
echo "CAMBIÁ LA CONTRASEÑA INMEDIATAMENTE."
