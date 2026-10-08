"""Serve the arcade homepage and the browser games that need a local API."""

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import subprocess
from threading import RLock
from urllib.parse import urlsplit

import hangman_browser
import mastermind_browser


_hangman_lock = RLock()
_mastermind_lock = RLock()
_HANGMAN_GET = {
    "/api/hangman/state": hangman_browser.get_game_state,
}
_HANGMAN_POST = {
    "/api/hangman/new": hangman_browser.new_game,
    "/api/hangman/guess": lambda payload: hangman_browser.submit_guess(
        payload.get("guess")
    ),
}
_MASTERMIND_GET = {
    "/api/mastermind/state": mastermind_browser.get_game_state,
}
_MASTERMIND_POST = {
    "/api/mastermind/new": mastermind_browser.new_game,
    "/api/mastermind/clear": mastermind_browser.clear_guess,
    "/api/mastermind/remove": mastermind_browser.remove_pin,
    "/api/mastermind/submit": mastermind_browser.submit_guess,
    "/api/mastermind/pin": lambda payload: mastermind_browser.add_pin(
        payload.get("pin")
    ),
}


class ArcadeRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        action = _HANGMAN_GET.get(path)
        lock = _hangman_lock
        if action is None:
            action = _MASTERMIND_GET.get(path)
            lock = _mastermind_lock
        if action is None:
            super().do_GET()
            return
        with lock:
            self._send_json(action())

    def do_POST(self):
        path = urlsplit(self.path).path
        action = _HANGMAN_POST.get(path)
        lock = _hangman_lock
        if action is None:
            action = _MASTERMIND_POST.get(path)
            lock = _mastermind_lock
        if action is None:
            self.send_error(404, "Unknown arcade game action.")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json({"error": "Invalid request body length."}, 400)
            return
        if not 0 <= content_length <= 1024:
            self._send_json({"error": "Request body must be at most 1 KB."}, 413)
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json({"error": "Request body must contain valid JSON."}, 400)
            return
        if not isinstance(payload, dict):
            self._send_json({"error": "Request body must be a JSON object."}, 400)
            return

        try:
            with lock:
                if path in {"/api/hangman/guess", "/api/mastermind/pin"}:
                    state = action(payload)
                else:
                    state = action()
        except (TypeError, ValueError) as error:
            self._send_json({"error": str(error)}, 400)
            return
        self._send_json(state)

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def find_chrome():
    chrome_path = shutil.which("chrome")
    if chrome_path is not None:
        return chrome_path

    candidates = (
        Path(os.environ.get("PROGRAMFILES", ""))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", ""))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("LOCALAPPDATA", ""))
        / "Google/Chrome/Application/chrome.exe",
    )
    return next(
        (str(candidate) for candidate in candidates if candidate.is_file()),
        None,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    handler = partial(ArcadeRequestHandler, directory=str(root))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    homepage_url = f"http://{args.host}:{server.server_port}/arcade/"

    try:
        chrome_path = find_chrome()
        if chrome_path is not None:
            subprocess.Popen([chrome_path, homepage_url], close_fds=True)
            print(f"Little Arcade opened in Chrome: {homepage_url}")
        else:
            print(f"Open Little Arcade in your browser: {homepage_url}")
        print("Leave this window open while playing. Press Ctrl+C to stop the server.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nLittle Arcade server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
