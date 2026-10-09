import json

from sudoku_logic import DIFFICULTIES, SIZE, SudokuPuzzle


_puzzle = SudokuPuzzle()
_difficulty = "Easy"
_given = [[False] * SIZE for _ in range(SIZE)]
_notes = [[set() for _ in range(SIZE)] for _ in range(SIZE)]
_selected = None
_note_mode = False
_checked = False
_mistakes = 0
_game_won = False
_status = "Loading Sudoku..."
_status_kind = "info"


def _set_status(text, kind="info"):
    global _status, _status_kind
    _status = text
    _status_kind = kind


def _valid_coordinate(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer.")
    if not 0 <= value < SIZE:
        raise ValueError(f"{name} must be between 0 and {SIZE - 1}.")


def new_game(difficulty="Easy"):
    """Generate a new unique puzzle using the shared Python Sudoku solver."""
    global _difficulty, _given, _notes, _selected, _note_mode
    global _checked, _mistakes, _game_won

    if difficulty not in DIFFICULTIES:
        raise ValueError(f"Difficulty must be one of: {', '.join(DIFFICULTIES)}.")

    _difficulty = difficulty
    _puzzle.generate(_difficulty)
    _given = [[value != 0 for value in row] for row in _puzzle.grid]
    _notes = [[set() for _ in range(SIZE)] for _ in range(SIZE)]
    _selected = None
    _note_mode = False
    _checked = False
    _mistakes = 0
    _game_won = False
    _set_status(f"{_difficulty} puzzle — select a cell to begin.")


def select_cell(row, column):
    """Select a board cell and return whether the selection was accepted."""
    global _selected
    _valid_coordinate(row, "Row")
    _valid_coordinate(column, "Column")
    _selected = (row, column)
    if not _game_won:
        _set_status(f"Selected row {row + 1}, column {column + 1}.")
    return True


def enter_number(number):
    """Enter a value or toggle a pencil note in the selected cell."""
    global _checked, _game_won

    if isinstance(number, bool) or not isinstance(number, int) or not 1 <= number <= SIZE:
        raise ValueError("Enter a number from 1 to 9.")
    if _selected is None:
        _set_status("Select an empty cell before entering a number.", "muted")
        return False
    if _game_won:
        _set_status("This puzzle is already solved. Start a new game to play again.", "muted")
        return False

    row, column = _selected
    if _given[row][column]:
        _set_status("That cell is a clue and cannot be changed.", "muted")
        return False

    if SudokuPuzzle.conflicts(_puzzle.grid, row, column, number):
        _set_status(
            f"{number} is not allowed here: it already appears in this row, column, or 3×3 box.",
            "error",
        )
        return False

    if _note_mode:
        notes = _notes[row][column]
        if number in notes:
            notes.remove(number)
            action = "removed"
        else:
            notes.add(number)
            action = "added"
        _set_status(f"Note {number} {action}.")
        return True

    _puzzle.grid[row][column] = number
    _notes[row][column].clear()
    _checked = False
    if _puzzle.grid == _puzzle.solution:
        _game_won = True
        _set_status("Solved! Excellent work.", "success")
    else:
        _set_status(f"{number} entered.")
    return True


def erase_cell():
    """Clear the selected editable cell."""
    global _checked

    if _selected is None or _game_won:
        return False

    row, column = _selected
    if _given[row][column]:
        _set_status("Clue cells cannot be erased.", "muted")
        return False

    _puzzle.grid[row][column] = 0
    _notes[row][column].clear()
    _checked = False
    _set_status("Cell cleared.")
    return True


def toggle_notes():
    """Turn pencil-note entry on or off."""
    global _note_mode
    _note_mode = not _note_mode
    _set_status("Notes mode: choose a cell, then a number." if _note_mode else "Number entry mode.")
    return _note_mode


def check_board():
    """Mark entries that differ from the solution and report the result."""
    global _checked, _mistakes, _game_won
    if _game_won:
        return

    _checked = True
    _mistakes = sum(
        _puzzle.grid[row][column] != 0
        and not _given[row][column]
        and _puzzle.grid[row][column] != _puzzle.solution[row][column]
        for row in range(SIZE)
        for column in range(SIZE)
    )
    if _mistakes:
        _set_status(
            f"Found {_mistakes} incorrect entr{'y' if _mistakes == 1 else 'ies'} (highlighted).",
            "error",
        )
    else:
        _set_status("All filled numbers are correct so far.", "success")

    if _puzzle.grid == _puzzle.solution:
        _game_won = True
        _set_status("Solved! Excellent work.", "success")


def get_game_state():
    """Return JSON-safe puzzle state for the browser interface."""
    wrong_cells = []
    if _checked:
        wrong_cells = [
            [row, column]
            for row in range(SIZE)
            for column in range(SIZE)
            if _puzzle.grid[row][column] != 0
            and not _given[row][column]
            and _puzzle.grid[row][column] != _puzzle.solution[row][column]
        ]

    state = {
        "grid": _puzzle.grid,
        "given": _given,
        "notes": [
            [sorted(cell_notes) for cell_notes in row]
            for row in _notes
        ],
        "selected": _selected,
        "note_mode": _note_mode,
        "checked": _checked,
        "wrong_cells": wrong_cells,
        "mistakes": _mistakes,
        "game_won": _game_won,
        "difficulty": _difficulty,
        "status": _status,
        "status_kind": _status_kind,
    }
    return json.dumps(state)


def main():
    """Serve the browser Sudoku game locally and open it in Google Chrome."""
    from functools import partial
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    import os
    from pathlib import Path
    import shutil
    import subprocess

    game_directory = Path(__file__).resolve().parent
    page_file = game_directory / "sudoku.html"
    if not page_file.is_file():
        raise FileNotFoundError(f"Could not find the Sudoku page: {page_file}")

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
    game_url = f"http://127.0.0.1:{server.server_port}/sudoku.html"

    try:
        subprocess.Popen([chrome_path, game_url], close_fds=True)
        print(f"Sudoku opened in Chrome: {game_url}")
        print("Leave this window open while playing. Press Ctrl+C to stop the local server.")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSudoku server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
