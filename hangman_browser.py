import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import subprocess
from threading import RLock

from hangman import MAX_WRONG_GUESSES, choose_word, reveal_word


_game_lock = RLock()
_game = {}


def new_game():
    """Start a round using the desktop game's shared word list."""
    global _game
    _game = {
        "secret_word": choose_word(),
        "guessed_letters": set(),
        "wrong_guesses": 0,
        "finished": False,
        "status": "Guess a letter to reveal the word.",
        "status_kind": "info",
    }
    return get_game_state()


def submit_guess(guess):
    """Apply one letter guess or quit command and return the public game state."""
    if not isinstance(guess, str):
        raise TypeError("Guess must be text.")
    normalized_guess = guess.strip().upper()

    with _game_lock:
        if not _game:
            new_game()
        if _game["finished"]:
            return get_game_state()

        if normalized_guess == "QUIT":
            _game["finished"] = True
            _game["status"] = f"You quit! The word was {_game['secret_word']}."
            _game["status_kind"] = "muted"
            return get_game_state()
        if len(normalized_guess) != 1 or not "A" <= normalized_guess <= "Z":
            raise ValueError("Enter one letter from A to Z, or type QUIT to reveal the word.")
        if normalized_guess in _game["guessed_letters"]:
            _game["status"] = f"You already guessed {normalized_guess}. Try another letter."
            _game["status_kind"] = "muted"
            return get_game_state()

        _game["guessed_letters"].add(normalized_guess)
        if normalized_guess in _game["secret_word"]:
            _game["status"] = f"Correct! {normalized_guess} is in the word."
            _game["status_kind"] = "success"
        else:
            _game["wrong_guesses"] += 1
            _game["status"] = f"{normalized_guess} is not in the word."
            _game["status_kind"] = "error"

        if set(_game["secret_word"]).issubset(_game["guessed_letters"]):
            _game["finished"] = True
            _game["status"] = f"You won! The word was {_game['secret_word']}."
            _game["status_kind"] = "success"
        elif _game["wrong_guesses"] >= MAX_WRONG_GUESSES:
            _game["finished"] = True
            _game["status"] = f"Game over! The word was {_game['secret_word']}."
            _game["status_kind"] = "error"
        return get_game_state()


def get_game_state():
    """Return public round state without disclosing an unfinished secret word."""
    if not _game:
        return {
            "word_display": "",
            "guessed_letters": [],
            "wrong_guesses": 0,
            "max_wrong_guesses": MAX_WRONG_GUESSES,
            "finished": False,
            "status": "Loading game...",
            "status_kind": "info",
        }

    reveal_all = _game["finished"] and not set(_game["secret_word"]).issubset(
        _game["guessed_letters"]
    )
    letters = (
        set(_game["secret_word"]) if reveal_all else _game["guessed_letters"]
    )
    state = {
        "word_display": reveal_word(_game["secret_word"], letters),
        "guessed_letters": sorted(_game["guessed_letters"]),
        "correct_letters": sorted(
            _game["guessed_letters"] & set(_game["secret_word"])
        ),
        "wrong_guesses": _game["wrong_guesses"],
        "max_wrong_guesses": MAX_WRONG_GUESSES,
        "finished": _game["finished"],
        "status": _game["status"],
        "status_kind": _game["status_kind"],
    }
    return state


class HangmanRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/state":
            with _game_lock:
                self._send_json(get_game_state())
            return
        super().do_GET()

    def do_POST(self):
        if self.path not in ("/api/new", "/api/guess"):
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
                if self.path == "/api/new":
                    state = new_game()
                else:
                    state = submit_guess(payload.get("guess"))
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
    page_file = game_directory / "hangman.html"
    if not page_file.is_file():
        raise FileNotFoundError(f"Could not find the Hangman page: {page_file}")

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

    handler = partial(HangmanRequestHandler, directory=str(game_directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    game_url = f"http://127.0.0.1:{server.server_port}/hangman.html"

    try:
        subprocess.Popen([chrome_path, game_url], close_fds=True)
        print(f"Hangman opened in Chrome: {game_url}")
        print("Leave this window open while playing. Press Ctrl+C to stop the local server.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nHangman server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
