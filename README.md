# Hangman game

Run the game by executing the `hangman` script from this folder:

```bash
python -m pip install -r hangman-requirements.txt
python hangman
```

The game uses the `wordfreq` package's 1,000 most common English words and randomly chooses from those that are 4–9 letters long. The list is available locally after installation, so an internet connection is not needed while playing. During a round, type `quit` to reveal the word and end the round.

## Checkers

Run the human-vs-computer checkers game with:

```bash
python checkers.py
```

It uses Tkinter from Python's standard library. Red moves first; captures are mandatory, and a piece must continue a capture sequence when another jump is available.

## Chess

Install the chess-rules library and start the human-vs-computer chess game with:

```bash
python -m pip install -r chess-requirements.txt
python chess_game.py
```

The game uses Tkinter for its resizable board and `python-chess` for legal moves, check, castling, en passant, promotion, checkmate, and draws. White moves first.

## Sudoku

Run the Sudoku game with:

```bash
python sudoku.py
```

It uses Tkinter and the Python standard library only. Choose a difficulty, enter numbers with the keyboard or number pad, toggle pencil notes, and use **Check** to highlight incorrect entries.

## Mastermind

Run the Mastermind code-breaking game with:

```bash
python mastermind.py
```

Choose four colored pegs (repeats are allowed) and submit your guess. Feedback shows how many pegs have the right color and position and how many have the right color in another position. The game uses Tkinter and the Python standard library only.
