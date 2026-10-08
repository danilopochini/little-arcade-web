import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import subprocess
from threading import RLock

from mastermind import CODE_LENGTH, MAX_TURNS, PALETTE, MastermindGame


_game_lock = RLock()
_game = MastermindGame()
_current_guess = []
_status = "Choose four colors to make your first guess."
_status_kind = "info"


def get_game_state():
    """Return JSON-safe round state without exposing the unfinished code."""
    state = {
        "palette": [
            {"name": name, "color": color}
            for name, color in PALETTE
        ],
        "code_length": CODE_LENGTH,
        "max_turns": MAX_TURNS,
        "guesses": [
            {
                "pins": list(guess),
                "feedback": {
                    "exact": feedback[0],
                    "color_only": feedback[1],
                },
            }
            for guess, feedback in zip(_game.guesses, _game.feedback)
        ],
        "current_guess": list(_current_guess),
        "turn": len(_game.guesses) + 1,
        "finished": _game.finished,
        "won": _game.won,
        "status": _status,
        "status_kind": _status_kind,
        "secret": list(_game.secret) if _game.finished else None,
    }
    return state


def new_game():
    """Start a fresh round."""
    global _current_guess, _status, _status_kind
    _game.new_game()
    _current_guess = []
    _status = "Choose four colors to make your first guess."
    _status_kind = "info"
    return get_game_state()


def add_pin(pin):
    """Add one palette color to the current guess."""
    global _status, _status_kind
    if isinstance(pin, bool) or not isinstance(pin, int):
        raise TypeError("Color selection must be an integer.")
    if not 0 <= pin < len(PALETTE):
        raise ValueError(f"Choose a color from 1 to {len(PALETTE)}.")
    if _game.finished:
        _status = "Start a new game to play again."
        _status_kind = "muted"
    elif len(_current_guess) >= CODE_LENGTH:
        _status = "Your guess already has four pegs. Submit it or clear it."
        _status_kind = "muted"
    else:
        _current_guess.append(pin)
        _status = f"{len(_current_guess)} of {CODE_LENGTH} pegs selected."
        _status_kind = "info"
    return get_game_state()


def clear_guess():
    """Clear the unsubmitted guess."""
    global _current_guess, _status, _status_kind
    if not _game.finished:
        _current_guess = []
        _status = "Guess cleared. Choose four colors."
        _status_kind = "info"
    return get_game_state()


def remove_pin():
    """Remove the last color selected for the unsubmitted guess."""
    global _status, _status_kind
    if not _game.finished and _current_guess:
        _current_guess.pop()
        _status = "Last peg removed."
        _status_kind = "info"
    return get_game_state()


def submit_guess():
    """Submit the current code and update status from the shared game engine."""
    global _current_guess, _status, _status_kind
    if _game.finished:
        _status = "Start a new game to play again."
        _status_kind = "muted"
        return get_game_state()
    if len(_current_guess) != CODE_LENGTH:
        missing = CODE_LENGTH - len(_current_guess)
        _status = f"Choose {missing} more peg{'s' if missing != 1 else ''} before submitting."
        _status_kind = "error"
        return get_game_state()

    result, feedback = _game.submit_guess(_current_guess)
    _current_guess = []
    if result == "won":
        _status = "Code cracked! You win — click New Game to play again."
        _status_kind = "success"
    elif result == "lost":
        secret = "  ".join(PALETTE[pin][0] for pin in _game.secret)
        _status = f"Out of guesses! The code was {secret}."
        _status_kind = "error"
    else:
        exact, color_only = feedback
        _status = (
            f"{exact} exact match{'es' if exact != 1 else ''}, "
            f"{color_only} right color{'s' if color_only != 1 else ''} in another spot."
        )
        _status_kind = "info"
    return get_game_state()


class MastermindRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/state":
            with _game_lock:
                self._send_json(get_game_state())
            return
        super().do_GET()

    def do_POST(self):
        actions = {
            "/api/new": new_game,
            "/api/clear": clear_guess,
            "/api/remove": remove_pin,
            "/api/submit": submit_guess,
        }
        action = actions.get(self.path)
        if self.path != "/api/pin" and action is None:
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
                state = add_pin(payload.get("pin")) if self.path == "/api/pin" else action()
        except (TypeError, ValueError) as error:
            self._send_json({"error": str(error)}, 400)
            return
        self._send_json(state)

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
    page_file = game_directory / "mastermind.html"
    if not page_file.is_file():
        raise FileNotFoundError(f"Could not find the Mastermind page: {page_file}")

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

    handler = partial(MastermindRequestHandler, directory=str(game_directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    game_url = f"http://127.0.0.1:{server.server_port}/mastermind.html"

    try:
        subprocess.Popen([chrome_path, game_url], close_fds=True)
        print(f"Mastermind opened in Chrome: {game_url}")
        print("Leave this window open while playing. Press Ctrl+C to stop the local server.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMastermind server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
