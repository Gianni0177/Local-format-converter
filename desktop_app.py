from __future__ import annotations

import os
import threading

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


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    preferred_port = int(os.getenv("PORT", "5000"))
    app_title = os.getenv("APP_WINDOW_TITLE", "Format Forge Desktop")

    selected_port = pick_port(host, preferred_port)
    if selected_port != preferred_port:
        add_app_log("info", f"Porta {preferred_port} non disponibile. Uso {selected_port}.")

    server = ServerThread(host, selected_port)
    server.start()

    url = f"http://{host}:{selected_port}?desktop=1"
    add_app_log("info", f"Desktop app avviata su {url}")
    webview.create_window(app_title, url, min_size=(1000, 680))

    try:
        webview.start(debug=False)
    finally:
        add_app_log("info", "Desktop app in chiusura")
        server.shutdown()


if __name__ == "__main__":
    main()
