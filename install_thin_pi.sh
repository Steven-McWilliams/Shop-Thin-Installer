#!/usr/bin/env bash
set -euo pipefail

# Minimal public Thin Pi bootstrap installer.
# This script intentionally lives in a public repo and does not depend on a private
# app repo during first-time setup.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Steven-McWilliams/Shop-Thin-Installer/main/install_thin_pi.sh -o install_thin_pi.sh
#   sudo bash install_thin_pi.sh

PI_USER="${SUDO_USER:-pi}"
INSTALL_DIR="/home/${PI_USER}/qr-system"
SERVICE_NAME="innosaw-thin"
REPO_BASE="https://raw.githubusercontent.com/Steven-McWilliams/Shop-Thin-Installer/main"

# A raw file download only contains this script. Fetch the runtime files from the
# public repo explicitly so this works on a fresh Raspberry Pi without a git clone.

echo "[1/5] Installing required packages"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip python3-dev build-essential rpi.gpio-common git

mkdir -p "${INSTALL_DIR}"
chown -R "${PI_USER}:${PI_USER}" "${INSTALL_DIR}"

for file in thin_pi_runtime.py requirements.txt innosaw-thin.service config.example.json; do
  final_path="${INSTALL_DIR}/${file}"
  echo "Downloading ${file}"
  curl -fsSL "${REPO_BASE}/${file}" -o "${final_path}"
done

chown -R "${PI_USER}:${PI_USER}" "${INSTALL_DIR}"

echo "[2/5] Creating Python venv and installing dependencies"
sudo -u "${PI_USER}" bash -lc "
  cd \"${INSTALL_DIR}\"
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
"

if [[ ! -f "${INSTALL_DIR}/config.json" && -f "${INSTALL_DIR}/config.example.json" ]]; then
  cp "${INSTALL_DIR}/config.example.json" "${INSTALL_DIR}/config.json"
  chown "${PI_USER}:${PI_USER}" "${INSTALL_DIR}/config.json"
fi

echo "[3/5] Installing systemd service"
cp "${INSTALL_DIR}/innosaw-thin.service" "/etc/systemd/system/${SERVICE_NAME}.service"
sed -i "s|User=pi|User=${PI_USER}|g" "/etc/systemd/system/${SERVICE_NAME}.service"
sed -i "s|Group=pi|Group=${PI_USER}|g" "/etc/systemd/system/${SERVICE_NAME}.service"
sed -i "s|WorkingDirectory=/home/pi/qr-system|WorkingDirectory=${INSTALL_DIR}|g" "/etc/systemd/system/${SERVICE_NAME}.service"
sed -i "s|ExecStart=/home/pi/qr-system/.venv/bin/python /home/pi/qr-system/thin_pi/thin_pi_runtime.py|ExecStart=${INSTALL_DIR}/.venv/bin/python ${INSTALL_DIR}/thin_pi_runtime.py|g" "/etc/systemd/system/${SERVICE_NAME}.service"

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}.service" || true
systemctl restart "${SERVICE_NAME}.service"

echo "[4/5] Thin Pi bootstrap complete"
echo ""
echo "Service status: sudo systemctl status ${SERVICE_NAME} --no-pager"
echo "Admin UI: http://<pi-ip>:5006/admin"
echo ""
echo "This public repo intentionally contains only the minimal Thin Pi install/runtime files and no private app dependency."
