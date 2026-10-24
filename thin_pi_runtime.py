#!/usr/bin/env python3
"""Minimal public Thin Pi runtime with a working admin page."""

from __future__ import annotations

import json
import os
import signal
import sys
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, render_template_string


def _env_int(name: str, default: int) -> int:
    try:
        return int((os.environ.get(name) or "").strip() or default)
    except Exception:
        return default


def _load_config(config_path: str) -> dict:
    path = Path(config_path)
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    @app.get("/admin")
    def admin_page():
        return render_template_string(
            """
            <!doctype html>
            <html lang="en">
            <head>
              <meta charset="utf-8">
              <meta name="viewport" content="width=device-width, initial-scale=1">
              <title>Innosaw Thin Pi</title>
              <style>
                body { font-family: Arial, sans-serif; background: #101820; color: #eaf2ff; margin: 0; padding: 40px; }
                .card { max-width: 760px; margin: 0 auto; background: #1b2733; border-radius: 16px; padding: 32px; box-shadow: 0 12px 32px rgba(0,0,0,0.25); }
                h1 { margin-top: 0; }
                .ok { color: #7be495; }
                .meta { color: #c8d9f0; line-height: 1.7; }
                code { background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; }
              </style>
            </head>
            <body>
              <div class="card">
                <h1>Innosaw Thin Pi</h1>
                <p class="ok">Service is running.</p>
                <div class="meta">
                  <p><strong>Mode:</strong> Local thin admin runtime</p>
                  <p><strong>Health:</strong> <code>/healthz</code></p>
                  <p><strong>Config:</strong> <code>config.json</code></p>
                </div>
              </div>
            </body>
            </html>
            """
        )

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok", "service": "innosaw-thin"})

    return app


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    sys.path.insert(0, str(repo_root))

    config_path = os.environ.get("INNOSAW_CONFIG_PATH", str(repo_root / "config.json"))
    config = _load_config(config_path)
    bind_host = os.environ.get("INNOSAW_DASHBOARD_HOST") or config.get("network", {}).get("host") or "0.0.0.0"
    bind_port = _env_int("INNOSAW_DASHBOARD_PORT", int(config.get("network", {}).get("port", 5006)))

    print(f"Thin Pi runtime starting on {bind_host}:{bind_port}")
    print(f"Using config: {config_path}")

    app = create_app()
    stop_event = threading.Event()

    def _handle_signal(_sig, _frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    try:
        app.run(host=bind_host, port=bind_port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
