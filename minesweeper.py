import random
import tkinter as tk
from tkinter import ttk


DIFFICULTIES = {
    "Easy": (9, 9, 10),
    "Medium": (12, 12, 20),
    "Hard": (16, 16, 40),
}
NUMBER_COLORS = {
    1: "#337a8e",
    2: "#38856d",
    3: "#c6534b",
    4: "#6050a0",
    5: "#8b4b36",
    6: "#318b8b",
    7: "#302820",
    8: "#827466",
}


class MinesweeperGame:
    """Minesweeper board state and reveal/flag rules."""

    def __init__(self, rows, columns, mine_count):
        self.rows = rows
        self.columns = columns
        self.mine_count = mine_count
        self.reset()

    def reset(self):
        self.mines = set()
        self.revealed = set()
        self.flags = set()
        self.started = False
        self.finished = False
        self.won = False

    def neighbors(self, row, column):
        return [
            (neighbor_row, neighbor_column)
            for neighbor_row in range(max(0, row - 1), min(self.rows, row + 2))
            for neighbor_column in range(max(0, column - 1), min(self.columns, column + 2))
            if (neighbor_row, neighbor_column) != (row, column)
        ]

    def _place_mines(self, first_cell):
        available = [
            (row, column)
            for row in range(self.rows)
            for column in range(self.columns)
            if (row, column) != first_cell
        ]
        self.mines = set(random.sample(available, self.mine_count))
        self.started = True

    def adjacent_mines(self, row, column):
        return sum(cell in self.mines for cell in self.neighbors(row, column))

    def reveal(self, row, column):
        cell = (row, column)
        if (
            self.finished
            or cell in self.flags
            or cell in self.revealed
            or not (0 <= row < self.rows and 0 <= column < self.columns)
        ):
            return "unchanged"

        if not self.started:
            self._place_mines(cell)

        if cell in self.mines:
            self.revealed.add(cell)
            self.finished = True
            self.won = False
            return "mine"

        pending = [cell]
        while pending:
            current = pending.pop()
            if current in self.revealed or current in self.flags:
                continue
            self.revealed.add(current)
            row, column = current
            if self.adjacent_mines(row, column) == 0:
                pending.extend(
                    neighbor
                    for neighbor in self.neighbors(row, column)
                    if neighbor not in self.revealed
                    and neighbor not in self.flags
                    and neighbor not in self.mines
                )

        if len(self.revealed) == self.rows * self.columns - self.mine_count:
            self.finished = True
            self.won = True
            return "won"
        return "revealed"

    def toggle_flag(self, row, column):
        cell = (row, column)
        if (
            self.finished
            or cell in self.revealed
            or not (0 <= row < self.rows and 0 <= column < self.columns)
        ):
            return False
        if cell in self.flags:
            self.flags.remove(cell)
        else:
            self.flags.add(cell)
        return True


class MinesweeperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Minesweeper")
        self.root.geometry("760x760")
        self.root.minsize(540, 580)
        self.root.configure(bg="#eee7dc")

        self.colors = {
            "background": "#eee7dc",
            "panel": "#faf6ef",
            "board": "#cfc5b6",
            "covered": "#e4dacb",
            "covered_light": "#f4ecdf",
            "covered_dark": "#b8a995",
            "revealed": "#faf6ef",
            "mine": "#c6534b",
            "flag": "#d7893d",
            "text": "#302820",
            "muted": "#827466",
            "accent": "#337a8e",
            "accent_dark": "#245766",
            "wood": "#8f5e3d",
        }
        self.difficulty = tk.StringVar(value="Easy")
        self.status = tk.StringVar()
        self.mine_display = tk.StringVar()
        self.game = None
        self.cell_size = 40
        self.board_left = 0
        self.board_top = 0
        self._build_widgets()
        self.new_game()

    def _build_widgets(self):
        outer = tk.Frame(self.root, bg=self.colors["background"], padx=18, pady=12)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=self.colors["background"])
        header.pack(fill="x", pady=(0, 8))
        logo = tk.Canvas(
            header,
            width=42,
            height=42,
            bg=self.colors["background"],
            highlightthickness=0,
        )
        logo.pack(side="left", padx=(0, 10))
        logo.create_oval(3, 3, 39, 39, fill=self.colors["accent"], outline="")
        logo.create_text(21, 21, text="*", fill="white", font=("Georgia", 27, "bold"))
        title = tk.Frame(header, bg=self.colors["background"])
        title.pack(side="left")
        tk.Label(
            title,
            text="MINESWEEPER",
            font=("Georgia", 20, "bold"),
            fg=self.colors["text"],
            bg=self.colors["background"],
        ).pack(anchor="w")
        tk.Label(
            title,
            text="CLEAR THE BOARD. AVOID THE MINES.",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["background"],
        ).pack(anchor="w", pady=(1, 0))

        toolbar = tk.Frame(outer, bg=self.colors["panel"], padx=10, pady=8)
        toolbar.pack(fill="x", pady=(0, 8))
        self._button(toolbar, "New Game", self.new_game, primary=True).pack(side="left")
        ttk.Label(
            toolbar,
            text="Difficulty",
            background=self.colors["panel"],
            foreground=self.colors["text"],
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(14, 6))
        self.difficulty_box = ttk.Combobox(
            toolbar,
            textvariable=self.difficulty,
            values=list(DIFFICULTIES),
            state="readonly",
            width=9,
        )
        self.difficulty_box.pack(side="left")
        self.difficulty_box.bind("<<ComboboxSelected>>", self._on_difficulty_changed)
        tk.Label(
            toolbar,
            textvariable=self.mine_display,
            font=("Consolas", 12, "bold"),
            fg=self.colors["accent_dark"],
            bg=self.colors["panel"],
        ).pack(side="right", padx=(8, 2))

        info = tk.Frame(outer, bg=self.colors["panel"], padx=10, pady=7)
        info.pack(fill="x", pady=(0, 8))
        tk.Label(
            info,
            textvariable=self.status,
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
            anchor="w",
        ).pack(fill="x")

        board_panel = tk.Frame(outer, bg=self.colors["board"], padx=8, pady=8)
        board_panel.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(
            board_panel,
            bg=self.colors["board"],
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-3>", self._on_right_click)

        tk.Label(
            outer,
            text="Left-click to reveal  ·  Right-click to place or remove a flag",
            font=("Segoe UI", 8),
            fg=self.colors["muted"],
            bg=self.colors["background"],
        ).pack(pady=(8, 0))

    def _button(self, parent, text, command, primary=False):
        background = self.colors["accent"] if primary else self.colors["panel"]
        foreground = "white" if primary else self.colors["text"]
        active_background = self.colors["accent_dark"] if primary else "#e7dfd3"
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9, "bold"),
            fg=foreground,
            bg=background,
            activeforeground=foreground,
            activebackground=active_background,
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        )

    def _on_difficulty_changed(self, _event=None):
        self.new_game()

    def new_game(self):
        rows, columns, mine_count = DIFFICULTIES[self.difficulty.get()]
        self.game = MinesweeperGame(rows, columns, mine_count)
        self.status.set("Choose a square to begin. Your first click is always safe.")
        self.mine_display.set(f"MINES {mine_count:03}")
        self._draw_board()

    def _on_canvas_resize(self, _event=None):
        self._draw_board()

    def _cell_at(self, event):
        if self.game is None or self.cell_size <= 0:
            return None
        column = (event.x - self.board_left) // self.cell_size
        row = (event.y - self.board_top) // self.cell_size
        if row >= self.game.rows or column >= self.game.columns:
            return None
        if event.x < self.board_left or event.y < self.board_top:
            return None
        return row, column

    def _on_left_click(self, event):
        cell = self._cell_at(event)
        if cell is None:
            return
        result = self.game.reveal(*cell)
        if result == "mine":
            self.status.set("Boom! You hit a mine. Start a new game to try again.")
        elif result == "won":
            self.status.set("You cleared the board! You win.")
        elif result == "revealed":
            self.status.set("Keep going — use the numbers to find the mines.")
        self.mine_display.set(
            f"MINES {self.game.mine_count - len(self.game.flags):03}"
        )
        self._draw_board()

    def _on_right_click(self, event):
        cell = self._cell_at(event)
        if cell is None or not self.game.toggle_flag(*cell):
            return
        self.mine_display.set(
            f"MINES {self.game.mine_count - len(self.game.flags):03}"
        )
        self.status.set("Flag placed." if cell in self.game.flags else "Flag removed.")
        self._draw_board()

    def _draw_board(self):
        if self.game is None or not hasattr(self, "canvas"):
            return
        self.canvas.delete("all")
        rows, columns = self.game.rows, self.game.columns
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        self.cell_size = max(1, min(48, width // columns, height // rows))
        board_width = self.cell_size * columns
        board_height = self.cell_size * rows
        self.board_left = max(0, (width - board_width) // 2)
        self.board_top = max(0, (height - board_height) // 2)
        left = self.board_left
        top = self.board_top
        size = self.cell_size
        font_size = max(9, min(17, size // 2))

        for row in range(rows):
            for column in range(columns):
                cell = (row, column)
                x1, y1 = left + column * size, top + row * size
                x2, y2 = x1 + size, y1 + size
                if cell in self.game.revealed:
                    if cell in self.game.mines:
                        fill = self.colors["mine"]
                        text = "*"
                        text_color = "white"
                    else:
                        fill = self.colors["revealed"]
                        count = self.game.adjacent_mines(row, column)
                        text = str(count) if count else ""
                        text_color = NUMBER_COLORS.get(count, self.colors["text"])
                    self.canvas.create_rectangle(
                        x1, y1, x2, y2, fill=fill, outline=self.colors["covered_dark"]
                    )
                    if text:
                        self.canvas.create_text(
                            (x1 + x2) / 2,
                            (y1 + y2) / 2,
                            text=text,
                            fill=text_color,
                            font=("Segoe UI", font_size, "bold"),
                        )
                else:
                    self.canvas.create_rectangle(
                        x1,
                        y1,
                        x2,
                        y2,
                        fill=self.colors["covered"],
                        outline=self.colors["covered_dark"],
                        width=1,
                    )
                    self.canvas.create_line(
                        x1 + 1, y1 + 1, x2 - 1, y1 + 1,
                        fill=self.colors["covered_light"], width=2
                    )
                    if cell in self.game.flags:
                        self.canvas.create_text(
                            (x1 + x2) / 2,
                            (y1 + y2) / 2,
                            text="F",
                            fill=self.colors["flag"],
                            font=("Segoe UI", font_size, "bold"),
                        )

        if self.game.finished and not self.game.won:
            for row, column in self.game.mines:
                if (row, column) in self.game.revealed:
                    continue
                x1 = left + column * size
                y1 = top + row * size
                self.canvas.create_oval(
                    x1 + size * 0.3,
                    y1 + size * 0.3,
                    x1 + size * 0.7,
                    y1 + size * 0.7,
                    fill=self.colors["mine"],
                    outline="",
                )


def main():
    root = tk.Tk()
    MinesweeperApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
