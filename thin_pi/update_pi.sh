#!/usr/bin/env bash
set -euo pipefail

# Compatibility wrapper:
# older docs/use cases call thin_pi/update_pi.sh
# canonical update logic lives at thin_pi/thin_pi/update_pi.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec sudo bash "${SCRIPT_DIR}/thin_pi/update_pi.sh" "$@"
