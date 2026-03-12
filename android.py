from __future__ import annotations
import json
import logging
import os
import sys
import threading
import time
import asyncio as _asyncio
from pathlib import Path
from typing import Dict, Optional

# Import the core proxy logic
import proxy.tg_ws_proxy as tg_ws_proxy

# --- Configuration ---
APP_NAME = "TgWsProxy"
# On Android, we save config in the home directory
APP_DIR = Path.home() / APP_NAME
CONFIG_FILE = APP_DIR / "config.json"

DEFAULT_CONFIG = {
    "port": 1080,
    "host": "127.0.0.1",
    "dc_ip": ["2:149.154.167.220", "4:149.154.167.220"],
    "verbose": False,
}

_proxy_thread: Optional[threading.Thread] = None
_async_stop: Optional[object] = None
_config: dict = {}

log = logging.getLogger("tg-ws-android")

def _ensure_dirs():
    APP_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> dict:
    _ensure_dirs()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                data.setdefault(k, v)
            return data
        except Exception as exc:
            log.warning("Failed to load config: %s", exc)
    return dict(DEFAULT_CONFIG)

def setup_logging(verbose: bool = False):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if verbose else logging.INFO)
    # Log to console only for Android
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG if verbose else logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"))
    root.addHandler(ch)

def _run_proxy_thread(port: int, dc_opt: Dict[int, str], verbose: bool, host: str = '127.0.0.1'):
    global _async_stop
    loop = _asyncio.new_event_loop()
    _asyncio.set_event_loop(loop)
    stop_ev = _asyncio.Event()
    _async_stop = (loop, stop_ev)
    try:
        loop.run_until_complete(tg_ws_proxy._run(port, dc_opt, stop_event=stop_ev, host=host))
    except Exception as exc:
        log.error("Proxy thread crashed: %s", exc)
    finally:
        loop.close()
        _async_stop = None

def start_proxy():
    global _proxy_thread, _config
    if _proxy_thread and _proxy_thread.is_alive():
        log.info("Proxy already running")
        return

    cfg = _config
    port = cfg.get("port", DEFAULT_CONFIG["port"])
    host = cfg.get("host", DEFAULT_CONFIG["host"])
    dc_ip_list = cfg.get("dc_ip", DEFAULT_CONFIG["dc_ip"])
    verbose = cfg.get("verbose", False)

    try:
        dc_opt = tg_ws_proxy.parse_dc_ip_list(dc_ip_list)
    except ValueError as e:
        log.error("Bad config dc_ip: %s", e)
        return

    log.info("Starting proxy on %s:%d ...", host, port)
    _proxy_thread = threading.Thread(target=_run_proxy_thread, args=(port, dc_opt, verbose, host), daemon=True, name="proxy")
    _proxy_thread.start()
    
    # Print clear instructions for the user
    print("\n" + "="*40)
    print(f"Proxy is running!")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print("Configure Telegram with these settings.")
    print("="*40 + "\n")

def main():
    global _config
    _config = load_config()
    setup_logging(_config.get("verbose", False))
    
    log.info("Starting Android TG WS Proxy...")
    
    start_proxy()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")

if __name__ == "__main__":
    main()
