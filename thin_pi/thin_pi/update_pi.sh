#!/usr/bin/env bash
set -euo pipefail

# Repeatable Thin Pi update routine.
# Usage:
#   sudo bash thin_pi/update_pi.sh
#
# This script is intentionally simple and idempotent so the update button and
# manual SSH commands can both run the same supported sequence.

INSTALL_DIR="${INSTALL_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
BRANCH="${BRANCH:-${INNOSAW_BRANCH:-main}}"
REMOTE="${REMOTE:-origin}"
SERVICE_NAME="${SERVICE_NAME:-innosaw-thin}"
SERVICE_ALTERNATE="${SERVICE_ALTERNATE:-innosaw-thin.service}"

if [[ ! -d "${INSTALL_DIR}/.git" ]]; then
  echo "Repository not found at ${INSTALL_DIR}"
  exit 1
fi

cd "${INSTALL_DIR}"

echo "[1/4] Fetching latest code from ${REMOTE}/${BRANCH}"
git fetch --all --prune
if git rev-parse --verify "${BRANCH}" >/dev/null 2>&1; then
  git checkout "${BRANCH}"
else
  git checkout -b "${BRANCH}" "${REMOTE}/${BRANCH}" 2>/dev/null || git checkout -
fi
git pull --ff-only "${REMOTE}" "${BRANCH}"

echo "[2/4] Updating Python dependencies"
if [[ -x "${INSTALL_DIR}/.venv/bin/python" ]]; then
  "${INSTALL_DIR}/.venv/bin/python" -m pip install --upgrade pip >/dev/null 2>&1 || true
  if [[ -f "${INSTALL_DIR}/thin_pi/requirements.txt" ]]; then
    "${INSTALL_DIR}/.venv/bin/pip" install -r "${INSTALL_DIR}/thin_pi/requirements.txt"
  fi
fi

echo "[3/4] Restarting Thin Pi service"
sudo systemctl daemon-reload || true
if sudo systemctl restart "${SERVICE_NAME}" >/dev/null 2>&1; then
  echo "Restarted ${SERVICE_NAME}"
else
  sudo systemctl restart "${SERVICE_ALTERNATE}" >/dev/null 2>&1 || true
  echo "Fallback restart attempted for ${SERVICE_ALTERNATE}"
fi

echo "[4/4] Verifying service"
if sudo systemctl is-active --quiet "${SERVICE_NAME}"; then
  sudo systemctl status "${SERVICE_NAME}" --no-pager -l || true
elif sudo systemctl is-active --quiet "${SERVICE_ALTERNATE}"; then
  sudo systemctl status "${SERVICE_ALTERNATE}" --no-pager -l || true
else
  echo "Warning: service did not report active after restart. Check sudo systemctl status ${SERVICE_NAME} --no-pager"
fi

echo "Thin Pi update finished."
