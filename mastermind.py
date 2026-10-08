import random


CODE_LENGTH = 4
MAX_TURNS = 10
PALETTE = [
    ("Ruby", "#dc4054"),
    ("Tangerine", "#ed8a35"),
    ("Sunshine", "#e7c43c"),
    ("Jade", "#35a879"),
    ("Ocean", "#3986cb"),
    ("Violet", "#8958b5"),
]


class MastermindGame:
    """Secret-code generation and exact/color-only feedback rules."""

    def __init__(self):
        self.new_game()

    def new_game(self):
        self.secret = tuple(random.randrange(len(PALETTE)) for _ in range(CODE_LENGTH))
        self.guesses = []
        self.feedback = []
        self.finished = False
        self.won = False

    @staticmethod
    def score_guess(secret, guess):
        """Score exact matches first, then color matches without double-counting."""
        exact = sum(secret_pin == guess_pin for secret_pin, guess_pin in zip(secret, guess))
        remaining_secret = []
        remaining_guess = []
        for secret_pin, guess_pin in zip(secret, guess):
            if secret_pin != guess_pin:
                remaining_secret.append(secret_pin)
                remaining_guess.append(guess_pin)

        color_only = sum(
            min(remaining_secret.count(color), remaining_guess.count(color))
            for color in set(remaining_secret)
        )
        return exact, color_only

    def submit_guess(self, guess):
        if self.finished:
            return "finished", (0, 0)
        if len(guess) != CODE_LENGTH or any(
            not isinstance(pin, int) or isinstance(pin, bool) or not 0 <= pin < len(PALETTE)
            for pin in guess
        ):
            return "invalid", (0, 0)

        guess = tuple(guess)
        result = self.score_guess(self.secret, guess)
        self.guesses.append(guess)
        self.feedback.append(result)
        if result[0] == CODE_LENGTH:
            self.finished = True
            self.won = True
            return "won", result
        if len(self.guesses) == MAX_TURNS:
            self.finished = True
            return "lost", result
        return "continue", result


class MastermindApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mastermind")
        self.root.resizable(True, True)
        self.game = MastermindGame()
        self.current_guess = []
        self.cell_size = 48
        self.row_height = 50
        self.left_margin = 24
        self.top_margin = 24
        self.display_row_height = self.row_height

        self.colors = {
            "background": "#e8e0d3",
            "panel": "#fbf7f0",
            "wood": "#6e4730",
            "wood_light": "#b47c50",
            "board": "#263845",
            "board_light": "#334c5b",
            "board_edge": "#142630",
            "hole": "#14242e",
            "hole_rim": "#405866",
            "text": "#302820",
            "muted": "#827466",
            "accent": "#337a8e",
            "accent_dark": "#245766",
            "exact": "#171b20",
            "color_only": "#fff2d6",
            "current": "#78cfb3",
        }
        self.status = tk.StringVar()
        self._build_widgets()
        self._fit_window_to_screen()
        self.new_game()

    def _build_widgets(self):
        outer = tk.Frame(self.root, bg=self.colors["background"], padx=20, pady=12)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=self.colors["background"])
        header.pack(fill="x", pady=(0, 7))
        logo = tk.Canvas(
            header,
            width=42,
            height=42,
            bg=self.colors["background"],
            highlightthickness=0,
        )
        logo.pack(side="left", padx=(0, 10))
        for index, color in enumerate(
            (PALETTE[0][1], PALETTE[2][1], PALETTE[3][1], PALETTE[4][1])
        ):
            row, column = divmod(index, 2)
            x, y = 4 + column * 18, 4 + row * 18
            logo.create_oval(x, y, x + 15, y + 15, fill=color, outline="#fff4e6", width=1)
        title = tk.Frame(header, bg=self.colors["background"])
        title.pack(side="left")
        tk.Label(
            title,
            text="MASTERMIND",
            font=("Georgia", 20, "bold"),
            fg=self.colors["text"],
            bg=self.colors["background"],
        ).pack(anchor="w")
        tk.Label(
            title,
            text="CRACK THE CODE",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["background"],
        ).pack(anchor="w", pady=(1, 0))

        info = tk.Frame(outer, bg=self.colors["panel"], padx=11, pady=7)
        info.pack(fill="x", pady=(0, 7))
        self.status_dot = tk.Canvas(
            info, width=16, height=16, bg=self.colors["panel"], highlightthickness=0
        )
        self.status_dot.pack(side="left", padx=(0, 7))
        self.status_label = tk.Label(
            info,
            textvariable=self.status,
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
            anchor="w",
        )
        self.status_label.pack(side="left", fill="x", expand=True)
        self.turn_label = tk.Label(
            info,
            font=("Segoe UI", 9, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["panel"],
        )
        self.turn_label.pack(side="right")

        self.canvas = tk.Canvas(
            outer,
            width=440,
            height=520,
            bg=self.colors["background"],
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        palette_row = tk.Frame(outer, bg=self.colors["panel"], padx=9, pady=7)
        palette_row.pack(fill="x", pady=(7, 0))
        self._build_palette(palette_row)

        actions = tk.Frame(outer, bg=self.colors["background"])
        actions.pack(fill="x", pady=(8, 0))
        self._button(actions, "Clear", self.clear_guess).pack(side="left")
        self._button(actions, "Submit Guess", self.submit_guess, primary=True).pack(
            side="left", padx=6
        )
        self._button(actions, "New Game", self.new_game).pack(side="right")

        legend = tk.Frame(outer, bg=self.colors["background"])
        legend.pack(pady=(7, 0))
        for color, label in (
            (self.colors["exact"], "Right color & place"),
            (self.colors["color_only"], "Right color, different place"),
        ):
            item = tk.Frame(legend, bg=self.colors["background"])
            item.pack(side="left", padx=7)
            marker = tk.Canvas(
                item, width=15, height=15, bg=self.colors["background"], highlightthickness=0
            )
            marker.pack(side="left", padx=(0, 4))
            marker.create_oval(2, 2, 13, 13, fill=color, outline=self.colors["wood"])
            tk.Label(
                item,
                text=label,
                font=("Segoe UI", 8),
                fg=self.colors["muted"],
                bg=self.colors["background"],
            ).pack(side="left")

    def _build_palette(self, parent):
        for index, (name, color) in enumerate(PALETTE):
            button = tk.Frame(parent, bg=self.colors["panel"], padx=4, pady=1, cursor="hand2")
            button.pack(side="left", fill="x", expand=True)
            peg = tk.Canvas(
                button,
                width=30,
                height=28,
                bg=self.colors["panel"],
                highlightthickness=0,
                cursor="hand2",
            )
            peg.pack()
            peg.create_oval(4, 6, 26, 28, fill="#9f9383", outline="")
            peg.create_oval(4, 4, 26, 26, fill=color, outline="#33414a", width=1)
            peg.create_oval(8, 7, 15, 12, fill="#ffffff", outline="")
            peg.bind("<Button-1>", lambda _event, pin=index: self.add_pin(pin))
            label = tk.Label(
                button,
                text=f"{index + 1}  {name}",
                font=("Segoe UI", 8, "bold"),
                fg=self.colors["text"],
                bg=self.colors["panel"],
                cursor="hand2",
            )
            label.pack()
            label.bind("<Button-1>", lambda _event, pin=index: self.add_pin(pin))

    def _button(self, parent, text, command, primary=False):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9, "bold"),
            fg="white",
            bg=self.colors["accent"] if primary else self.colors["wood"],
            activebackground=self.colors["accent_dark"] if primary else self.colors["wood_light"],
            activeforeground="white",
            relief="flat",
            padx=11,
            pady=7,
            cursor="hand2",
        )

    def _fit_window_to_screen(self):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        fixed_height = self.root.winfo_reqheight() - self.canvas.winfo_reqheight()
        available_height = max(450, screen_height - 55)
        self.top_margin = 14
        self.left_margin = 24
        available_for_board = available_height - fixed_height - 2 * self.top_margin
        self.row_height = min(43, max(33, available_for_board // (MAX_TURNS + 2)))
        self.cell_size = min(44, max(34, (screen_width - 100) // CODE_LENGTH - 12))
        self.canvas.configure(
            width=max(400, min(500, screen_width - 70)),
            height=2 * self.top_margin + (MAX_TURNS + 2) * self.row_height,
        )
        self.root.update_idletasks()
        width = min(self.root.winfo_reqwidth(), screen_width - 30)
        height = min(self.root.winfo_reqheight(), available_height)
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def new_game(self):
        self.game.new_game()
        self.current_guess = []
        self.set_status("Choose four colors to make your first guess.", self.colors["accent"])
        self.draw_board()
        self._update_turn_label()

    def set_status(self, text, color=None):
        self.status.set(text)
        self.status_label.configure(fg=color or self.colors["text"])
        self.status_dot.delete("all")
        self.status_dot.create_oval(
            3,
            3,
            13,
            13,
            fill=color or self.colors["accent"],
            outline="",
        )

    def _update_turn_label(self):
        if self.game.finished:
            label = "CODE CRACKED" if self.game.won else "CODE REVEALED"
        else:
            label = f"GUESS {len(self.game.guesses) + 1} / {MAX_TURNS}"
        self.turn_label.configure(text=label)

    def add_pin(self, pin):
        if self.game.finished:
            self.set_status("Start a new game to play again.", self.colors["muted"])
            return
        if len(self.current_guess) >= CODE_LENGTH:
            self.set_status("Your guess already has four pegs. Submit it or clear it.", self.colors["muted"])
            return
        self.current_guess.append(pin)
        self.set_status(f"{len(self.current_guess)} of {CODE_LENGTH} pegs selected.", self.colors["accent"])
        self.draw_board()

    def clear_guess(self):
        if self.game.finished:
            return
        self.current_guess.clear()
        self.set_status("Guess cleared. Choose four colors.", self.colors["accent"])
        self.draw_board()

    def submit_guess(self):
        if self.game.finished:
            self.set_status("Start a new game to play again.", self.colors["muted"])
            return
        if len(self.current_guess) != CODE_LENGTH:
            missing = CODE_LENGTH - len(self.current_guess)
            self.set_status(f"Choose {missing} more peg{'s' if missing != 1 else ''} before submitting.", "#a33b32")
            return

        result, feedback = self.game.submit_guess(self.current_guess)
        self.current_guess = []
        self._update_turn_label()
        self.draw_board()
        if result == "won":
            self.set_status("Code cracked! You win — click New Game to play again.", "#287653")
        elif result == "lost":
            secret = "  ".join(PALETTE[pin][0] for pin in self.game.secret)
            self.set_status(f"Out of guesses! The code was {secret}.", "#a33b32")
        else:
            exact, color_only = feedback
            self.set_status(
                f"{exact} exact match{'es' if exact != 1 else ''}, {color_only} right color{'s' if color_only != 1 else ''} in another spot.",
                self.colors["accent_dark"],
            )

    def draw_board(self):
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), self.canvas.winfo_reqwidth())
        height = max(self.canvas.winfo_height(), self.canvas.winfo_reqheight())
        row_height = max(29, min(43, (height - 70) // MAX_TURNS))
        pin_radius = max(11, min(15, row_height * 0.34))
        board_width = min(width - 16, 480)
        left = (width - board_width) / 2
        board_height = 70 + MAX_TURNS * row_height
        top = max(8, (height - board_height) / 2)
        code_start = left + 64
        code_spacing = 42
        feedback_left = left + board_width - 77
        rows_top = top + 67
        self.display_row_height = row_height
        self.display_cell_size = pin_radius * 2
        self.board_left = left
        self.board_top = rows_top

        self.canvas.create_rectangle(
            left + 3,
            top + 4,
            left + board_width + 3,
            top + board_height + 4,
            fill=self.colors["board_edge"],
            outline="",
        )
        self.canvas.create_rectangle(
            left,
            top,
            left + board_width,
            top + board_height,
            fill=self.colors["board"],
            outline=self.colors["wood"],
            width=3,
        )

        self.canvas.create_text(
            code_start + code_spacing * 1.5,
            top + 12,
            text="SECRET CODE",
            fill="#f1ddc2",
            font=("Segoe UI", 8, "bold"),
        )
        self.canvas.create_text(
            feedback_left + 24,
            top + 12,
            text="CODE FEEDBACK",
            fill="#f1ddc2",
            font=("Segoe UI", 8, "bold"),
        )
        if self.game.finished:
            for position, pin in enumerate(self.game.secret):
                self._draw_pin(
                    code_start + position * code_spacing,
                    top + 39,
                    pin_radius * 0.77,
                    PALETTE[pin][1],
                )
        else:
            self.canvas.create_rectangle(
                code_start - 22,
                top + 22,
                code_start + 3 * code_spacing + 22,
                top + 56,
                fill=self.colors["board_edge"],
                outline=self.colors["hole_rim"],
                width=1,
            )
            self.canvas.create_text(
                code_start + 1.5 * code_spacing,
                top + 39,
                text="HIDDEN",
                fill="#c8d2d6",
                font=("Segoe UI", 8, "bold"),
            )
            for position in range(CODE_LENGTH):
                center_x = code_start + position * code_spacing
                self.canvas.create_oval(
                    center_x - 5,
                    top + 34,
                    center_x + 5,
                    top + 44,
                    fill=self.colors["hole_rim"],
                    outline="",
                )

        self.canvas.create_line(
            left + 12, top + 59, left + board_width - 12, top + 59,
            fill=self.colors["hole_rim"], width=1
        )
        self.canvas.create_text(
            code_start + code_spacing * 1.5,
            top + 63,
            text="GUESS PEGS",
            fill="#c8d2d6",
            font=("Segoe UI", 7, "bold"),
        )
        self.canvas.create_text(
            feedback_left + 24,
            top + 63,
            text="KEY PEGS",
            fill="#c8d2d6",
            font=("Segoe UI", 7, "bold"),
        )
        for turn in range(MAX_TURNS):
            y = rows_top + turn * row_height + row_height / 2
            is_current = turn == len(self.game.guesses) and not self.game.finished
            row_outline = self.colors["current"] if is_current else self.colors["board_light"]
            self.canvas.create_rectangle(
                left + 9,
                y - row_height / 2 + 2,
                left + board_width - 9,
                y + row_height / 2 - 2,
                fill=self.colors["board_light"] if is_current else self.colors["board"],
                outline=row_outline,
                width=1 if is_current else 0,
            )
            self.canvas.create_text(
                left + 25,
                y,
                text=f"{turn + 1:02d}",
                fill="#b8c8cf",
                font=("Consolas", 8, "bold"),
            )

            if turn < len(self.game.guesses):
                guess = self.game.guesses[turn]
                for position, pin in enumerate(guess):
                    center_x = code_start + position * code_spacing
                    self._draw_pin(center_x, y, pin_radius, PALETTE[pin][1])
                self._draw_feedback(feedback_left, y, self.game.feedback[turn], pin_radius * 2)
            elif turn == len(self.game.guesses):
                for position, pin in enumerate(self.current_guess):
                    center_x = code_start + position * code_spacing
                    self._draw_pin(center_x, y, pin_radius, PALETTE[pin][1])
                for position in range(len(self.current_guess), CODE_LENGTH):
                    center_x = code_start + position * code_spacing
                    self._draw_pin(center_x, y, pin_radius, self.colors["hole"], hollow=True)
                for position in range(CODE_LENGTH):
                    self._draw_feedback_socket(feedback_left, y, position, pin_radius * 2)
            else:
                for position in range(CODE_LENGTH):
                    center_x = code_start + position * code_spacing
                    self._draw_pin(center_x, y, pin_radius, self.colors["hole"], hollow=True)
                    self._draw_feedback_socket(feedback_left, y, position, pin_radius * 2)

    def _draw_pin(self, center_x, center_y, radius, color, hollow=False):
        self.canvas.create_oval(
            center_x - radius,
            center_y - radius + 2,
            center_x + radius,
            center_y + radius + 2,
            fill="#66513c",
            outline="",
        )
        self.canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            fill=self.colors["hole"] if hollow else color,
            outline=self.colors["hole_rim"] if hollow else "#18232a",
            width=2 if hollow else 1,
        )
        if not hollow:
            self.canvas.create_oval(
                center_x - radius * 0.55,
                center_y - radius * 0.6,
                center_x + radius * 0.25,
                center_y - radius * 0.3,
                fill="#ffffff",
                outline="",
            )

    def _draw_feedback(self, x, center_y, feedback, pin_size):
        exact, color_only = feedback
        radius = max(3, pin_size * 0.16)
        gap = max(4, pin_size * 0.22)
        grid_width = radius * 2 + gap
        start_x = x + (48 - grid_width) / 2
        start_y = center_y - (radius * 2 + gap) / 2
        for position in range(CODE_LENGTH):
            row, column = divmod(position, 2)
            marker_x = start_x + column * (radius * 2 + gap)
            marker_y = start_y + row * (radius * 2 + gap)
            self.canvas.create_oval(
                marker_x - radius,
                marker_y - radius,
                marker_x + radius,
                marker_y + radius,
                fill=self.colors["hole"],
                outline=self.colors["hole_rim"],
                width=1,
            )
        markers = [self.colors["exact"]] * exact + [self.colors["color_only"]] * color_only

        for index, color in enumerate(markers):
            row, column = divmod(index, 2)
            marker_x = start_x + column * (radius * 2 + gap)
            marker_y = start_y + row * (radius * 2 + gap)
            self.canvas.create_oval(
                marker_x - radius,
                marker_y - radius,
                marker_x + radius,
                marker_y + radius,
                fill=color,
                outline=self.colors["hole_rim"],
                width=1,
            )

    def _draw_feedback_socket(self, x, center_y, position, pin_size):
        radius = max(3, pin_size * 0.16)
        gap = max(4, pin_size * 0.22)
        start_x = x + (48 - (radius * 2 + gap)) / 2
        start_y = center_y - (radius * 2 + gap) / 2
        row, column = divmod(position, 2)
        center_x = start_x + column * (radius * 2 + gap)
        marker_y = start_y + row * (radius * 2 + gap)
        self.canvas.create_oval(
            center_x - radius,
            marker_y - radius,
            center_x + radius,
            marker_y + radius,
            fill=self.colors["hole"],
            outline=self.colors["hole_rim"],
            width=1,
        )

    def on_key(self, event):
        if event.keysym in ("BackSpace", "Delete"):
            if self.current_guess:
                self.current_guess.pop()
                self.set_status("Last peg removed.", self.colors["accent"])
                self.draw_board()
            return "break"
        if event.keysym == "Return":
            self.submit_guess()
            return "break"
        if event.char and event.char.isdigit():
            number = int(event.char)
            if 1 <= number <= len(PALETTE):
                self.add_pin(number - 1)
            else:
                self.set_status("Choose a color from 1 to 6.", "#a33b32")
            return "break"
        if event.char and event.char.isprintable():
            self.set_status("Choose a color using the palette or keys 1 to 6.", "#a33b32")
            return "break"

    def on_canvas_resize(self, event):
        if event.widget is self.canvas:
            self.draw_board()


def main():
    global tk
    import tkinter as tk

    root = tk.Tk()
    app = MastermindApp(root)
    root.bind("<KeyPress>", app.on_key)
    root.mainloop()


if __name__ == "__main__":
    main()
