import tkinter as tk
from tkinter import ttk
from time import monotonic

from sudoku_logic import BOX_SIZE, DIFFICULTIES, SIZE, SudokuPuzzle


class SudokuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku")
        self.root.resizable(True, True)
        self.puzzle = SudokuPuzzle()
        self.difficulty = tk.StringVar(value="Easy")
        self.status = tk.StringVar()
        self.elapsed = tk.StringVar(value="00:00")
        self.selected = None
        self.notes = [[set() for _ in range(SIZE)] for _ in range(SIZE)]
        self.given = [[False] * SIZE for _ in range(SIZE)]
        self.note_mode = False
        self.checked = False
        self.mistakes = 0
        self.started_at = monotonic()
        self.game_won = False
        self.cell_size = 54
        self.margin = 16
        self.board_left = 0
        self.board_top = 0
        self.display_cell = self.cell_size
        self._timer_job = None

        self.colors = {
            "background": "#eee7dc",
            "panel": "#faf6ef",
            "grid": "#7b6753",
            "grid_major": "#4a3828",
            "cell": "#fffaf2",
            "given": "#eadfce",
            "selected": "#b8d9e8",
            "peer": "#e7eef0",
            "same_number": "#d3e5eb",
            "accent": "#337a8e",
            "accent_dark": "#245766",
            "wood": "#8f5e3d",
            "wrong": "#f3c2b8",
            "text": "#302820",
            "muted": "#827466",
            "note": "#657b91",
        }

        self._build_widgets()
        self._fit_window_to_screen()
        self.new_game()
        self.root.bind("<KeyPress>", self.on_key)
        self._update_timer()

    def _build_widgets(self):
        outer = tk.Frame(self.root, bg=self.colors["background"], padx=18, pady=12)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=self.colors["background"])
        header.pack(fill="x", pady=(0, 7))
        logo = tk.Canvas(
            header,
            width=40,
            height=40,
            bg=self.colors["background"],
            highlightthickness=0,
        )
        logo.pack(side="left", padx=(0, 9))
        logo.create_rectangle(3, 3, 37, 37, fill=self.colors["accent"], outline="")
        logo.create_text(
            20,
            20,
            text="9",
            fill="white",
            font=("Georgia", 22, "bold"),
        )
        title = tk.Frame(header, bg=self.colors["background"])
        title.pack(side="left")
        tk.Label(
            title,
            text="SUDOKU",
            font=("Georgia", 20, "bold"),
            fg=self.colors["text"],
            bg=self.colors["background"],
        ).pack(anchor="w")
        tk.Label(
            title,
            text="A CLASSIC NUMBER PUZZLE",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["background"],
        ).pack(anchor="w", pady=(1, 0))

        info = tk.Frame(outer, bg=self.colors["panel"], padx=11, pady=7)
        info.pack(fill="x", pady=(0, 7))
        self.status_dot = tk.Canvas(
            info,
            width=16,
            height=16,
            bg=self.colors["panel"],
            highlightthickness=0,
        )
        self.status_dot.pack(side="left", padx=(0, 7))
        tk.Label(
            info,
            textvariable=self.status,
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
            anchor="w",
        ).pack(side="left", fill="x", expand=True)
        tk.Label(
            info,
            textvariable=self.elapsed,
            font=("Consolas", 10, "bold"),
            fg=self.colors["accent_dark"],
            bg=self.colors["panel"],
        ).pack(side="right", padx=(8, 0))

        controls = tk.Frame(outer, bg=self.colors["background"])
        controls.pack(fill="x", pady=(0, 7))
        tk.Label(
            controls,
            text="Difficulty",
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["background"],
        ).pack(side="left", padx=(0, 6))
        self.difficulty_menu = ttk.Combobox(
            controls,
            textvariable=self.difficulty,
            values=list(DIFFICULTIES),
            state="readonly",
            width=9,
        )
        self.difficulty_menu.pack(side="left")
        self.difficulty_menu.bind("<<ComboboxSelected>>", self._difficulty_changed)
        self._button(controls, "New Game", self.new_game).pack(side="right", padx=(5, 0))
        self._button(controls, "Check", self.check_board).pack(side="right", padx=(5, 0))
        self.notes_button = self._button(controls, "Notes: Off", self.toggle_notes)
        self.notes_button.pack(side="right", padx=(5, 0))
        self._button(controls, "Erase", self.erase_cell).pack(side="right")

        self.canvas = tk.Canvas(
            outer,
            width=SIZE * self.cell_size + 2 * self.margin,
            height=SIZE * self.cell_size + 2 * self.margin,
            bg=self.colors["background"],
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        keypad = tk.Frame(outer, bg=self.colors["background"])
        keypad.pack(fill="x", pady=(7, 0))
        self.number_buttons = []
        for number in range(1, SIZE + 1):
            button = tk.Button(
                keypad,
                text=str(number),
                command=lambda value=number: self.enter_number(value),
                font=("Segoe UI", 12, "bold"),
                fg=self.colors["accent_dark"],
                bg=self.colors["panel"],
                activebackground=self.colors["selected"],
                relief="flat",
                cursor="hand2",
                padx=1,
                pady=4,
            )
            button.pack(side="left", fill="x", expand=True, padx=2)
            self.number_buttons.append(button)

        tk.Label(
            outer,
            text="Select a cell, then use 1–9 or click a number  •  N toggles notes  •  Arrow keys move",
            font=("Segoe UI", 8),
            fg=self.colors["muted"],
            bg=self.colors["background"],
        ).pack(pady=(6, 0))

    def _button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 8, "bold"),
            fg="white",
            bg=self.colors["accent"],
            activebackground=self.colors["accent_dark"],
            activeforeground="white",
            relief="flat",
            padx=8,
            pady=5,
            cursor="hand2",
        )

    def _fit_window_to_screen(self):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        fixed_height = self.root.winfo_reqheight() - self.canvas.winfo_reqheight()
        available_height = max(400, screen_height - 55)
        self.margin = 14
        available_board = available_height - fixed_height - 2 * self.margin
        self.cell_size = min(54, max(34, available_board // SIZE))
        board_size = SIZE * self.cell_size + 2 * self.margin
        self.canvas.configure(width=board_size, height=board_size)
        self.root.update_idletasks()
        width = min(self.root.winfo_reqwidth(), screen_width - 30)
        height = min(self.root.winfo_reqheight(), available_height)
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _difficulty_changed(self, event):
        if event.widget is self.difficulty_menu:
            self.new_game()

    def new_game(self):
        self.puzzle.generate(self.difficulty.get())
        self.given = [[value != 0 for value in row] for row in self.puzzle.grid]
        self.notes = [[set() for _ in range(SIZE)] for _ in range(SIZE)]
        self.selected = None
        self.checked = False
        self.mistakes = 0
        self.game_won = False
        self.started_at = monotonic()
        self.set_status(f"{self.difficulty.get()} puzzle — select a cell to begin.", self.colors["accent_dark"])
        self.draw_board()

    def set_status(self, text, color=None):
        self.status.set(text)
        self.status_dot.delete("all")
        self.status_dot.create_oval(
            3,
            3,
            13,
            13,
            fill=color or self.colors["accent"],
            outline="",
        )

    def _cell_at(self, x, y):
        row = (y - self.board_top) // self.display_cell
        column = (x - self.board_left) // self.display_cell
        if 0 <= row < SIZE and 0 <= column < SIZE:
            return row, column
        return None

    def draw_board(self):
        self.canvas.delete("all")
        canvas_width = max(self.canvas.winfo_width(), self.canvas.winfo_reqwidth())
        canvas_height = max(self.canvas.winfo_height(), self.canvas.winfo_reqheight())
        margin = max(8, min(self.margin, min(canvas_width, canvas_height) // 22))
        cell = max(
            1,
            min(
                72,
                (canvas_width - 2 * margin) // SIZE,
                (canvas_height - 2 * margin) // SIZE,
            ),
        )
        left = (canvas_width - SIZE * cell) // 2
        top = (canvas_height - SIZE * cell) // 2
        self.display_cell = cell
        self.board_left = left
        self.board_top = top

        selected_value = 0
        if self.selected is not None:
            selected_value = self.puzzle.grid[self.selected[0]][self.selected[1]]
        selected_row, selected_column = self.selected if self.selected is not None else (-1, -1)

        self.canvas.create_rectangle(
            left - 7,
            top - 7,
            left + SIZE * cell + 7,
            top + SIZE * cell + 7,
            fill="#33251d",
            outline="",
        )
        self.canvas.create_rectangle(
            left - 5,
            top - 5,
            left + SIZE * cell + 5,
            top + SIZE * cell + 5,
            fill=self.colors["accent_dark"],
            outline=self.colors["wood"],
            width=2,
        )

        for row in range(SIZE):
            for column in range(SIZE):
                x1 = left + column * cell
                y1 = top + row * cell
                x2, y2 = x1 + cell, y1 + cell
                value = self.puzzle.grid[row][column]
                is_peer = (
                    self.selected is not None
                    and (
                        row == selected_row
                        or column == selected_column
                        or (row // BOX_SIZE, column // BOX_SIZE)
                        == (selected_row // BOX_SIZE, selected_column // BOX_SIZE)
                    )
                )
                fill = self.colors["cell"]
                if self.given[row][column]:
                    fill = self.colors["given"]
                if is_peer and (row, column) != self.selected:
                    fill = self.colors["peer"]
                if selected_value and value == selected_value and (row, column) != self.selected:
                    fill = self.colors["same_number"]
                if (row, column) == self.selected:
                    fill = self.colors["selected"]
                if self.checked and value and not self.given[row][column]:
                    if value != self.puzzle.solution[row][column]:
                        fill = self.colors["wrong"]

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=fill,
                    outline=self.colors["grid"],
                    width=1,
                )

                if value:
                    color = self.colors["text"] if self.given[row][column] else self.colors["accent_dark"]
                    self.canvas.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text=str(value),
                        fill=color,
                        font=("Segoe UI", max(12, int(cell * 0.48)), "bold" if self.given[row][column] else "normal"),
                    )
                else:
                    notes = self.notes[row][column]
                    for note in notes:
                        note_row = (note - 1) // 3
                        note_column = (note - 1) % 3
                        self.canvas.create_text(
                            x1 + (note_column + 0.5) * cell / 3,
                            y1 + (note_row + 0.5) * cell / 3,
                            text=str(note),
                            fill=self.colors["note"],
                            font=("Segoe UI", max(7, int(cell * 0.17))),
                        )

        for index in range(SIZE + 1):
            line_width = 3 if index % BOX_SIZE == 0 else 1
            color = self.colors["grid_major"] if index % BOX_SIZE == 0 else self.colors["grid"]
            x = left + index * cell
            y = top + index * cell
            self.canvas.create_line(x, top, x, top + SIZE * cell, fill=color, width=line_width)
            self.canvas.create_line(left, y, left + SIZE * cell, y, fill=color, width=line_width)

    def on_click(self, event):
        cell = self._cell_at(event.x, event.y)
        if cell is None:
            return
        self.selected = cell
        self.draw_board()
        if not self.game_won:
            self.set_status(f"Selected row {cell[0] + 1}, column {cell[1] + 1}.", self.colors["accent"])

    def enter_number(self, number):
        if not isinstance(number, int) or isinstance(number, bool) or not 1 <= number <= SIZE:
            self.set_status("Enter a number from 1 to 9.", "#a33b32")
            return False
        if self.selected is None:
            self.set_status("Select an empty cell before entering a number.", self.colors["muted"])
            return False
        if self.game_won:
            self.set_status("This puzzle is already solved. Start a new game to play again.", self.colors["muted"])
            return False

        row, column = self.selected
        if self.given[row][column]:
            self.set_status("That cell is a clue and cannot be changed.", self.colors["muted"])
            return False

        conflicts = SudokuPuzzle.conflicts(self.puzzle.grid, row, column, number)
        if conflicts:
            self.set_status(
                f"{number} is not allowed here: it already appears in this row, column, or 3×3 box.",
                "#a33b32",
            )
            return False

        if self.note_mode:
            notes = self.notes[row][column]
            if number in notes:
                notes.remove(number)
            else:
                notes.add(number)
            self.draw_board()
            self.set_status(f"Note {number} {'removed' if number not in notes else 'added'}.", self.colors["accent"])
            return True

        self.puzzle.grid[row][column] = number
        self.notes[row][column].clear()
        self.checked = False
        if self.is_complete():
            self.game_won = True
            elapsed = self._elapsed_seconds()
            self.set_status(f"Solved! Excellent work — {self._format_time(elapsed)}.", "#287653")
        else:
            self.set_status(f"{number} entered.", self.colors["accent"])
        self.draw_board()
        return True

    def erase_cell(self):
        if self.selected is None or self.game_won:
            return
        row, column = self.selected
        if self.given[row][column]:
            self.set_status("Clue cells cannot be erased.", self.colors["muted"])
            return
        self.puzzle.grid[row][column] = 0
        self.notes[row][column].clear()
        self.checked = False
        self.draw_board()
        self.set_status("Cell cleared.", self.colors["accent"])

    def toggle_notes(self):
        self.note_mode = not self.note_mode
        label = "Notes: On" if self.note_mode else "Notes: Off"
        self.notes_button.configure(text=label)
        self.set_status(
            "Notes mode: choose a cell, then a number." if self.note_mode else "Number entry mode.",
            self.colors["accent"],
        )

    def check_board(self):
        if self.game_won:
            return
        self.checked = True
        incorrect = sum(
            self.puzzle.grid[row][column] != 0
            and not self.given[row][column]
            and self.puzzle.grid[row][column] != self.puzzle.solution[row][column]
            for row in range(SIZE)
            for column in range(SIZE)
        )
        self.mistakes = incorrect
        self.draw_board()
        if incorrect:
            self.set_status(f"Found {incorrect} incorrect entr{'y' if incorrect == 1 else 'ies'} (highlighted).", "#a33b32")
        else:
            self.set_status("All filled numbers are correct so far.", "#287653")
        if self.is_complete():
            self.game_won = True
            self.set_status(f"Solved! Excellent work — {self.elapsed.get()}.", "#287653")

    def is_complete(self):
        return self.puzzle.grid == self.puzzle.solution

    def _elapsed_seconds(self):
        return int(monotonic() - self.started_at)

    @staticmethod
    def _format_time(seconds):
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def _update_timer(self):
        self.elapsed.set(self._format_time(self._elapsed_seconds()))
        if not self.game_won:
            self._timer_job = self.root.after(1000, self._update_timer)

    def on_key(self, event):
        if len(event.char) == 1 and event.char in "123456789":
            self.enter_number(int(event.char))
            return "break"
        if event.keysym in ("BackSpace", "Delete"):
            self.erase_cell()
            return "break"
        if event.keysym.lower() == "n":
            self.toggle_notes()
            return "break"
        if event.keysym in ("Up", "Down", "Left", "Right"):
            if self.selected is None:
                self.selected = (0, 0)
            else:
                row, column = self.selected
                row += -1 if event.keysym == "Up" else 1 if event.keysym == "Down" else 0
                column += -1 if event.keysym == "Left" else 1 if event.keysym == "Right" else 0
                self.selected = (max(0, min(8, row)), max(0, min(8, column)))
            self.draw_board()
            return "break"
        if event.char and event.char.isprintable():
            self.enter_number(event.char)
            return "break"

    def on_canvas_resize(self, event):
        if event.widget is self.canvas:
            self.draw_board()


def main():
    root = tk.Tk()
    SudokuApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
