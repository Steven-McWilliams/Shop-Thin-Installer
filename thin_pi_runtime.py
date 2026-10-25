#!/usr/bin/env python3
"""
Thin Pi runtime (customer-flash image)

- Multi-scanner input (USB hub + multiple dongles)
- Optional GPIO feedback (LED/buzzer)
- Local admin mapping UI (shop_dashboard.py /admin)
- Local LAN discovery so a local server can see and approve the device without manual IP entry
- Cloud v2 forwarding (thin_mode) with offline queue + local archive

This intentionally avoids running the full legacy Pi stack (api_server, bin manager UI, etc.).
"""

from __future__ import annotations

import json
import os
import platform
import signal
import socket
import sys
import threading
import time
import uuid
from pathlib import Path

DISCOVERY_BEACON_COUNT = 0
DISCOVERY_LAST_BROADCAST = 0.0


def _env_int(name: str, default: int) -> int:
    try:
        return int((os.environ.get(name) or "").strip() or default)
    except Exception:
        return default


def _load_config() -> dict:
    config_path = os.environ.get("INNOSAW_CONFIG_PATH", "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _is_paired_config() -> bool:
    cfg = _load_config()
    if not isinstance(cfg, dict):
        return False

    if cfg.get("paired_cloud_shop_id") or cfg.get("paired_at"):
        return True

    station_tokens = cfg.get("station_tokens")
    if isinstance(station_tokens, dict) and station_tokens:
        return True

    cloud_cfg = cfg.get("cloud_v2")
    if isinstance(cloud_cfg, dict):
        station_tokens = cloud_cfg.get("station_tokens")
        if isinstance(station_tokens, dict) and station_tokens:
            return True

    return False


def _get_device_identity() -> dict:
    hostname = platform.node() or "innosaw-pi"
    mac = None
    try:
        node = uuid.getnode()
        if node:
            mac = ":".join(f"{(node >> (8 * i)) & 0xFF:02x}" for i in range(5, -1, -1))
    except Exception:
        mac = None
    lan_ip = ""
    try:
        tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tmp.connect(("8.8.8.8", 80))
        lan_ip = tmp.getsockname()[0]
        tmp.close()
    except Exception:
        lan_ip = ""

    paired = _is_paired_config()
    return {
        "device_id": hostname,
        "hostname": hostname,
        "mac": mac,
        "product": "thin-pi",
        "version": os.environ.get("INNOSAW_VERSION", "unknown"),
        "kind": "thin-pi-discovery",
        "state": "ready" if paired else "discovery",
        "discovery_mode": not paired,
        "ip": lan_ip,
    }


def _broadcast_discovery_loop(stop_event: threading.Event, interval_seconds: int = 10, window_seconds: int = 600) -> None:
    global DISCOVERY_BEACON_COUNT, DISCOVERY_LAST_BROADCAST
    port = _env_int("INNOSAW_DISCOVERY_PORT", 5011)
    deadline = time.time() + max(1, window_seconds)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(1.0)
    payload = _get_device_identity()
    payload["kind"] = "thin-pi-discovery"
    payload["state"] = "ready" if _is_paired_config() else "discovery"
    payload["discovery_mode"] = not _is_paired_config()
    try:
        while not stop_event.is_set() and time.time() < deadline:
            payload = _get_device_identity()
            payload["kind"] = "thin-pi-discovery"
            payload["state"] = "ready" if _is_paired_config() else "discovery"
            payload["discovery_mode"] = not _is_paired_config()
            if payload["discovery_mode"] is False:
                break
            payload["sent_at"] = time.time()
            try:
                sock.sendto(json.dumps(payload).encode("utf-8"), ("<broadcast>", port))
                DISCOVERY_BEACON_COUNT += 1
                DISCOVERY_LAST_BROADCAST = time.time()
            except OSError:
                pass
            for _ in range(max(1, interval_seconds)):
                if stop_event.is_set():
                    break
                time.sleep(1)
    finally:
        sock.close()


def main() -> int:
    # Ensure repo root is on sys.path so imports work when installed via sparse checkout.
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))

    # Import late so sys.path is ready
    from multi_scanner_manager import MultiScannerManager
    import shop_dashboard

    config_path = os.environ.get("INNOSAW_CONFIG_PATH", "config.json")
    bind_host = os.environ.get("INNOSAW_DASHBOARD_HOST", "0.0.0.0")
    bind_port = _env_int("INNOSAW_DASHBOARD_PORT", 5006)

    mgr = MultiScannerManager(config_file=config_path)
    mgr.load_scanners()
    mgr.start_all()

    # Attach to dashboard so /api/scanner/restart/<path> works and runtime status is visible
    shop_dashboard.app.scanner_manager = mgr

    stop_event = threading.Event()

    def _handle_signal(_sig, _frame):
        stop_event.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    discovery_thread = None
    try:
        paired = _is_paired_config()
        if not paired and os.environ.get("INNOSAW_DISCOVERY_DISABLE", "0").strip().lower() not in {"1", "true", "yes"}:
            discovery_thread = threading.Thread(
                target=_broadcast_discovery_loop,
                args=(stop_event,),
                name="thin-pi-discovery",
                daemon=True,
            )
            discovery_thread.start()

        # Run the dashboard (blocking) in main thread.
        # Flask dev server is OK for LAN admin mapping; keep it single-process to share mgr instance.
        shop_dashboard.app.run(host=bind_host, port=bind_port, debug=False)
    finally:
        stop_event.set()
        if discovery_thread is not None:
            discovery_thread.join(timeout=2.0)
        try:
            mgr.stop_all()
        except Exception:
            pass

    # If we ever get here, wait briefly for threads to stop.
    t0 = time.time()
    while time.time() - t0 < 2.0 and not stop_event.is_set():
        time.sleep(0.1)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


