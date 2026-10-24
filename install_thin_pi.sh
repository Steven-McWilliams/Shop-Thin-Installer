#!/usr/bin/env bash
set -euo pipefail

# Public bootstrap installer for the Thin Pi.
# This script intentionally lives in a public repo so a brand-new Pi can fetch it
# anonymously via raw.githubusercontent.com.
#
# Then it authenticates to the private app repo using APP_REPO_URL and/or
# GITHUB_TOKEN if those are provided.
#
# Example:
#   curl -fsSL https://raw.githubusercontent.com/your-public-thin-repo/main/install_thin_pi.sh -o install_thin_pi.sh
#   sudo bash install_thin_pi.sh
#
# Optional overrides:
#   export APP_REPO_URL="https://github.com/Steven-McWilliams/Shop.git"
#   export APP_REPO_BRANCH="main"
#   export GITHUB_TOKEN="ghp_your_token"
#
# If the app repo is private, the token is required.

PI_USER="${SUDO_USER:-pi}"
INSTALL_DIR="/home/${PI_USER}/qr-system"
APP_REPO_URL="${APP_REPO_URL:-https://github.com/Steven-McWilliams/Shop.git}"
APP_REPO_BRANCH="${APP_REPO_BRANCH:-main}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
SERVICE_NAME="innosaw-thin"

if [[ "${GITHUB_TOKEN}" != "" && "${APP_REPO_URL}" == https://github.com/* ]]; then
  APP_REPO_URL="https://x-access-token:${GITHUB_TOKEN}@github.com/${APP_REPO_URL#https://github.com/}"
fi

echo "[1/6] Installing required packages"
apt-get update -y
apt-get install -y git python3 python3-venv python3-pip python3-dev build-essential rpi.gpio-common

mkdir -p "${INSTALL_DIR}"
chown -R "${PI_USER}:${PI_USER}" "${INSTALL_DIR}"

if [[ ! -d "${INSTALL_DIR}/.git" ]]; then
  echo "[2/6] Cloning app repo into ${INSTALL_DIR}"
  sudo -u "${PI_USER}" bash -lc "
    cd \"${INSTALL_DIR}\"
    git clone --depth 1 --branch \"${APP_REPO_BRANCH}\" \"${APP_REPO_URL}\" .
  "
else
  echo "[2/6] Repo already exists, updating"
  sudo -u "${PI_USER}" bash -lc "
    cd \"${INSTALL_DIR}\"
    git fetch --all --prune
    git checkout \"${APP_REPO_BRANCH}\" || git checkout -b \"${APP_REPO_BRANCH}\" origin/\"${APP_REPO_BRANCH}\"
    git pull --ff-only origin \"${APP_REPO_BRANCH}\"
  "
fi

if [[ ! -f "${INSTALL_DIR}/thin_pi/requirements.txt" ]]; then
  echo "Expected file not found: ${INSTALL_DIR}/thin_pi/requirements.txt"
  echo "Check APP_REPO_URL and APP_REPO_BRANCH."
  exit 1
fi

echo "[3/6] Creating Python venv and installing dependencies"
sudo -u "${PI_USER}" bash -lc "
  cd \"${INSTALL_DIR}\"
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r thin_pi/requirements.txt
"

echo "[4/6] Creating default config if missing"
if [[ ! -f "${INSTALL_DIR}/config.json" && -f "${INSTALL_DIR}/config.example.json" ]]; then
  cp "${INSTALL_DIR}/config.example.json" "${INSTALL_DIR}/config.json"
  chown "${PI_USER}:${PI_USER}" "${INSTALL_DIR}/config.json"
fi

echo "[5/6] Copying Thin Pi systemd service"
if [[ -f "${INSTALL_DIR}/thin_pi/innosaw-thin.service" ]]; then
  cp "${INSTALL_DIR}/thin_pi/innosaw-thin.service" "/etc/systemd/system/${SERVICE_NAME}.service"
  sed -i "s|User=pi|User=${PI_USER}|g" "/etc/systemd/system/${SERVICE_NAME}.service"
  sed -i "s|Group=pi|Group=${PI_USER}|g" "/etc/systemd/system/${SERVICE_NAME}.service"
  sed -i "s|WorkingDirectory=/home/pi/qr-system|WorkingDirectory=${INSTALL_DIR}|g" "/etc/systemd/system/${SERVICE_NAME}.service"
  sed -i "s|ExecStart=/home/pi/qr-system/.venv/bin/python /home/pi/qr-system/thin_pi/thin_pi_runtime.py|ExecStart=${INSTALL_DIR}/.venv/bin/python ${INSTALL_DIR}/thin_pi/thin_pi_runtime.py|g" "/etc/systemd/system/${SERVICE_NAME}.service"
  systemctl daemon-reload
  systemctl enable "${SERVICE_NAME}.service" || true
  systemctl restart "${SERVICE_NAME}.service"
fi

echo "[6/6] Thin Pi bootstrap complete"
echo ""
echo "Service status: sudo systemctl status ${SERVICE_NAME} --no-pager"
echo "Admin UI: http://<pi-ip>:5006/admin"
echo ""
echo "If you are using a private repo, set APP_REPO_URL and GITHUB_TOKEN before deployment."
