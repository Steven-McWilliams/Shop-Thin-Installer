#!/usr/bin/env python3
"""
Minimal Thin Pi runtime.

This file is intentionally lightweight and kept in the public bootstrap repo so a
fresh Pi can install and run the thin-layer service without depending on the
private app repo.
"""

from __future__ import annotations

import os
import signal
import sys
import threading
import time
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    try:
        return int((os.environ.get(name) or "").strip() or default)
    except Exception:
        return default


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(repo_root))

    config_path = os.environ.get("INNOSAW_CONFIG_PATH", "config.json")
    bind_host = os.environ.get("INNOSAW_DASHBOARD_HOST", "0.0.0.0")
    bind_port = _env_int("INNOSAW_DASHBOARD_PORT", 5006)

    print(f"Thin Pi runtime starting on {bind_host}:{bind_port}")
    print(f"Using config: {config_path}")

    stop_event = threading.Event()

    def _handle_signal(_sig, _frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    # Minimal placeholder runtime keeps the service alive for now.
    # The real Thin Pi can be expanded in the public bootstrap repo as needed.
    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
