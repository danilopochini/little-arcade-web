import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import subprocess
from threading import RLock

from mens_erger_je_niet import MensErgerJeNietGame


_game_lock = RLock()
_game = MensErgerJeNietGame()


class MensErgerJeNietRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/state":
            with _game_lock:
                self._send_json(_game.get_state())
            return
        super().do_GET()

    def do_POST(self):
        actions = {
            "/api/new": self._new_game,
            "/api/roll": self._roll,
            "/api/move": self._move,
            "/api/computer": self._computer_turn,
        }
        action = actions.get(self.path)
        if action is None:
            self.send_error(404, "Unknown game action.")
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
            with _game_lock:
                state = action(payload)
        except (TypeError, ValueError) as error:
            self._send_json({"error": str(error)}, 400)
            return
        self._send_json(state)

    def _new_game(self, _payload):
        _game.new_game()
        return _game.get_state()

    def _roll(self, _payload):
        if _game.current_player != 0:
            raise ValueError("Wait for the computer players to finish their turns.")
        return _game.roll_die()

    def _move(self, payload):
        if _game.current_player != 0:
            raise ValueError("It is not your turn.")
        return _game.move_pawn(payload.get("pawn"))

    def _computer_turn(self, _payload):
        return _game.computer_turn()

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main():
    """Serve the browser game locally and open it in Google Chrome."""
    game_directory = Path(__file__).resolve().parent
    page_file = game_directory / "mens_erger_je_niet.html"
    if not page_file.is_file():
        raise FileNotFoundError(f"Could not find the game page: {page_file}")

    chrome_path = shutil.which("chrome")
    if chrome_path is None:
        chrome_candidates = (
            Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
            Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
        )
        chrome_path = next(
            (str(candidate) for candidate in chrome_candidates if candidate.is_file()),
            None,
        )
    if chrome_path is None:
        raise FileNotFoundError(
            "Google Chrome was not found. Install Chrome or add chrome.exe to PATH."
        )

    handler = partial(
        MensErgerJeNietRequestHandler,
        directory=str(game_directory),
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    game_url = f"http://127.0.0.1:{server.server_port}/mens_erger_je_niet.html"

    try:
        subprocess.Popen([chrome_path, game_url], close_fds=True)
        print(f"Mens erger je niet opened in Chrome: {game_url}")
        print("Leave this window open while playing. Press Ctrl+C to stop the local server.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMens erger je niet server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
