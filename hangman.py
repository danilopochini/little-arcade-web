import random
from wordfreq import top_n_list


COMMON_WORDS = [
    word.upper()
    for word in top_n_list("en", 1000)
    if word.isascii() and word.isalpha() and 4 <= len(word) <= 9
]
MAX_WRONG_GUESSES = 10


def choose_word():
    return random.choice(COMMON_WORDS)


def reveal_word(secret_word, guessed_letters):
    return " ".join(letter if letter in guessed_letters else "_" for letter in secret_word)


class HangmanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hangman")
        self.root.geometry("760x540")
        self.root.minsize(680, 500)
        self.root.configure(bg="#eee7dc")

        self.colors = {
            "background": "#eee7dc",
            "panel": "#faf6ef",
            "text": "#302820",
            "muted": "#827466",
            "accent": "#337a8e",
            "accent_dark": "#245766",
            "wood": "#8f5e3d",
            "wrong": "#c6534b",
            "correct": "#38856d",
        }
        self.secret_word = ""
        self.guessed_letters = set()
        self.wrong_guesses = 0
        self.finished = False
        self.status = tk.StringVar()
        self.word_display = tk.StringVar()
        self.used_display = tk.StringVar()
        self.guesses_display = tk.StringVar()

        self._build_widgets()
        self.new_game()

    def _build_widgets(self):
        outer = tk.Frame(self.root, bg=self.colors["background"], padx=20, pady=16)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg=self.colors["background"])
        header.pack(fill="x", pady=(0, 14))
        logo = tk.Canvas(
            header,
            width=42,
            height=42,
            bg=self.colors["background"],
            highlightthickness=0,
        )
        logo.pack(side="left", padx=(0, 10))
        logo.create_oval(3, 3, 39, 39, fill=self.colors["accent"], outline="")
        logo.create_text(21, 21, text="?", fill="white", font=("Georgia", 24, "bold"))

        title = tk.Frame(header, bg=self.colors["background"])
        title.pack(side="left")
        tk.Label(
            title,
            text="HANGMAN",
            font=("Georgia", 20, "bold"),
            fg=self.colors["text"],
            bg=self.colors["background"],
        ).pack(anchor="w")
        tk.Label(
            title,
            text="GUESS THE HIDDEN WORD",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["background"],
        ).pack(anchor="w")

        content = tk.Frame(outer, bg=self.colors["background"])
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        drawing_panel = tk.Frame(
            content, bg=self.colors["panel"], padx=8, pady=8
        )
        drawing_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.canvas = tk.Canvas(
            drawing_panel,
            width=380,
            height=360,
            bg=self.colors["panel"],
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._draw_hangman)

        side = tk.Frame(content, bg=self.colors["background"])
        side.grid(row=0, column=1, sticky="nsew")

        status_panel = tk.Frame(side, bg=self.colors["panel"], padx=12, pady=10)
        status_panel.pack(fill="x", pady=(0, 10))
        tk.Label(
            status_panel,
            textvariable=self.status,
            font=("Segoe UI", 10, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
            anchor="w",
            justify="left",
            wraplength=250,
        ).pack(fill="x")
        tk.Label(
            status_panel,
            textvariable=self.guesses_display,
            font=("Segoe UI", 9),
            fg=self.colors["muted"],
            bg=self.colors["panel"],
            anchor="w",
        ).pack(fill="x", pady=(5, 0))

        word_panel = tk.Frame(side, bg=self.colors["panel"], padx=12, pady=14)
        word_panel.pack(fill="x", pady=(0, 10))
        tk.Label(
            word_panel,
            text="HIDDEN WORD",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["panel"],
        ).pack(anchor="w")
        tk.Label(
            word_panel,
            textvariable=self.word_display,
            font=("Consolas", 19, "bold"),
            fg=self.colors["text"],
            bg=self.colors["panel"],
            wraplength=270,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        guess_panel = tk.Frame(side, bg=self.colors["panel"], padx=12, pady=12)
        guess_panel.pack(fill="x", pady=(0, 10))
        tk.Label(
            guess_panel,
            text="YOUR GUESS (or type QUIT to reveal)",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["panel"],
        ).pack(anchor="w")
        guess_row = tk.Frame(guess_panel, bg=self.colors["panel"])
        guess_row.pack(fill="x", pady=(7, 0))
        self.guess_entry = tk.Entry(
            guess_row,
            font=("Segoe UI", 15, "bold"),
            justify="center",
            width=8,
            relief="solid",
            bd=1,
        )
        self.guess_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.guess_entry.bind("<Return>", self.submit_guess)
        self._button(
            guess_row, "Guess", self.submit_guess, primary=True
        ).pack(side="left", padx=(7, 0), fill="y")

        used_panel = tk.Frame(side, bg=self.colors["panel"], padx=12, pady=10)
        used_panel.pack(fill="both", expand=True)
        tk.Label(
            used_panel,
            text="USED LETTERS",
            font=("Segoe UI", 8, "bold"),
            fg=self.colors["muted"],
            bg=self.colors["panel"],
        ).pack(anchor="w")
        tk.Label(
            used_panel,
            textvariable=self.used_display,
            font=("Segoe UI", 10),
            fg=self.colors["text"],
            bg=self.colors["panel"],
            anchor="nw",
            justify="left",
            wraplength=250,
        ).pack(fill="both", expand=True, pady=(6, 0))

        self.new_game_button = self._button(outer, "New Game", self.new_game)
        self.new_game_button.pack(anchor="e", pady=(12, 0))

    def _button(self, parent, text, command, primary=False):
        background = (
            self.colors["accent"] if primary else self.colors["panel"]
        )
        foreground = "white" if primary else self.colors["text"]
        active_background = (
            self.colors["accent_dark"] if primary else "#e7dfd3"
        )
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
            pady=7,
            cursor="hand2",
        )

    def _draw_hangman(self, _event=None):
        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        x = lambda fraction: width * fraction
        y = lambda fraction: height * fraction
        wood = self.colors["wood"]
        ink = self.colors["text"]

        self.canvas.create_line(x(0.12), y(0.88), x(0.68), y(0.88), fill=wood, width=7)
        self.canvas.create_line(x(0.28), y(0.88), x(0.28), y(0.12), fill=wood, width=7)
        self.canvas.create_line(x(0.28), y(0.12), x(0.64), y(0.12), fill=wood, width=7)
        self.canvas.create_line(x(0.64), y(0.12), x(0.64), y(0.22), fill=wood, width=5)

        parts = (
            lambda: self.canvas.create_oval(
                x(0.58), y(0.22), x(0.70), y(0.36), outline=ink, width=3
            ),
            lambda: self.canvas.create_line(
                x(0.64), y(0.36), x(0.64), y(0.58), fill=ink, width=3
            ),
            lambda: self.canvas.create_line(
                x(0.64), y(0.41), x(0.55), y(0.50), fill=ink, width=3
            ),
            lambda: self.canvas.create_line(
                x(0.64), y(0.41), x(0.73), y(0.50), fill=ink, width=3
            ),
            lambda: self.canvas.create_line(
                x(0.64), y(0.58), x(0.55), y(0.72), fill=ink, width=3
            ),
            lambda: self.canvas.create_line(
                x(0.64), y(0.58), x(0.73), y(0.72), fill=ink, width=3
            ),
            lambda: self.canvas.create_oval(
                x(0.605), y(0.265), x(0.615), y(0.275), fill=ink, outline=ink
            ),
            lambda: self.canvas.create_oval(
                x(0.665), y(0.265), x(0.675), y(0.275), fill=ink, outline=ink
            ),
            lambda: self.canvas.create_line(
                x(0.615), y(0.325), x(0.665), y(0.325), fill=ink, width=2
            ),
            lambda: self.canvas.create_line(
                x(0.64), y(0.29), x(0.625), y(0.31), fill=ink, width=2
            ),
        )
        for part in parts[: self.wrong_guesses]:
            part()

    def _refresh_display(self):
        reveal_all = self.finished and not set(self.secret_word).issubset(
            self.guessed_letters
        )
        letters = (
            set(self.secret_word) if reveal_all else self.guessed_letters
        )
        self.word_display.set(reveal_word(self.secret_word, letters))
        self.used_display.set(
            ", ".join(sorted(self.guessed_letters)) or "No letters guessed yet"
        )
        self.guesses_display.set(
            f"Incorrect guesses: {self.wrong_guesses}/{MAX_WRONG_GUESSES}"
        )
        self._draw_hangman()

    def new_game(self):
        self.secret_word = choose_word()
        self.guessed_letters = set()
        self.wrong_guesses = 0
        self.finished = False
        self.status.set("Guess a letter to reveal the word.")
        self.guess_entry.configure(state="normal")
        self.guess_entry.delete(0, tk.END)
        self._refresh_display()
        self.guess_entry.focus_set()

    def submit_guess(self, _event=None):
        if self.finished:
            return

        guess = self.guess_entry.get().strip().upper()
        self.guess_entry.delete(0, tk.END)
        if guess == "QUIT":
            self.finished = True
            self.status.set(f"You quit! The word was {self.secret_word}.")
            self.guess_entry.configure(state="disabled")
            self._refresh_display()
            return
        if len(guess) != 1 or not guess.isalpha():
            self.status.set("Enter one letter from A to Z.")
            self.guess_entry.focus_set()
            return
        if guess in self.guessed_letters:
            self.status.set(f"You already guessed {guess}. Try another letter.")
            self.guess_entry.focus_set()
            return

        self.guessed_letters.add(guess)
        if guess in self.secret_word:
            self.status.set(f"Correct! {guess} is in the word.")
        else:
            self.wrong_guesses += 1
            self.status.set(f"{guess} is not in the word.")

        if set(self.secret_word).issubset(self.guessed_letters):
            self.finished = True
            self.status.set(f"You won! The word was {self.secret_word}.")
        elif self.wrong_guesses >= MAX_WRONG_GUESSES:
            self.finished = True
            self.status.set(f"Game over! The word was {self.secret_word}.")

        if self.finished:
            self.guess_entry.configure(state="disabled")
        self._refresh_display()
        if not self.finished:
            self.guess_entry.focus_set()


def main():
    global tk
    import tkinter as tk

    root = tk.Tk()
    HangmanApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
