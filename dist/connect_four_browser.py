import json
import math


ROWS = 6
COLUMNS = 7
EMPTY = 0
HUMAN = 1
COMPUTER = 2
CONNECT = 4
SEARCH_DEPTH = 5


class ConnectFourGame:
    """Connect Four rules and a depth-limited minimax opponent."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[EMPTY for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.turn = HUMAN
        self.winner = EMPTY
        self.winning_cells = []
        self.is_draw = False

    def valid_columns(self, board=None):
        board = self.board if board is None else board
        return [column for column in range(COLUMNS) if board[0][column] == EMPTY]

    def drop_piece(self, column, piece):
        """Drop a piece into a column; return its row, or None if the move is invalid."""
        if column not in self.valid_columns():
            return None

        for row in range(ROWS - 1, -1, -1):
            if self.board[row][column] == EMPTY:
                self.board[row][column] = piece
                return row
        return None

    @staticmethod
    def winning_line(board, piece, last_move=None):
        """Return the four connected cells, checking horizontal, vertical, and both diagonals."""
        directions = ((0, 1), (1, 0), (1, 1), (1, -1))

        if last_move is not None:
            candidates = [last_move]
        else:
            candidates = [
                (row, column)
                for row in range(ROWS)
                for column in range(COLUMNS)
                if board[row][column] == piece
            ]

        for row, column in candidates:
            for row_step, column_step in directions:
                line = [(row, column)]
                for sign in (-1, 1):
                    next_row = row + sign * row_step
                    next_column = column + sign * column_step
                    while (
                        0 <= next_row < ROWS
                        and 0 <= next_column < COLUMNS
                        and board[next_row][next_column] == piece
                    ):
                        line.append((next_row, next_column))
                        next_row += sign * row_step
                        next_column += sign * column_step

                if len(line) >= CONNECT:
                    return line[:CONNECT]
        return []

    def play(self, column):
        """Apply the current player's move and update the round outcome."""
        if self.winner or self.is_draw:
            return False

        row = self.drop_piece(column, self.turn)
        if row is None:
            return False

        self.winning_cells = self.winning_line(self.board, self.turn, (row, column))
        if self.winning_cells:
            self.winner = self.turn
        elif not self.valid_columns():
            self.is_draw = True
        else:
            self.turn = COMPUTER if self.turn == HUMAN else HUMAN
        return True

    @classmethod
    def winning_moves(cls, board, piece):
        moves = []
        for column in cls.ordered_columns(board):
            row = next((r for r in range(ROWS - 1, -1, -1) if board[r][column] == EMPTY), None)
            if row is None:
                continue
            board[row][column] = piece
            if cls.winning_line(board, piece, (row, column)):
                moves.append(column)
            board[row][column] = EMPTY
        return moves

    @staticmethod
    def ordered_columns(board):
        available = [column for column in range(COLUMNS) if board[0][column] == EMPTY]
        center = COLUMNS // 2
        return sorted(available, key=lambda column: abs(column - center))

    @staticmethod
    def score_window(window, piece):
        opponent = HUMAN if piece == COMPUTER else COMPUTER
        own_count = window.count(piece)
        opponent_count = window.count(opponent)
        empty_count = window.count(EMPTY)

        if own_count == 4:
            return 100_000
        if own_count == 3 and empty_count == 1:
            return 120
        if own_count == 2 and empty_count == 2:
            return 12
        if opponent_count == 3 and empty_count == 1:
            return -150
        return 0

    @classmethod
    def evaluate(cls, board, piece):
        score = 0

        # Center columns give pieces more ways to connect in four directions.
        center_column = [board[row][COLUMNS // 2] for row in range(ROWS)]
        score += center_column.count(piece) * 8

        # Score every possible four-cell segment for immediate threats and setups.
        for row in range(ROWS):
            for column in range(COLUMNS - 3):
                window = [board[row][column + offset] for offset in range(CONNECT)]
                score += cls.score_window(window, piece)

        for row in range(ROWS - 3):
            for column in range(COLUMNS):
                window = [board[row + offset][column] for offset in range(CONNECT)]
                score += cls.score_window(window, piece)

        for row in range(ROWS - 3):
            for column in range(COLUMNS - 3):
                window = [board[row + offset][column + offset] for offset in range(CONNECT)]
                score += cls.score_window(window, piece)

        for row in range(3, ROWS):
            for column in range(COLUMNS - 3):
                window = [board[row - offset][column + offset] for offset in range(CONNECT)]
                score += cls.score_window(window, piece)

        return score

    @classmethod
    def minimax(cls, board, depth, alpha, beta, maximizing):
        valid_columns = cls.ordered_columns(board)
        computer_wins = cls.winning_line(board, COMPUTER)
        human_wins = cls.winning_line(board, HUMAN)

        if computer_wins:
            return None, 1_000_000 + depth
        if human_wins:
            return None, -1_000_000 - depth
        if depth == 0 or not valid_columns:
            return None, cls.evaluate(board, COMPUTER)

        if maximizing:
            best_score = -math.inf
            best_column = valid_columns[0]
            # Center-first ordering improves alpha-beta pruning and favors stronger positions.
            for column in valid_columns:
                row = next(r for r in range(ROWS - 1, -1, -1) if board[r][column] == EMPTY)
                board[row][column] = COMPUTER
                _, score = cls.minimax(board, depth - 1, alpha, beta, False)
                board[row][column] = EMPTY
                if score > best_score:
                    best_score, best_column = score, column
                alpha = max(alpha, best_score)
                if alpha >= beta:
                    break
            return best_column, best_score

        best_score = math.inf
        best_column = valid_columns[0]
        for column in valid_columns:
            row = next(r for r in range(ROWS - 1, -1, -1) if board[r][column] == EMPTY)
            board[row][column] = HUMAN
            _, score = cls.minimax(board, depth - 1, alpha, beta, True)
            board[row][column] = EMPTY
            if score < best_score:
                best_score, best_column = score, column
            beta = min(beta, best_score)
            if alpha >= beta:
                break
        return best_column, best_score

    def choose_computer_move(self):
        available = self.ordered_columns(self.board)
        if not available:
            return None

        # Win immediately when possible; otherwise stop the human's immediate win.
        winning = self.winning_moves(self.board, COMPUTER)
        if winning:
            return winning[0]
        blocking = self.winning_moves(self.board, HUMAN)
        if blocking:
            return blocking[0]

        column, _ = self.minimax(self.board, SEARCH_DEPTH, -math.inf, math.inf, True)
        return column


_game = ConnectFourGame()


def new_game():
    """Reset the browser game's state."""
    _game.reset()


def player_move(column):
    """Apply one human move, returning False when the move cannot be played."""
    if isinstance(column, bool) or not isinstance(column, int):
        raise TypeError("Column must be an integer.")
    if not 0 <= column < COLUMNS:
        raise ValueError(f"Column must be between 0 and {COLUMNS - 1}.")
    if _game.turn != HUMAN or _game.winner or _game.is_draw:
        return False
    return _game.play(column)


def computer_move():
    """Choose and apply the existing Python AI's move."""
    if _game.turn != COMPUTER or _game.winner or _game.is_draw:
        return False

    column = _game.choose_computer_move()
    if column is None or not _game.play(column):
        raise RuntimeError("The computer could not make a move in a non-terminal game.")
    return True


def get_board():
    """Return the current board as JSON for the browser interface."""
    return json.dumps(_game.board)


def get_game_status():
    """Return turn and outcome information as JSON for the browser interface."""
    status = {
        "turn": _game.turn,
        "winner": _game.winner,
        "is_draw": _game.is_draw,
        "winning_cells": _game.winning_cells,
        "valid_columns": _game.valid_columns(),
    }
    return json.dumps(status)


def main():
    """Serve the browser game locally and open it in Google Chrome."""
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    import os
    from pathlib import Path
    import shutil
    import subprocess

    game_directory = Path(__file__).resolve().parent
    index_file = game_directory / "index.html"
    if not index_file.is_file():
        raise FileNotFoundError(f"Could not find the game page: {index_file}")

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
    game_url = f"http://127.0.0.1:{server.server_port}/index.html"

    try:
        subprocess.Popen([chrome_path, game_url], close_fds=True)
        print(f"Connect Four opened in Chrome: {game_url}")
        print("Leave this window open while playing. Press Ctrl+C to stop the local server.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nConnect Four server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
