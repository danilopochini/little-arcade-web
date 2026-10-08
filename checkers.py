from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass
from typing import Optional


BOARD_SIZE = 8
RED = "red"
BLACK = "black"
EMPTY = None
SEARCH_DEPTH = 4
DRAW_NO_PROGRESS_LIMIT = 80
SQUARE_SIZE = 70
BOARD_MARGIN = 32


@dataclass
class Piece:
    color: str
    king: bool = False

    def copy(self) -> Piece:
        return Piece(self.color, self.king)


@dataclass(frozen=True)
class Move:
    start: tuple[int, int]
    path: tuple[tuple[int, int], ...]
    captures: tuple[tuple[int, int], ...] = ()


class Board:
    """Board state and legal move generation, independent of the interface."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.squares: list[list[Optional[Piece]]] = [
            [EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)
        ]
        for row in range(3):
            for column in range(BOARD_SIZE):
                if self.is_playable(row, column):
                    self.squares[row][column] = Piece(BLACK)
        for row in range(5, BOARD_SIZE):
            for column in range(BOARD_SIZE):
                if self.is_playable(row, column):
                    self.squares[row][column] = Piece(RED)

    @staticmethod
    def is_playable(row: int, column: int) -> bool:
        return (row + column) % 2 == 1

    def copy(self) -> Board:
        new_board = Board.__new__(Board)
        new_board.squares = [
            [piece.copy() if piece is not None else EMPTY for piece in row]
            for row in self.squares
        ]
        return new_board

    @staticmethod
    def inside(row: int, column: int) -> bool:
        return 0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE

    @staticmethod
    def forward_directions(piece: Piece) -> tuple[int, ...]:
        if piece.king:
            return (-1, 1)
        return (-1,) if piece.color == RED else (1,)

    def _captures_from(
        self,
        start: tuple[int, int],
        position: tuple[int, int],
        piece: Piece,
        path: tuple[tuple[int, int], ...],
        captures: tuple[tuple[int, int], ...],
    ) -> list[Move]:
        """Recursively enumerate complete jump sequences for one piece.

        The board is temporarily updated during recursion so a captured piece
        cannot be jumped twice and the moving piece can continue from each landing.
        Promotion ends a turn, matching the standard rule for a man reaching its
        king row during a capture sequence.
        """
        row, column = position
        found: list[Move] = []
        for row_step in self.forward_directions(piece):
            for column_step in (-1, 1):
                middle = (row + row_step, column + column_step)
                landing = (row + 2 * row_step, column + 2 * column_step)
                if not self.inside(*landing) or not self.is_playable(*landing):
                    continue
                middle_piece = self.squares[middle[0]][middle[1]]
                if (
                    middle_piece is None
                    or middle_piece.color == piece.color
                    or self.squares[landing[0]][landing[1]] is not None
                ):
                    continue

                self.squares[row][column] = EMPTY
                self.squares[middle[0]][middle[1]] = EMPTY
                self.squares[landing[0]][landing[1]] = piece
                promotes = not piece.king and landing[0] == (0 if piece.color == RED else 7)
                was_king = piece.king
                if promotes:
                    piece.king = True

                next_path = path + (landing,)
                next_captures = captures + (middle,)
                if promotes:
                    found.append(Move(start, next_path, next_captures))
                else:
                    continuations = self._captures_from(
                        start, landing, piece, next_path, next_captures
                    )
                    if continuations:
                        found.extend(continuations)
                    else:
                        found.append(Move(start, next_path, next_captures))

                piece.king = was_king
                self.squares[landing[0]][landing[1]] = EMPTY
                self.squares[middle[0]][middle[1]] = middle_piece
                self.squares[row][column] = piece
        return found

    def legal_moves(
        self, color: str, forced_piece: Optional[tuple[int, int]] = None
    ) -> list[Move]:
        """Generate legal full-turn moves; any available capture is mandatory."""
        captures: list[Move] = []
        pieces = (
            [forced_piece]
            if forced_piece is not None
            else [
                (row, column)
                for row in range(BOARD_SIZE)
                for column in range(BOARD_SIZE)
                if self.squares[row][column] is not None
                and self.squares[row][column].color == color
            ]
        )
        for position in pieces:
            row, column = position
            piece = self.squares[row][column]
            if piece is not None and piece.color == color:
                captures.extend(self._captures_from(position, position, piece, (), ()))
        if captures:
            return captures

        if forced_piece is not None:
            return []

        moves = []
        for row, column in pieces:
            piece = self.squares[row][column]
            if piece is None or piece.color != color:
                continue
            for row_step in self.forward_directions(piece):
                for column_step in (-1, 1):
                    destination = (row + row_step, column + column_step)
                    if (
                        self.inside(*destination)
                        and self.is_playable(*destination)
                        and self.squares[destination[0]][destination[1]] is None
                    ):
                        moves.append(Move((row, column), (destination,)))
        return moves

    def apply_move(self, move: Move):
        """Apply a complete turn move, including captures and king promotion."""
        start_row, start_column = move.start
        piece = self.squares[start_row][start_column]
        if piece is None:
            raise ValueError("Cannot move from an empty square.")
        self.squares[start_row][start_column] = EMPTY
        for index, destination in enumerate(move.path):
            if index < len(move.captures):
                captured_row, captured_column = move.captures[index]
                self.squares[captured_row][captured_column] = EMPTY
            row, _ = destination
            if row == (0 if piece.color == RED else BOARD_SIZE - 1):
                piece.king = True
        end_row, end_column = move.path[-1]
        self.squares[end_row][end_column] = piece

    def piece_counts(self) -> tuple[int, int]:
        red = sum(piece is not None and piece.color == RED for row in self.squares for piece in row)
        black = sum(piece is not None and piece.color == BLACK for row in self.squares for piece in row)
        return red, black

    def position_key(self, turn: str) -> tuple:
        layout = tuple(
            tuple(
                None if piece is None else (piece.color, piece.king)
                for piece in row
            )
            for row in self.squares
        )
        return turn, layout


class Game:
    """Turn management, move validation, captures, draws, and win detection."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.board = Board()
        self.turn = RED
        self.winner: Optional[str] = None
        self.is_draw = False
        self.forced_piece: Optional[tuple[int, int]] = None
        self.no_progress_plies = 0
        self.position_counts = {self.board.position_key(self.turn): 1}
        self.last_move: Optional[Move] = None
        self.last_captured: list[tuple[int, int]] = []
        self.active_move: Optional[Move] = None
        self.active_promoted = False

    @property
    def game_over(self) -> bool:
        return self.winner is not None or self.is_draw

    def legal_moves(self) -> list[Move]:
        if self.game_over:
            return []
        return self.board.legal_moves(self.turn, self.forced_piece)

    def play_step(
        self, start: tuple[int, int], destination: tuple[int, int]
    ) -> tuple[bool, bool]:
        """Play one square of a move; return (valid, turn_finished).

        A forced capture continuation keeps the same player active and locks the
        moved piece as the only possible source for the next click.
        """
        if self.game_over:
            return False, False
        choices = [
            move
            for move in self.legal_moves()
            if move.start == start and move.path and move.path[0] == destination
        ]
        if not choices:
            return False, False

        chosen = choices[0]
        piece = self.board.squares[start[0]][start[1]]
        if piece is None:
            return False, False
        was_king = piece.king
        is_capture = bool(chosen.captures)
        captured_square = chosen.captures[0] if is_capture else None

        self.board.squares[start[0]][start[1]] = EMPTY
        if captured_square is not None:
            self.board.squares[captured_square[0]][captured_square[1]] = EMPTY
            self.last_captured.append(captured_square)
        if destination[0] == (0 if piece.color == RED else BOARD_SIZE - 1):
            piece.king = True
        self.board.squares[destination[0]][destination[1]] = piece

        remaining_path = chosen.path[1:]
        if self.active_move is None:
            self.last_captured = [captured_square] if captured_square is not None else []
            self.active_promoted = False
            partial_move = Move(
                chosen.start,
                (destination,),
                (captured_square,) if captured_square is not None else (),
            )
        else:
            partial_move = Move(
                self.active_move.start,
                self.active_move.path + (destination,),
                self.active_move.captures
                + ((captured_square,) if captured_square is not None else ()),
            )
        promoted = not was_king and piece.king
        self.active_promoted = self.active_promoted or promoted
        self.active_move = partial_move

        if is_capture and remaining_path:
            self.forced_piece = destination
            self.last_move = partial_move
            return True, False

        # A legal generator returns only complete capture sequences. Reaching
        # here means the turn is complete, whether it was a jump or a quiet move.
        self.forced_piece = None
        completed_move = self.active_move
        if (completed_move is not None and completed_move.captures) or self.active_promoted:
            self.no_progress_plies = 0
        else:
            self.no_progress_plies += 1
        self.active_move = None
        self.active_promoted = False

        self.turn = BLACK if self.turn == RED else RED
        if not self.board.piece_counts()[0 if self.turn == RED else 1]:
            self.winner = BLACK if self.turn == RED else RED
        elif not self.board.legal_moves(self.turn):
            self.winner = BLACK if self.turn == RED else RED
        else:
            key = self.board.position_key(self.turn)
            self.position_counts[key] = self.position_counts.get(key, 0) + 1
            if (
                self.no_progress_plies >= DRAW_NO_PROGRESS_LIMIT
                or self.position_counts[key] >= 3
            ):
                self.is_draw = True

        self.last_move = completed_move
        return True, True

    def play_ai_move(self, move: Move):
        """Commit one computer full-turn move, preserving GUI game-state rules."""
        if self.game_over or self.turn != BLACK or move not in self.legal_moves():
            return False

        moving_piece = self.board.squares[move.start[0]][move.start[1]]
        if moving_piece is None:
            return False
        started_as_king = moving_piece.king
        promotes = not started_as_king and move.path[-1][0] == BOARD_SIZE - 1
        self.board.apply_move(move)
        self.last_move = move
        self.last_captured = list(move.captures)
        self.forced_piece = None
        if move.captures or promotes:
            self.no_progress_plies = 0
        else:
            self.no_progress_plies += 1

        self.turn = RED
        if not self.board.piece_counts()[0]:
            self.winner = BLACK
        elif not self.board.legal_moves(RED):
            self.winner = BLACK
        else:
            key = self.board.position_key(self.turn)
            self.position_counts[key] = self.position_counts.get(key, 0) + 1
            if (
                self.no_progress_plies >= DRAW_NO_PROGRESS_LIMIT
                or self.position_counts[key] >= 3
            ):
                self.is_draw = True
        return True


class AI:
    """Alpha-beta minimax opponent with material and positional evaluation."""

    @classmethod
    def evaluate(cls, board: Board) -> int:
        score = 0
        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                piece = board.squares[row][column]
                if piece is None:
                    continue
                sign = 1 if piece.color == BLACK else -1
                if piece.king:
                    value = 180
                else:
                    value = 100
                    progress = row if piece.color == BLACK else BOARD_SIZE - 1 - row
                    value += progress * 7
                center_bonus = int(3 - abs(3.5 - column))
                value += center_bonus * 4
                score += sign * value
        return score

    @classmethod
    def minimax(
        cls,
        board: Board,
        turn: str,
        depth: int,
        alpha: float,
        beta: float,
    ) -> tuple[Optional[Move], int]:
        moves = board.legal_moves(turn)
        if not moves:
            return None, -100_000 - depth if turn == BLACK else 100_000 + depth
        if depth == 0:
            return None, cls.evaluate(board)

        maximizing = turn == BLACK
        best_move = None
        best_score = -math.inf if maximizing else math.inf
        next_turn = RED if maximizing else BLACK

        # Captures and promotions first improve pruning and reward tactical moves.
        moves.sort(
            key=lambda move: (
                len(move.captures),
                board.squares[move.start[0]][move.start[1]].king is False
                and move.path[-1][0] == (7 if turn == BLACK else 0),
            ),
            reverse=True,
        )
        for move in moves:
            child = board.copy()
            child.apply_move(move)
            _, score = cls.minimax(child, next_turn, depth - 1, alpha, beta)
            if maximizing and score > best_score:
                best_move, best_score = move, score
                alpha = max(alpha, best_score)
            elif not maximizing and score < best_score:
                best_move, best_score = move, score
                beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_move, int(best_score)

    @classmethod
    def choose_move(cls, board: Board) -> Optional[Move]:
        move, _ = cls.minimax(
            board.copy(), BLACK, SEARCH_DEPTH, -math.inf, math.inf
        )
        return move


class CheckersGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Checkers")
        self.root.resizable(True, True)
        self.game = Game()
        self.selected: Optional[tuple[int, int]] = None
        self.ai_pending = False
        self.ai_job = None
        self.square_size = SQUARE_SIZE
        self.board_margin = BOARD_MARGIN
        self.board_left = BOARD_MARGIN
        self.board_top = BOARD_MARGIN
        self.display_square_size = SQUARE_SIZE

        self.colors = {
            "background": "#eee5d7",
            "panel": "#faf6ef",
            "light": "#e8d4b3",
            "dark": "#65402e",
            "wood": "#8f5e3d",
            "wood_light": "#b47c50",
            "red": "#c9363d",
            "red_light": "#f06b67",
            "black": "#24232b",
            "black_light": "#55515a",
            "selection": "#63e0bb",
            "destination": "#f4cf63",
            "last_move": "#fff0a8",
            "text": "#302820",
            "muted": "#827466",
        }
        self.status = tk.StringVar()
        self.red_count = tk.StringVar()
        self.black_count = tk.StringVar()
        self._build_widgets()
        self._fit_window_to_screen()
        self.new_game()

    def _build_widgets(self):
        outer = tk.Frame(self.root, bg=self.colors["background"], padx=24, pady=20)
        outer.pack(fill="both", expand=True)
        header = tk.Frame(outer, bg=self.colors["background"])
        header.pack(fill="x", pady=(0, 12))
        logo = tk.Canvas(
            header,
            width=38,
            height=38,
            bg=self.colors["background"],
            highlightthickness=0,
        )
        logo.pack(side="left", padx=(0, 10))
        logo.create_oval(11, 3, 33, 25, fill=self.colors["black"], outline="#fff5e8", width=1)
        logo.create_oval(4, 12, 26, 34, fill=self.colors["red"], outline="#fff5e8", width=1)
        title = tk.Frame(header, bg=self.colors["background"])
        title.pack(side="left")
        tk.Label(
            title,
            text="CHECKERS",
            font=("Georgia", 20, "bold"),
            fg=self.colors["text"],
            bg=self.colors["background"],
        ).pack(anchor="w")
        tk.Label(
            title,
            text="A CLASSIC GAME OF STRATEGY",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["background"],
        ).pack(anchor="w", pady=(1, 0))

        info = tk.Frame(outer, bg=self.colors["panel"], padx=12, pady=10)
        info.pack(fill="x", pady=(0, 12))
        self.status_dot = tk.Canvas(
            info, width=16, height=16, bg=self.colors["panel"], highlightthickness=0
        )
        self.status_dot.pack(side="left", padx=(0, 7))
        self.status_label = tk.Label(
            info,
            textvariable=self.status,
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
            anchor="w",
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        score = tk.Frame(outer, bg=self.colors["background"])
        score.pack(fill="x", pady=(0, 12))
        self._build_score_card(score, RED, "YOU", self.red_count).pack(
            side="left", fill="x", expand=True, padx=(0, 5)
        )
        self._build_score_card(score, BLACK, "COMPUTER", self.black_count).pack(
            side="left", fill="x", expand=True, padx=(5, 0)
        )

        size = BOARD_SIZE * self.square_size + 2 * self.board_margin
        self.canvas = tk.Canvas(
            outer,
            width=size,
            height=size,
            bg=self.colors["background"],
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        tk.Button(
            outer,
            text="New Game",
            command=self.new_game,
            font=("Segoe UI", 10, "bold"),
            bg=self.colors["wood"],
            fg="white",
            activebackground=self.colors["dark"],
            activeforeground="white",
            relief="flat",
            padx=22,
            pady=9,
            cursor="hand2",
        ).pack(pady=(13, 0))
        tk.Label(
            outer,
            text="Click a red piece, then choose a highlighted square  •  Captures are mandatory",
            font=("Segoe UI", 8),
            fg=self.colors["muted"],
            bg=self.colors["background"],
        ).pack(pady=(9, 0))

    def _fit_window_to_screen(self):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        requested_height = self.root.winfo_reqheight()
        fixed_height = requested_height - self.canvas.winfo_reqheight()
        available_height = max(400, screen_height - 60)
        self.board_margin = 24
        available_for_board = available_height - fixed_height - 2 * self.board_margin
        self.square_size = min(SQUARE_SIZE, max(40, available_for_board // BOARD_SIZE))
        self.canvas.configure(
            width=BOARD_SIZE * self.square_size + 2 * self.board_margin,
            height=BOARD_SIZE * self.square_size + 2 * self.board_margin,
        )
        self.root.update_idletasks()

        width = min(self.root.winfo_reqwidth(), screen_width - 40)
        height = min(self.root.winfo_reqheight(), available_height)
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _build_score_card(self, parent, color, label, count):
        card = tk.Frame(parent, bg=self.colors["panel"], padx=11, pady=8)
        swatch = self.colors[color]
        icon = tk.Canvas(
            card,
            width=24,
            height=24,
            bg=self.colors["panel"],
            highlightthickness=0,
        )
        icon.pack(side="left", padx=(0, 8))
        icon.create_oval(3, 3, 21, 21, fill=swatch, outline=self.colors["wood"], width=1)
        text = tk.Frame(card, bg=self.colors["panel"])
        text.pack(side="left", fill="x", expand=True)
        tk.Label(
            text,
            text=label,
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["panel"],
        ).pack(anchor="w")
        tk.Label(
            text,
            textvariable=count,
            font=("Georgia", 15, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
        ).pack(anchor="w")
        return card

    def new_game(self):
        if self.ai_job is not None:
            self.root.after_cancel(self.ai_job)
            self.ai_job = None
        self.game.reset()
        self.selected = None
        self.ai_pending = False
        self.update_labels()
        self.draw_board()

    def update_labels(self, message: Optional[str] = None):
        red_count, black_count = self.game.board.piece_counts()
        self.red_count.set(str(red_count))
        self.black_count.set(str(black_count))
        if message is not None:
            self.status.set(message)
            status_color = self.colors["wood"]
        elif self.game.game_over:
            if self.game.is_draw:
                self.status.set("Draw! Click New Game to play again.")
                status_color = self.colors["wood"]
            else:
                winner = "Red" if self.game.winner == RED else "Black"
                self.status.set(f"{winner} wins! Click New Game to play again.")
                status_color = self.colors[winner.lower()]
        elif self.ai_pending:
            self.status.set("Computer is thinking...")
            status_color = self.colors["black"]
        elif self.game.turn == RED:
            if self.game.forced_piece is not None:
                self.status.set("Continue capturing with the highlighted piece.")
                status_color = self.colors["red"]
            elif any(move.captures for move in self.game.legal_moves()):
                self.status.set("Your turn — a capture is mandatory.")
                status_color = self.colors["red"]
            else:
                self.status.set("Your turn — select a red piece.")
                status_color = self.colors["red"]
        else:
            self.status.set("Computer is thinking...")
            status_color = self.colors["black"]
        self.status_label.configure(fg=status_color)
        self.status_dot.delete("all")
        dot_color = (
            self.colors["red"]
            if not self.game.game_over and self.game.turn == RED
            else self.colors["black"]
            if not self.game.game_over
            else self.colors["wood"]
        )
        self.status_dot.create_oval(3, 3, 13, 13, fill=dot_color, outline="")

    def destinations(self) -> set[tuple[int, int]]:
        if self.selected is None or self.game.turn != RED:
            return set()
        return {
            move.path[0]
            for move in self.game.legal_moves()
            if move.start == self.selected and move.path
        }

    def draw_board(self):
        self.canvas.delete("all")
        legal_destinations = self.destinations()
        capture_destinations = {
            move.path[0]
            for move in self.game.legal_moves()
            if move.start == self.selected and move.captures
        }
        last_cells = set()
        if self.game.last_move is not None:
            last_cells.add(self.game.last_move.start)
            last_cells.update(self.game.last_move.path)
            last_cells.update(self.game.last_captured)

        canvas_width = max(self.canvas.winfo_width(), self.canvas.winfo_reqwidth())
        canvas_height = max(self.canvas.winfo_height(), self.canvas.winfo_reqheight())
        margin = min(self.board_margin, max(10, min(canvas_width, canvas_height) // 18))
        square = max(
            1,
            min(
                100,
                (canvas_width - 2 * margin) // BOARD_SIZE,
                (canvas_height - 2 * margin) // BOARD_SIZE,
            ),
        )
        board_left = (canvas_width - BOARD_SIZE * square) // 2
        board_top = (canvas_height - BOARD_SIZE * square) // 2
        self.display_square_size = square
        self.board_left = board_left
        self.board_top = board_top
        self.display_margin = margin
        board_right = board_left + BOARD_SIZE * square
        board_bottom = board_top + BOARD_SIZE * square
        self.canvas.create_rectangle(
            board_left - 8,
            board_top - 8,
            board_right + 8,
            board_bottom + 8,
            fill="#3f291e",
            outline="",
        )
        self.canvas.create_rectangle(
            board_left - 6,
            board_top - 6,
            board_right + 6,
            board_bottom + 6,
            fill=self.colors["wood"],
            outline=self.colors["wood_light"],
            width=2,
        )
        self.canvas.create_rectangle(
            board_left - 2,
            board_top - 2,
            board_right + 2,
            board_bottom + 2,
            outline="#d2a06e",
            width=1,
        )

        for column in range(BOARD_SIZE):
            x = board_left + column * square + square / 2
            self.canvas.create_text(
                x,
                board_top - 16,
                text=chr(ord("A") + column),
                fill="#f4dfc4",
                font=("Segoe UI", 8, "bold"),
            )
        for row in range(BOARD_SIZE):
            y = board_top + row * square + square / 2
            self.canvas.create_text(
                board_left - margin / 2,
                y,
                text=str(BOARD_SIZE - row),
                fill="#f4dfc4",
                font=("Segoe UI", 8, "bold"),
            )
            self.canvas.create_text(
                board_right + margin / 2,
                y,
                text=str(BOARD_SIZE - row),
                fill="#f4dfc4",
                font=("Segoe UI", 8, "bold"),
            )

        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                x1 = board_left + column * square
                y1 = board_top + row * square
                x2, y2 = x1 + square, y1 + square
                playable = Board.is_playable(row, column)
                square_color = self.colors["dark"] if playable else self.colors["light"]
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=square_color, outline=square_color
                )

                position = (row, column)
                if position in last_cells:
                    self.canvas.create_rectangle(
                        x1 + 3,
                        y1 + 3,
                        x2 - 3,
                        y2 - 3,
                        outline=self.colors["last_move"],
                        width=2,
                    )
                if position in legal_destinations:
                    if position in capture_destinations:
                        capture_inset = square * 0.11
                        self.canvas.create_oval(
                            x1 + capture_inset,
                            y1 + capture_inset,
                            x2 - capture_inset,
                            y2 - capture_inset,
                            outline=self.colors["destination"],
                            width=max(2, square * 0.055),
                        )
                    else:
                        dot_inset = square * 0.38
                        self.canvas.create_oval(
                            x1 + dot_inset,
                            y1 + dot_inset,
                            x2 - dot_inset,
                            y2 - dot_inset,
                            fill=self.colors["destination"],
                            outline="#fff0bd",
                            width=1,
                        )

                piece = self.game.board.squares[row][column]
                if piece is None:
                    continue
                selected = position == self.selected or position == self.game.forced_piece
                center_x = (x1 + x2) / 2
                center_y = (y1 + y2) / 2
                radius = square * 0.39
                piece_outline = max(2, square * 0.05) if selected else max(1, square * 0.025)
                rim = self.colors["wood_light"] if piece.color == RED else "#08080b"
                base = self.colors["red"] if piece.color == RED else self.colors["black"]
                highlight = (
                    self.colors["red_light"]
                    if piece.color == RED
                    else self.colors["black_light"]
                )
                self.canvas.create_oval(
                    center_x - radius + 2,
                    center_y - radius + square * 0.06,
                    center_x + radius + 2,
                    center_y + radius + square * 0.06,
                    fill="#35261f",
                    outline="",
                )
                self.canvas.create_oval(
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                    fill=rim,
                    outline=self.colors["selection"] if selected else "#fff5e8",
                    width=piece_outline,
                )
                inner_inset = square * 0.045
                self.canvas.create_oval(
                    center_x - radius + inner_inset,
                    center_y - radius + inner_inset,
                    center_x + radius - inner_inset,
                    center_y + radius - inner_inset,
                    fill=base,
                    outline="#9b302e" if piece.color == RED else "#6d6871",
                    width=1,
                )
                self.canvas.create_oval(
                    center_x - radius * 0.52,
                    center_y - radius * 0.57,
                    center_x + radius * 0.35,
                    center_y - radius * 0.28,
                    fill=highlight,
                    outline="",
                )
                if piece.king:
                    crown_color = "#f7d777"
                    crown_outline = "#9e7130"
                    crown_y = center_y - square * 0.08
                    crown_half_width = square * 0.17
                    crown_base_y = crown_y + square * 0.06
                    crown_top_y = crown_y - square * 0.13
                    crown_point = square * 0.16
                    self.canvas.create_polygon(
                        center_x - crown_point,
                        crown_y - square * 0.13,
                        center_x - crown_half_width,
                        crown_base_y,
                        center_x + crown_half_width,
                        crown_base_y,
                        center_x + crown_point,
                        crown_y - square * 0.13,
                        center_x + crown_half_width * 0.65,
                        crown_y - square * 0.03,
                        center_x,
                        crown_top_y,
                        center_x - crown_half_width * 0.65,
                        crown_y - square * 0.03,
                        fill=crown_color,
                        outline=crown_outline,
                        width=1,
                    )
                    self.canvas.create_rectangle(
                        center_x - crown_half_width,
                        crown_base_y + square * 0.015,
                        center_x + crown_half_width,
                        crown_base_y + square * 0.065,
                        fill=crown_color,
                        outline=crown_outline,
                    )

    def on_click(self, event):
        if self.game.game_over or self.ai_pending or self.game.turn != RED:
            return
        row = (event.y - self.board_top) // self.display_square_size
        column = (event.x - self.board_left) // self.display_square_size
        if not Board.inside(row, column):
            return

        position = (row, column)
        if self.selected is not None and position in self.destinations():
            valid, turn_finished = self.game.play_step(self.selected, position)
            if not valid:
                self.update_labels("That move is not legal.")
                return
            if turn_finished:
                self.selected = None
                self.update_labels()
                self.draw_board()
                if not self.game.game_over:
                    self.ai_pending = True
                    self.update_labels()
                    self.ai_job = self.root.after(180, self.computer_turn)
            else:
                self.selected = self.game.forced_piece
                self.update_labels()
                self.draw_board()
            return

        piece = self.game.board.squares[row][column]
        legal_sources = {move.start for move in self.game.legal_moves()}
        if piece is not None and piece.color == RED and position in legal_sources:
            self.selected = position
            self.update_labels()
            self.draw_board()
            return

        if self.game.forced_piece is not None:
            self.selected = self.game.forced_piece
            self.update_labels("This piece must continue capturing.")
        elif piece is not None and piece.color == BLACK:
            self.selected = None
            self.update_labels("You can only move red pieces.")
        elif self.selected is None:
            self.update_labels("Select a red piece with a legal move.")
        else:
            self.update_labels("That square is not a legal destination.")
        self.draw_board()

    def on_canvas_resize(self, event):
        if event.widget is self.canvas:
            self.draw_board()

    def computer_turn(self):
        self.ai_job = None
        if not self.ai_pending or self.game.game_over or self.game.turn != BLACK:
            return
        move = AI.choose_move(self.game.board)
        self.ai_pending = False
        if move is None or not self.game.play_ai_move(move):
            self.update_labels("No legal computer move. Click New Game to restart.")
            return
        self.update_labels()
        self.draw_board()


def main():
    root = tk.Tk()
    CheckersGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
