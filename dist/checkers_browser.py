import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import subprocess

from checkers import AI, BLACK, BOARD_SIZE, Game, RED


_game = Game()


def new_game():
    """Reset the browser game's state."""
    _game.reset()


def _coordinate(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer.")
    if not 0 <= value < BOARD_SIZE:
        raise ValueError(f"{name} must be between 0 and {BOARD_SIZE - 1}.")


def player_move(start_row, start_column, destination_row, destination_column):
    """Apply one human step, returning False when the move is not legal."""
    _coordinate(start_row, "Start row")
    _coordinate(start_column, "Start column")
    _coordinate(destination_row, "Destination row")
    _coordinate(destination_column, "Destination column")
    if _game.game_over or _game.turn != RED:
        return False
    return _game.play_step(
        (start_row, start_column), (destination_row, destination_column)
    )[0]


def computer_move():
    """Choose and apply the existing Python AI's complete turn."""
    if _game.game_over or _game.turn != BLACK:
        return False
    move = AI.choose_move(_game.board)
    if move is None or not _game.play_ai_move(move):
        raise RuntimeError("The computer could not make a move in a non-terminal game.")
    return True


def get_game_state():
    """Return the current game state as JSON for the browser interface."""
    counts = _game.board.piece_counts()
    state = {
        "board": [
            [
                None if piece is None else {"color": piece.color, "king": piece.king}
                for piece in row
            ]
            for row in _game.board.squares
        ],
        "turn": _game.turn,
        "winner": _game.winner,
        "is_draw": _game.is_draw,
        "game_over": _game.game_over,
        "forced_piece": _game.forced_piece,
        "legal_moves": [
            {
                "start": move.start,
                "path": move.path,
                "captures": move.captures,
            }
            for move in _game.legal_moves()
        ],
        "last_move": None
        if _game.last_move is None
        else {
            "start": _game.last_move.start,
            "path": _game.last_move.path,
            "captures": _game.last_move.captures,
        },
        "last_captured": _game.last_captured,
        "piece_counts": {RED: counts[0], BLACK: counts[1]},
    }
    return json.dumps(state)


def main():
    """Serve the browser game locally and open it in Google Chrome."""
    game_directory = Path(__file__).resolve().parent
    page_file = game_directory / "checkers.html"
    if not page_file.is_file():
        raise FileNotFoundError(f"Could not find the Checkers page: {page_file}")

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

    handler = partial(SimpleHTTPRequestHandler, directory=str(game_directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    game_url = f"http://127.0.0.1:{server.server_port}/checkers.html"

    try:
        subprocess.Popen([chrome_path, game_url], close_fds=True)
        print(f"Checkers opened in Chrome: {game_url}")
        print("Leave this window open while playing. Press Ctrl+C to stop the local server.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCheckers server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
