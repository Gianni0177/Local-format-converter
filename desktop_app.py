from __future__ import annotations

import base64
import os
from pathlib import Path
import subprocess
import threading
import sys

import webview
from werkzeug.serving import make_server

from app import add_app_log, app, pick_port


class ServerThread(threading.Thread):
    def __init__(self, host: str, port: int):
        super().__init__(daemon=True)
        self._server = make_server(host, port, app)

    def run(self) -> None:
        self._server.serve_forever()

    def shutdown(self) -> None:
        self._server.shutdown()


class DesktopBridge:
    def __init__(self) -> None:
        self._download_dir = Path.home() / "Downloads" / "FormatForge"
        self._download_dir.mkdir(parents=True, exist_ok=True)

    def _safe_filename(self, suggested_name: str) -> str:
        cleaned = Path(suggested_name).name.strip()
        return cleaned or "converted_file"

    def _unique_path(self, filename: str) -> Path:
        target = self._download_dir / filename
        if not target.exists():
            return target

        stem = target.stem
        suffix = target.suffix
        for idx in range(1, 1000):
            candidate = self._download_dir / f"{stem} ({idx}){suffix}"
            if not candidate.exists():
                return candidate
        return target

    def save_converted_file(self, base64_payload: str, suggested_name: str) -> str:
        file_name = self._safe_filename(suggested_name)
        target_path = self._unique_path(file_name)
        target_path.write_bytes(base64.b64decode(base64_payload.encode("utf-8")))
        add_app_log("ok", f"File salvato: {target_path}")
        return str(target_path)

    def locate_file(self, path_text: str) -> bool:
        target = Path(path_text)
        if not target.exists():
            add_app_log("error", f"File non trovato: {target}")
            return False

        if os.name == "nt":
            subprocess.Popen(["explorer", "/select,", str(target)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target.parent)])
        return True


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    preferred_port = int(os.getenv("PORT", "5000"))
    app_title = os.getenv("APP_WINDOW_TITLE", "Format Forge Desktop")

    selected_port = pick_port(host, preferred_port)
    if selected_port != preferred_port:
        add_app_log("info", f"Porta {preferred_port} non disponibile. Uso {selected_port}.")

    server = ServerThread(host, selected_port)
    server.start()

    bridge = DesktopBridge()
    url = f"http://{host}:{selected_port}?desktop=1"
    add_app_log("info", f"Desktop app avviata su {url}")
    webview.create_window(app_title, url, js_api=bridge, min_size=(1000, 680))

    try:
        webview.start(debug=False)
    finally:
        add_app_log("info", "Desktop app in chiusura")
        server.shutdown()


if __name__ == "__main__":
    main()
