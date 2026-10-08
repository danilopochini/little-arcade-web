import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import subprocess

import chess

from chess_game import ChessAI


BOARD_SIZE = 8
_board = chess.Board()
_ai = ChessAI()
_last_move = None


def new_game():
    """Reset the browser game's board and computer opponent."""
    global _board, _last_move
    _board = chess.Board()
    _last_move = None
    _ai.transposition_table.clear()


def player_move(from_square, to_square, promotion="q"):
    """Apply a legal white move; promote pawns to the selected piece."""
    global _last_move
    if not isinstance(from_square, str) or not isinstance(to_square, str):
        raise TypeError("Square names must be strings.")
    if promotion not in ("q", "r", "b", "n"):
        raise ValueError("Promotion must be queen, rook, bishop, or knight.")
    if _board.is_game_over(claim_draw=True) or _board.turn != chess.WHITE:
        return False

    try:
        move = chess.Move.from_uci(
            from_square + to_square
            + (promotion if _board.piece_type_at(chess.parse_square(from_square)) == chess.PAWN
               and chess.square_rank(chess.parse_square(to_square)) in (0, 7)
               else "")
        )
    except ValueError:
        return False
    if not _board.is_legal(move):
        return False
    _board.push(move)
    _last_move = move
    return True


def computer_move():
    """Choose and apply the existing Python AI's black move."""
    global _last_move
    if _board.is_game_over(claim_draw=True) or _board.turn != chess.BLACK:
        return False
    move = _ai.choose_move(_board)
    if move is None or not _board.is_legal(move):
        raise RuntimeError("The computer could not make a move in a non-terminal game.")
    _board.push(move)
    _last_move = move
    return True


def get_game_state():
    """Return the current board and legal moves as JSON for the browser."""
    pieces = []
    for rank in range(BOARD_SIZE - 1, -1, -1):
        row = []
        for file_index in range(BOARD_SIZE):
            piece = _board.piece_at(chess.square(file_index, rank))
            row.append(
                None
                if piece is None
                else {
                    "color": "white" if piece.color == chess.WHITE else "black",
                    "type": chess.piece_name(piece.piece_type),
                    "symbol": piece.unicode_symbol(),
                }
            )
        pieces.append(row)

    legal_moves = [
        {
            "from": chess.square_name(move.from_square),
            "to": chess.square_name(move.to_square),
            "promotion": chess.piece_name(move.promotion) if move.promotion else None,
            "capture": _board.is_capture(move),
            "san": _board.san(move),
        }
        for move in _board.legal_moves
    ]
    outcome = _board.outcome(claim_draw=True)
    state = {
        "board": pieces,
        "turn": "white" if _board.turn == chess.WHITE else "black",
        "is_check": _board.is_check(),
        "checked_king": chess.square_name(_board.king(_board.turn))
        if _board.is_check()
        else None,
        "game_over": outcome is not None,
        "winner": None
        if outcome is None or outcome.winner is None
        else "white" if outcome.winner == chess.WHITE else "black",
        "termination": outcome.termination.name.replace("_", " ").title()
        if outcome is not None
        else None,
        "legal_moves": legal_moves,
        "last_move": _last_move.uci() if _last_move is not None else None,
        "piece_counts": {
            "white": len(_board.pieces(chess.PAWN, chess.WHITE))
            + len(_board.pieces(chess.KNIGHT, chess.WHITE))
            + len(_board.pieces(chess.BISHOP, chess.WHITE))
            + len(_board.pieces(chess.ROOK, chess.WHITE))
            + len(_board.pieces(chess.QUEEN, chess.WHITE))
            + len(_board.pieces(chess.KING, chess.WHITE)),
            "black": len(_board.pieces(chess.PAWN, chess.BLACK))
            + len(_board.pieces(chess.KNIGHT, chess.BLACK))
            + len(_board.pieces(chess.BISHOP, chess.BLACK))
            + len(_board.pieces(chess.ROOK, chess.BLACK))
            + len(_board.pieces(chess.QUEEN, chess.BLACK))
            + len(_board.pieces(chess.KING, chess.BLACK)),
        },
    }
    return json.dumps(state)


def main():
    """Serve the browser game locally and open it in Google Chrome."""
    game_directory = Path(__file__).resolve().parent
    page_file = game_directory / "chess.html"
    if not page_file.is_file():
        raise FileNotFoundError(f"Could not find the Chess page: {page_file}")

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
    game_url = f"http://127.0.0.1:{server.server_port}/chess.html"

    try:
        subprocess.Popen([chrome_path, game_url], close_fds=True)
        print(f"Chess opened in Chrome: {game_url}")
        print("Leave this window open while playing. Press Ctrl+C to stop the local server.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nChess server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
