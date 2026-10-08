import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import subprocess
from threading import RLock

from ganzenbord import GanzenbordGame


_game_lock = RLock()
_game = GanzenbordGame()


class GanzenbordRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/state":
            with _game_lock:
                self._send_json(_game.get_state())
            return
        super().do_GET()

    def do_POST(self):
        actions = {
            "/api/roll": self._roll_dice,
            "/api/finish": self._finish_animation,
            "/api/skip": self._skip_turn,
            "/api/computer": self._computer_turn,
        }
        if self.path == "/api/new":
            action = self._new_game
        else:
            action = actions.get(self.path)
        if action is None:
            self.send_error(404, "Onbekende spelactie.")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json({"error": "Ongeldige lengte van het verzoek."}, 400)
            return
        if not 0 <= content_length <= 1024:
            self._send_json({"error": "Het verzoek mag maximaal 1 KB groot zijn."}, 413)
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json({"error": "Het verzoek bevat geen geldige JSON."}, 400)
            return
        if not isinstance(payload, dict):
            self._send_json({"error": "Het verzoek moet een JSON-object zijn."}, 400)
            return

        try:
            with _game_lock:
                state = action(payload)
        except (TypeError, ValueError) as error:
            self._send_json({"error": str(error)}, 400)
            return
        self._send_json(state)

    def _new_game(self, payload):
        player_count = payload.get("players", 2)
        _game.new_game(player_count)
        return _game.get_state()

    def _roll_dice(self, _payload):
        if _game.current_player != 0:
            raise ValueError("Wacht tot jij aan de beurt bent.")
        return _game.roll_dice()

    def _finish_animation(self, _payload):
        return _game.finish_animation()

    def _skip_turn(self, _payload):
        return _game.skip_turn()

    def _computer_turn(self, _payload):
        return _game.computer_turn()

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main():
    """Start the local Ganzenbord server and open it in Google Chrome."""
    game_directory = Path(__file__).resolve().parent
    page_file = game_directory / "ganzenbord.html"
    if not page_file.is_file():
        raise FileNotFoundError(f"Het spelbestand is niet gevonden: {page_file}")

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
            "Google Chrome is niet gevonden. Installeer Chrome of voeg chrome.exe toe aan PATH."
        )

    handler = partial(GanzenbordRequestHandler, directory=str(game_directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    game_url = f"http://127.0.0.1:{server.server_port}/ganzenbord.html"

    try:
        subprocess.Popen([chrome_path, game_url], close_fds=True)
        print(f"Ganzenbord is geopend in Chrome: {game_url}")
        print("Laat dit venster open tijdens het spelen. Druk op Ctrl+C om de server te stoppen.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nGanzenbord-server gestopt.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
