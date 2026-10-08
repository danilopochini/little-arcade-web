import math
import tkinter as tk

import chess


BOARD_SIZE = 8
SQUARE_SIZE = 76
BOARD_MARGIN = 30
SEARCH_DEPTH = 3

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 335,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

PIECE_GLYPHS = {
    chess.WHITE: {
        chess.KING: "♔",
        chess.QUEEN: "♕",
        chess.ROOK: "♖",
        chess.BISHOP: "♗",
        chess.KNIGHT: "♘",
        chess.PAWN: "♙",
    },
    chess.BLACK: {
        chess.KING: "♚",
        chess.QUEEN: "♛",
        chess.ROOK: "♜",
        chess.BISHOP: "♝",
        chess.KNIGHT: "♞",
        chess.PAWN: "♟",
    },
}


class ChessAI:
    """A material-and-position evaluator with alpha-beta minimax search."""

    def __init__(self, depth=SEARCH_DEPTH):
        self.depth = depth
        self.transposition_table = {}

    @staticmethod
    def evaluate(board):
        if board.is_checkmate():
            return -100_000 if board.turn == chess.WHITE else 100_000
        if board.is_game_over(claim_draw=True):
            return 0

        score = 0
        for square, piece in board.piece_map().items():
            file_index = chess.square_file(square)
            rank_index = chess.square_rank(square)
            advancement = rank_index if piece.color == chess.WHITE else 7 - rank_index
            center_distance = abs(3.5 - file_index) + abs(3.5 - rank_index)
            value = PIECE_VALUES[piece.piece_type]

            if piece.piece_type == chess.PAWN:
                value += advancement * 8
                if 2 <= file_index <= 5:
                    value += 7
            elif piece.piece_type in (chess.KNIGHT, chess.BISHOP):
                value += int((7 - center_distance) * 5)
            elif piece.piece_type == chess.QUEEN:
                value += int((7 - center_distance) * 2)

            score += value if piece.color == chess.WHITE else -value

        # Small mobility bonus encourages active positions without dominating material.
        side_to_move_mobility = board.legal_moves.count()
        mobility = min(side_to_move_mobility, 40)
        score += mobility if board.turn == chess.WHITE else -mobility
        return score

    @staticmethod
    def ordered_moves(board):
        def move_priority(move):
            piece = board.piece_at(move.from_square)
            captured = board.piece_at(move.to_square)
            score = 0
            if board.is_capture(move):
                captured_value = (
                    PIECE_VALUES[chess.PAWN]
                    if board.is_en_passant(move)
                    else PIECE_VALUES[captured.piece_type] if captured else 0
                )
                moving_value = PIECE_VALUES[piece.piece_type] if piece else 0
                score += 10_000 + captured_value * 10 - moving_value
            if move.promotion:
                score += 9_000 + PIECE_VALUES[move.promotion]
            if board.gives_check(move):
                score += 100
            return score

        return sorted(list(board.legal_moves), key=move_priority, reverse=True)

    def _search(self, board, depth, alpha, beta, ply):
        if board.is_checkmate():
            return -100_000 + ply if board.turn == chess.WHITE else 100_000 - ply
        if board.is_game_over(claim_draw=True):
            return 0
        if depth == 0:
            return self.evaluate(board)

        key = (
            board.board_fen(),
            board.turn,
            board.castling_rights,
            board.ep_square,
            depth,
        )
        if key in self.transposition_table:
            return self.transposition_table[key]

        maximizing = board.turn == chess.WHITE
        best_score = -math.inf if maximizing else math.inf
        for move in self.ordered_moves(board):
            board.push(move)
            score = self._search(board, depth - 1, alpha, beta, ply + 1)
            board.pop()

            if maximizing:
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
            else:
                best_score = min(best_score, score)
                beta = min(beta, best_score)
            if alpha >= beta:
                break

        result = int(best_score)
        self.transposition_table[key] = result
        return result

    def choose_move(self, board):
        legal_moves = self.ordered_moves(board)
        if not legal_moves:
            return None

        self.transposition_table.clear()
        best_move = legal_moves[0]
        best_score = math.inf
        alpha, beta = -math.inf, math.inf
        for move in legal_moves:
            board.push(move)
            score = self._search(board, self.depth - 1, alpha, beta, 1)
            board.pop()
            if score < best_score:
                best_score, best_move = score, move
            beta = min(beta, best_score)
        return best_move


class ChessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess")
        self.root.resizable(True, True)
        self.board = chess.Board()
        self.ai = ChessAI()
        self.ai_pending = False
        self.ai_job = None
        self.selected_square = None
        self.last_move = None
        self.cell_size = SQUARE_SIZE
        self.board_padding = BOARD_MARGIN
        self.display_cell_size = SQUARE_SIZE
        self.board_left = BOARD_MARGIN
        self.board_top = BOARD_MARGIN

        self.colors = {
            "background": "#eee7dc",
            "panel": "#faf6ef",
            "light": "#e8d4b3",
            "dark": "#65402e",
            "wood": "#8f5e3d",
            "wood_light": "#b47c50",
            "white_piece": "#fff6e6",
            "black_piece": "#24232b",
            "white_shadow": "#b58b62",
            "black_shadow": "#07080b",
            "selection": "#63e0bb",
            "destination": "#f4cf63",
            "last_move": "#fff0a8",
            "check": "#e8645b",
            "text": "#302820",
            "muted": "#827466",
        }
        self.status = tk.StringVar()
        self._build_widgets()
        self._fit_window_to_screen()
        self.new_game()

    def _build_widgets(self):
        outer = tk.Frame(self.root, bg=self.colors["background"], padx=24, pady=18)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=self.colors["background"])
        header.pack(fill="x", pady=(0, 10))
        logo = tk.Canvas(
            header,
            width=42,
            height=42,
            bg=self.colors["background"],
            highlightthickness=0,
        )
        logo.pack(side="left", padx=(0, 10))
        logo.create_text(15, 23, text="♞", font=("Segoe UI Symbol", 29), fill="#24232b")
        logo.create_text(31, 21, text="♙", font=("Segoe UI Symbol", 23), fill="#c9363d")

        title_box = tk.Frame(header, bg=self.colors["background"])
        title_box.pack(side="left")
        tk.Label(
            title_box,
            text="CHESS",
            font=("Georgia", 20, "bold"),
            fg=self.colors["text"],
            bg=self.colors["background"],
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="A CLASSIC GAME OF STRATEGY",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["background"],
        ).pack(anchor="w", pady=(1, 0))

        info = tk.Frame(outer, bg=self.colors["panel"], padx=12, pady=9)
        info.pack(fill="x", pady=(0, 9))
        self.status_dot = tk.Canvas(
            info, width=17, height=17, bg=self.colors["panel"], highlightthickness=0
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

        players = tk.Frame(outer, bg=self.colors["background"])
        players.pack(fill="x", pady=(0, 9))
        self._player_card(players, "YOU", "White", chess.WHITE).pack(
            side="left", fill="x", expand=True, padx=(0, 5)
        )
        self._player_card(players, "COMPUTER", "Black", chess.BLACK).pack(
            side="left", fill="x", expand=True, padx=(5, 0)
        )

        size = BOARD_SIZE * self.cell_size + 2 * self.board_padding
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
            pady=8,
            cursor="hand2",
        ).pack(pady=(10, 0))
        tk.Label(
            outer,
            text="White moves first  •  Select a piece, then its destination",
            font=("Segoe UI", 8),
            fg=self.colors["muted"],
            bg=self.colors["background"],
        ).pack(pady=(7, 0))

    def _player_card(self, parent, label, piece_name, color):
        card = tk.Frame(parent, bg=self.colors["panel"], padx=11, pady=7)
        icon = tk.Canvas(
            card, width=29, height=29, bg=self.colors["panel"], highlightthickness=0
        )
        icon.pack(side="left", padx=(0, 8))
        fill = self.colors["white_piece"] if color == chess.WHITE else self.colors["black_piece"]
        outline = self.colors["wood"] if color == chess.WHITE else "#09090b"
        icon.create_oval(3, 3, 26, 26, fill=fill, outline=outline, width=2)
        icon.create_text(
            14.5,
            14.5,
            text="♙" if color == chess.WHITE else "♟",
            font=("Segoe UI Symbol", 18),
            fill=self.colors["black_piece"] if color == chess.WHITE else "#fff6e6",
        )
        details = tk.Frame(card, bg=self.colors["panel"])
        details.pack(side="left")
        tk.Label(
            details,
            text=label,
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["panel"],
        ).pack(anchor="w")
        tk.Label(
            details,
            text=piece_name,
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
        ).pack(anchor="w")
        return card

    def _fit_window_to_screen(self):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        requested_height = self.root.winfo_reqheight()
        fixed_height = requested_height - self.canvas.winfo_reqheight()
        available_height = max(400, screen_height - 60)
        self.board_padding = 24
        available_for_board = available_height - fixed_height - 2 * self.board_padding
        self.cell_size = min(SQUARE_SIZE, max(40, available_for_board // BOARD_SIZE))
        self.canvas.configure(
            width=BOARD_SIZE * self.cell_size + 2 * self.board_padding,
            height=BOARD_SIZE * self.cell_size + 2 * self.board_padding,
        )
        self.root.update_idletasks()

        width = min(self.root.winfo_reqwidth(), screen_width - 40)
        height = min(self.root.winfo_reqheight(), available_height)
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def new_game(self):
        if self.ai_job is not None:
            self.root.after_cancel(self.ai_job)
            self.ai_job = None
        self.board.reset()
        self.ai_pending = False
        self.selected_square = None
        self.last_move = None
        self.update_status()
        self.draw_board()

    def update_status(self, message=None):
        outcome = self.board.outcome(claim_draw=True)
        if message is not None:
            text = message
        elif outcome is not None:
            if outcome.winner is None:
                text = f"Draw — {outcome.termination.name.replace('_', ' ').title()}."
            else:
                winner = "White" if outcome.winner == chess.WHITE else "Black"
                text = f"{winner} wins — {outcome.termination.name.replace('_', ' ').title()}."
        elif self.ai_pending:
            text = "Computer is thinking..."
        elif self.board.is_check():
            text = "Check! Your move." if self.board.turn == chess.WHITE else "Check — computer to move."
        elif self.board.turn == chess.WHITE:
            text = "Your turn — select a white piece."
        else:
            text = "Computer is thinking..."

        self.status.set(text)
        if outcome is not None and outcome.winner is None:
            status_color = self.colors["wood"]
        elif outcome is not None:
            status_color = self.colors["wood"] if outcome.winner == chess.WHITE else self.colors["black_piece"]
        elif self.board.turn == chess.WHITE:
            status_color = "#a82e35"
        else:
            status_color = self.colors["black_piece"]
        self.status_label.configure(fg=status_color)
        self.status_dot.delete("all")
        dot = (
            self.colors["wood"]
            if outcome is not None and outcome.winner is None
            else self.colors["white_piece"]
            if self.board.turn == chess.WHITE
            else self.colors["black_piece"]
        )
        self.status_dot.create_oval(3, 3, 14, 14, fill=dot, outline=self.colors["wood"], width=1)

    def legal_destinations(self):
        if self.selected_square is None or self.board.turn != chess.WHITE:
            return set()
        return {
            move.to_square
            for move in self.board.legal_moves
            if move.from_square == self.selected_square
        }

    def draw_board(self):
        self.canvas.delete("all")
        canvas_width = max(self.canvas.winfo_width(), self.canvas.winfo_reqwidth())
        canvas_height = max(self.canvas.winfo_height(), self.canvas.winfo_reqheight())
        margin = max(10, min(24, min(canvas_width, canvas_height) // 20))
        square = max(
            1,
            min(
                100,
                (canvas_width - 2 * margin) // BOARD_SIZE,
                (canvas_height - 2 * margin) // BOARD_SIZE,
            ),
        )
        left = (canvas_width - BOARD_SIZE * square) // 2
        top = (canvas_height - BOARD_SIZE * square) // 2
        right = left + BOARD_SIZE * square
        bottom = top + BOARD_SIZE * square
        self.display_cell_size = square
        self.board_left = left
        self.board_top = top

        self.canvas.create_rectangle(
            left - 9,
            top - 9,
            right + 9,
            bottom + 10,
            fill="#33251d",
            outline="",
        )
        self.canvas.create_rectangle(
            left - 7,
            top - 8,
            right + 7,
            bottom + 7,
            fill=self.colors["wood"],
            outline=self.colors["wood_light"],
            width=3,
        )

        legal_moves = (
            [move for move in self.board.legal_moves if move.from_square == self.selected_square]
            if self.selected_square is not None
            else []
        )
        destinations = {move.to_square for move in legal_moves}
        capture_destinations = {
            move.to_square for move in legal_moves if self.board.is_capture(move)
        }
        last_squares = set()
        if self.last_move is not None:
            last_squares = {self.last_move.from_square, self.last_move.to_square}
        checked_king = (
            self.board.king(self.board.turn)
            if self.board.is_check()
            else None
        )

        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                square_id = chess.square(column, BOARD_SIZE - 1 - row)
                x1 = left + column * square
                y1 = top + row * square
                x2, y2 = x1 + square, y1 + square
                is_light = (row + column) % 2 == 0
                square_color = self.colors["light"] if is_light else self.colors["dark"]
                if square_id in last_squares:
                    square_color = "#c5a56c" if is_light else "#8c7448"
                if square_id == checked_king:
                    square_color = self.colors["check"]
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=square_color, outline=square_color
                )

                if column == 0:
                    self.canvas.create_text(
                        x1 + square * 0.08,
                        y1 + square * 0.08,
                        text=str(BOARD_SIZE - row),
                        anchor="nw",
                        fill="#f6e8d4" if not is_light else self.colors["dark"],
                        font=("Segoe UI", max(7, int(square * 0.12)), "bold"),
                    )
                if row == BOARD_SIZE - 1:
                    self.canvas.create_text(
                        x2 - square * 0.08,
                        y2 - square * 0.08,
                        text=chess.FILE_NAMES[column],
                        anchor="se",
                        fill="#f6e8d4" if not is_light else self.colors["dark"],
                        font=("Segoe UI", max(7, int(square * 0.12)), "bold"),
                    )

                if square_id == self.selected_square:
                    self.canvas.create_rectangle(
                        x1 + 2,
                        y1 + 2,
                        x2 - 2,
                        y2 - 2,
                        outline=self.colors["selection"],
                        width=max(3, int(square * 0.055)),
                    )
                if square_id in destinations:
                    if square_id in capture_destinations:
                        inset = square * 0.08
                        self.canvas.create_oval(
                            x1 + inset,
                            y1 + inset,
                            x2 - inset,
                            y2 - inset,
                            outline=self.colors["destination"],
                            width=max(3, int(square * 0.06)),
                        )
                    else:
                        inset = square * 0.39
                        self.canvas.create_oval(
                            x1 + inset,
                            y1 + inset,
                            x2 - inset,
                            y2 - inset,
                            fill=self.colors["destination"],
                            outline="#fff1c4",
                            width=1,
                        )

                piece = self.board.piece_at(square_id)
                if piece is None:
                    continue
                center_x, center_y = (x1 + x2) / 2, (y1 + y2) / 2
                glyph = PIECE_GLYPHS[piece.color][piece.piece_type]
                font_size = max(16, int(square * 0.76))
                glyph_color = (
                    self.colors["white_piece"]
                    if piece.color == chess.WHITE
                    else self.colors["black_piece"]
                )
                outline_color = (
                    self.colors["wood"]
                    if piece.color == chess.WHITE
                    else "#09090b"
                )
                self.canvas.create_text(
                    center_x + 1,
                    center_y + square * 0.04,
                    text=glyph,
                    font=("Segoe UI Symbol", font_size, "bold"),
                    fill=outline_color,
                )
                self.canvas.create_text(
                    center_x,
                    center_y,
                    text=glyph,
                    font=("Segoe UI Symbol", font_size, "bold"),
                    fill=glyph_color,
                )

    def on_click(self, event):
        if self.board.is_game_over(claim_draw=True) or self.ai_pending or self.board.turn != chess.WHITE:
            return
        row = (event.y - self.board_top) // self.display_cell_size
        column = (event.x - self.board_left) // self.display_cell_size
        if not (0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE):
            return

        square = chess.square(column, BOARD_SIZE - 1 - row)
        piece = self.board.piece_at(square)
        if self.selected_square is None:
            if piece is not None and piece.color == chess.WHITE:
                self.selected_square = square
                self.draw_board()
            else:
                self.update_status("Select one of your white pieces.")
            return

        move = next(
            (
                candidate
                for candidate in self.board.legal_moves
                if candidate.from_square == self.selected_square
                and candidate.to_square == square
            ),
            None,
        )
        if move is not None:
            if move.promotion:
                move = chess.Move(
                    move.from_square,
                    move.to_square,
                    promotion=chess.QUEEN,
                )
            self.board.push(move)
            self.last_move = move
            self.selected_square = None
            self.draw_board()
            if self.board.is_game_over(claim_draw=True):
                self.update_status()
            else:
                self.ai_pending = True
                self.update_status("Computer is thinking...")
                self.ai_job = self.root.after(100, self.computer_turn)
        elif piece is not None and piece.color == chess.WHITE:
            self.selected_square = square
            self.update_status("That piece has no legal move to this square.")
            self.draw_board()
        else:
            self.update_status("That is not a legal destination.")

    def computer_turn(self):
        self.ai_job = None
        if not self.ai_pending or self.board.is_game_over(claim_draw=True):
            self.ai_pending = False
            return

        move = self.ai.choose_move(self.board)
        self.ai_pending = False
        if move is None:
            self.update_status()
            return
        self.board.push(move)
        self.last_move = move
        self.draw_board()
        self.update_status()

    def on_canvas_resize(self, event):
        if event.widget is self.canvas:
            self.draw_board()


def main():
    root = tk.Tk()
    ChessApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
