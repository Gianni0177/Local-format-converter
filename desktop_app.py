from __future__ import annotations

import ctypes
import os
import threading

import webview
from werkzeug.serving import make_server

from app import app, pick_port

SW_HIDE = 0
SW_SHOW = 5


def _console_hwnd() -> int:
    if os.name != "nt":
        return 0
    return ctypes.windll.kernel32.GetConsoleWindow()


def _show_console(visible: bool) -> None:
    hwnd = _console_hwnd()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW if visible else SW_HIDE)


class ConsoleApi:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.visible = False

    def toggle_console(self) -> bool:
        with self._lock:
            self.visible = not self.visible
            _show_console(self.visible)
            return self.visible


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
    selected_port = pick_port(host, preferred_port)

    if selected_port != preferred_port:
        print(f"Porta {preferred_port} non disponibile. Avvio su {selected_port}.")

    _show_console(False)

    server = ServerThread(host, selected_port)
    server.start()

    api = ConsoleApi()
    url = f"http://{host}:{selected_port}"
    window = webview.create_window(
        "Format Forge",
        url,
        js_api=api,
        min_size=(1000, 680),
    )

    def bind_shortcut() -> None:
        window.evaluate_js(
            """
            window.addEventListener('keydown', function (event) {
              if (event.ctrlKey && event.key === '\\\\') {
                event.preventDefault();
                if (window.pywebview && window.pywebview.api) {
                  window.pywebview.api.toggle_console();
                }
              }
            });
            """
        )

    window.events.loaded += bind_shortcut

    try:
        webview.start(debug=False)
    finally:
        server.shutdown()


if __name__ == "__main__":
    main()
