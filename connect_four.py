import math
import tkinter as tk


ROWS = 6
COLUMNS = 7
EMPTY = 0
HUMAN = 1
COMPUTER = 2
CONNECT = 4
SEARCH_DEPTH = 5
CELL_SIZE = 82
BOARD_PADDING = 42


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


class ConnectFourApp:
    def __init__(self, root):
        self.root = root
        self.root.title("4 op een rij")
        self.root.resizable(True, True)
        self.game = ConnectFourGame()
        self.ai_pending = False
        self.ai_job = None
        self.cell_size = CELL_SIZE
        self.board_padding = BOARD_PADDING
        self.display_cell_size = CELL_SIZE
        self.board_left = BOARD_PADDING
        self.board_top = BOARD_PADDING

        self.background = "#eee7dc"
        self.panel_color = "#faf6ef"
        self.board_color = "#1761ae"
        self.board_shadow = "#103768"
        self.board_trim = "#d2a36e"
        self.empty_color = "#0c376a"
        self.red_color = "#d93642"
        self.red_highlight = "#ff817b"
        self.yellow_color = "#f3c641"
        self.yellow_highlight = "#fff0a0"
        self.highlight_color = "#55e0ad"
        self.hover_column = None

        self.status = tk.StringVar()
        self._build_widgets()
        self._fit_window_to_screen()
        self.new_game()

    def _build_widgets(self):
        outer = tk.Frame(self.root, bg=self.background, padx=24, pady=20)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=self.background)
        header.pack(fill="x", pady=(0, 12))
        logo = tk.Canvas(
            header,
            width=42,
            height=42,
            bg=self.background,
            highlightthickness=0,
        )
        logo.pack(side="left", padx=(0, 10))
        logo.create_oval(4, 11, 27, 34, fill=self.red_color, outline="#fff4e6", width=2)
        logo.create_oval(16, 3, 39, 26, fill=self.yellow_color, outline="#fff4e6", width=2)
        title_box = tk.Frame(header, bg=self.background)
        title_box.pack(side="left")
        tk.Label(
            title_box,
            text="4 OP EEN RIJ",
            font=("Georgia", 20, "bold"),
            fg="#17345f",
            bg=self.background,
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="CONNECT FOUR  ·  RED VS. YELLOW",
            font=("Segoe UI", 8, "bold"),
            fg="#827466",
            bg=self.background,
        ).pack(anchor="w", pady=(1, 0))

        status_panel = tk.Frame(outer, bg=self.panel_color, padx=13, pady=10)
        status_panel.pack(fill="x", pady=(0, 10))
        self.status_dot = tk.Canvas(
            status_panel,
            width=21,
            height=21,
            bg=self.panel_color,
            highlightthickness=0,
        )
        self.status_dot.pack(side="left", padx=(0, 8))
        self.status_label = tk.Label(
            status_panel,
            textvariable=self.status,
            font=("Segoe UI", 10, "bold"),
            fg="#273b59",
            bg=self.panel_color,
            anchor="w",
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        players = tk.Frame(outer, bg=self.background)
        players.pack(fill="x", pady=(0, 12))
        self._add_player_card(players, "YOU", "Red", self.red_color).pack(
            side="left", fill="x", expand=True, padx=(0, 5)
        )
        self._add_player_card(players, "COMPUTER", "Yellow", self.yellow_color).pack(
            side="left", fill="x", expand=True, padx=(5, 0)
        )

        width = COLUMNS * self.cell_size + 2 * self.board_padding
        height = ROWS * self.cell_size + 2 * self.board_padding
        self.canvas = tk.Canvas(
            outer,
            width=width,
            height=height,
            bg=self.background,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_board_click)
        self.canvas.bind("<Motion>", self.on_board_motion)
        self.canvas.bind("<Leave>", self.on_board_leave)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        tk.Button(
            outer,
            text="New Game",
            command=self.new_game,
            font=("Segoe UI", 11, "bold"),
            bg="#2255a4",
            fg="white",
            activebackground="#173f80",
            activeforeground="white",
            relief="flat",
            padx=22,
            pady=9,
            cursor="hand2",
        ).pack(pady=(13, 0))
        tk.Label(
            outer,
            text="Click a column to drop a piece",
            font=("Segoe UI", 8),
            fg="#827466",
            bg=self.background,
        ).pack(pady=(8, 0))

    def _fit_window_to_screen(self):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        requested_height = self.root.winfo_reqheight()
        fixed_height = requested_height - self.canvas.winfo_reqheight()

        # Keep the initial window short enough to fit above the taskbar on laptops.
        available_height = max(400, screen_height - 60)
        self.board_padding = min(BOARD_PADDING, 24)
        available_for_board = available_height - fixed_height - 2 * self.board_padding
        self.cell_size = min(CELL_SIZE, max(40, available_for_board // ROWS))
        self.canvas.configure(
            width=COLUMNS * self.cell_size + 2 * self.board_padding,
            height=ROWS * self.cell_size + 2 * self.board_padding,
        )
        self.root.update_idletasks()

        width = min(self.root.winfo_reqwidth(), screen_width - 40)
        height = min(self.root.winfo_reqheight(), available_height)
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _add_player_card(self, parent, label, piece_name, piece_color):
        card = tk.Frame(parent, bg=self.panel_color, padx=11, pady=8)
        token = tk.Canvas(
            card,
            width=30,
            height=30,
            bg=self.panel_color,
            highlightthickness=0,
        )
        token.pack(side="left", padx=(0, 8))
        token.create_oval(4, 5, 27, 28, fill="#352d27", outline="")
        token.create_oval(2, 2, 25, 25, fill=piece_color, outline="#fff4e6", width=1)
        token.create_oval(6, 5, 17, 9, fill="#ffffff", outline="")
        details = tk.Frame(card, bg=self.panel_color)
        details.pack(side="left")
        tk.Label(
            details,
            text=label,
            font=("Segoe UI", 8, "bold"),
            fg="#827466",
            bg=self.panel_color,
        ).pack(anchor="w")
        tk.Label(
            details,
            text=piece_name,
            font=("Segoe UI", 10, "bold"),
            fg="#302820",
            bg=self.panel_color,
        ).pack(anchor="w")
        return card

    def new_game(self):
        if self.ai_job is not None:
            self.root.after_cancel(self.ai_job)
            self.ai_job = None
        self.game.reset()
        self.ai_pending = False
        self.hover_column = None
        self.update_status("Your turn — choose a column.")
        self.draw_board()

    def update_status(self, message):
        self.status.set(message)
        if self.game.winner == HUMAN or (
            not self.game.winner and not self.game.is_draw and self.game.turn == HUMAN
        ):
            color = self.red_color
        elif self.game.winner == COMPUTER or (
            not self.game.winner and not self.game.is_draw and self.game.turn == COMPUTER
        ):
            color = self.yellow_color
        else:
            color = "#8c7658"
        game_ended = bool(self.game.winner or self.game.is_draw)
        self.status_label.configure(fg="#17345f" if game_ended else "#273b59")
        self.status_dot.delete("all")
        self.status_dot.create_oval(3, 3, 18, 18, fill=color, outline="#d4c7b5", width=1)

    def draw_board(self):
        self.canvas.delete("all")
        canvas_width = max(self.canvas.winfo_width(), self.canvas.winfo_reqwidth())
        canvas_height = max(self.canvas.winfo_height(), self.canvas.winfo_reqheight())
        padding = min(self.board_padding, max(12, min(canvas_width, canvas_height) // 20))
        cell = max(
            1,
            min(
                110,
                (canvas_width - 2 * padding) // COLUMNS,
                (canvas_height - 2 * padding) // ROWS,
            ),
        )
        left = (canvas_width - COLUMNS * cell) // 2
        top = (canvas_height - ROWS * cell) // 2
        self.display_cell_size = cell
        self.board_left = left
        self.board_top = top
        self.display_padding = padding
        right = left + COLUMNS * cell
        bottom = top + ROWS * cell
        self.canvas.create_rectangle(
            left - 10,
            top - 10,
            right + 10,
            bottom + 12,
            fill="#33251d",
            outline="",
        )
        self.canvas.create_rectangle(
            left - 8,
            top - 10,
            right + 8,
            bottom + 8,
            fill="#875a3c",
            outline=self.board_trim,
            width=3,
        )
        self.canvas.create_rectangle(
            left - 3,
            top - 5,
            right + 3,
            bottom + 3,
            fill=self.board_color,
            outline="#0d4380",
            width=2,
        )

        winning = set(self.game.winning_cells)
        active = not self.game.winner and not self.game.is_draw and not self.ai_pending
        preview_color = self.red_color if self.game.turn == HUMAN else self.yellow_color
        if active and self.hover_column is not None:
            center_x = left + self.hover_column * cell + cell / 2
            self._draw_piece(
                center_x,
                top - padding / 2,
                max(7, cell * 0.16),
                preview_color,
                self.red_highlight if self.game.turn == HUMAN else self.yellow_highlight,
                shadow=False,
            )

        for row in range(ROWS):
            for column in range(COLUMNS):
                center_x = left + column * cell + cell / 2
                center_y = top + row * cell + cell / 2
                piece = self.game.board[row][column]
                highlighted = (row, column) in winning
                radius = cell * 0.39
                self.canvas.create_oval(
                    center_x - radius - 3,
                    center_y - radius - 1,
                    center_x + radius + 3,
                    center_y + radius + 5,
                    fill=self.board_shadow,
                    outline="",
                )
                self.canvas.create_oval(
                    center_x - radius,
                    center_y - radius,
                    center_x + radius,
                    center_y + radius,
                    fill="#0b3568",
                    outline="#3682cf",
                    width=2,
                )
                if piece == EMPTY:
                    self.canvas.create_oval(
                        center_x - cell * 0.30,
                        center_y - cell * 0.30,
                        center_x + cell * 0.30,
                        center_y + cell * 0.30,
                        fill=self.empty_color,
                        outline="#092c54",
                        width=2,
                    )
                    continue

                piece_color = self.red_color if piece == HUMAN else self.yellow_color
                piece_highlight = (
                    self.red_highlight if piece == HUMAN else self.yellow_highlight
                )
                self._draw_piece(
                    center_x,
                    center_y - cell * 0.025,
                    cell * 0.29,
                    piece_color,
                    piece_highlight,
                )
                if highlighted:
                    self.canvas.create_oval(
                        center_x - cell * 0.38,
                        center_y - cell * 0.38,
                        center_x + cell * 0.38,
                        center_y + cell * 0.38,
                        outline=self.highlight_color,
                        width=4,
                    )

    def _draw_piece(self, center_x, center_y, radius, color, highlight, shadow=True):
        if shadow:
            shadow_offset = max(2, radius * 0.18)
            self.canvas.create_oval(
                center_x - radius,
                center_y - radius + shadow_offset,
                center_x + radius,
                center_y + radius + shadow_offset,
                fill="#33251d",
                outline="",
            )
        rim = "#92252e" if color == self.red_color else "#9a7517"
        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill=rim,
            outline="#fff1d9",
            width=1,
        )
        self.canvas.create_oval(
            center_x - radius + max(1, radius * 0.12),
            center_y - radius + max(1, radius * 0.12),
            center_x + radius - max(1, radius * 0.12),
            center_y + radius - max(1, radius * 0.12),
            fill=color,
            outline="",
        )
        self.canvas.create_oval(
            center_x - radius * 0.58,
            center_y - radius * 0.62,
            center_x + radius * 0.30,
            center_y - radius * 0.33,
            fill=highlight,
            outline="",
        )

    def on_board_motion(self, event):
        if self.game.winner or self.game.is_draw or self.ai_pending:
            return
        column = (event.x - self.board_left) // self.display_cell_size
        if (
            0 <= column < COLUMNS
            and self.board_top <= event.y <= self.board_top + ROWS * self.display_cell_size
            and column in self.game.valid_columns()
        ):
            hover_column = column
        else:
            hover_column = None
        if hover_column != self.hover_column:
            self.hover_column = hover_column
            self.draw_board()

    def on_board_leave(self, event):
        if event.widget is not self.canvas:
            return
        if self.hover_column is not None:
            self.hover_column = None
            self.draw_board()

    def on_canvas_resize(self, event):
        if event.widget is self.canvas:
            self.draw_board()

    def on_board_click(self, event):
        if self.game.winner or self.game.is_draw or self.ai_pending or self.game.turn != HUMAN:
            return

        column = (event.x - self.board_left) // self.display_cell_size
        if not 0 <= column < COLUMNS:
            return
        if not self.game.play(column):
            return

        self.hover_column = None
        self.draw_board()
        if self.game.winner == HUMAN:
            self.update_status("You win! Click New Game to play again.")
        elif self.game.is_draw:
            self.update_status("It's a draw! Click New Game to play again.")
        else:
            self.ai_pending = True
            self.update_status("Computer is thinking...")
            self.ai_job = self.root.after(180, self.computer_turn)

    def computer_turn(self):
        self.ai_job = None
        if not self.ai_pending or self.game.winner or self.game.is_draw:
            return

        column = self.game.choose_computer_move()
        self.ai_pending = False
        if column is None or not self.game.play(column):
            self.update_status("It's a draw! Click New Game to play again.")
            return

        self.draw_board()
        if self.game.winner == COMPUTER:
            self.update_status("The computer wins! Click New Game to play again.")
        elif self.game.is_draw:
            self.update_status("It's a draw! Click New Game to play again.")
        else:
            self.update_status("Your turn — choose a column.")


def main():
    root = tk.Tk()
    ConnectFourApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
