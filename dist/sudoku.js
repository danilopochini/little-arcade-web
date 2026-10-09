"use strict";

const PYODIDE_VERSION = "314.0.7";
const PYODIDE_SCRIPT_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.js`;
const PYTHON_MODULE = "sudoku_browser";
const SIZE = 9;

const boardElement = document.querySelector("#sudoku-board");
const statusElement = document.querySelector("#game-status");
const statusBar = document.querySelector("#status-bar");
const difficultySelect = document.querySelector("#difficulty");
const newGameButton = document.querySelector("#new-game");
const eraseButton = document.querySelector("#erase");
const notesButton = document.querySelector("#notes");
const checkButton = document.querySelector("#check");
const numberPad = document.querySelector("#number-pad");

let pyodide = null;
let gameReady = false;
let runtimeError = "";
let gameState = {
  grid: Array.from({ length: SIZE }, () => Array(SIZE).fill(0)),
  given: Array.from({ length: SIZE }, () => Array(SIZE).fill(false)),
  notes: Array.from({ length: SIZE }, () => Array.from({ length: SIZE }, () => [])),
  selected: null,
  note_mode: false,
  checked: false,
  wrong_cells: [],
  mistakes: 0,
  game_won: false,
  difficulty: "Easy",
  status: "Loading Sudoku...",
  status_kind: "info",
};

function loadPyodideScript() {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = PYODIDE_SCRIPT_URL;
    script.async = true;
    script.onload = resolve;
    script.onerror = () => reject(new Error("The Pyodide script could not be downloaded."));
    document.head.append(script);
  });
}

function readGameState() {
  gameState = JSON.parse(pyodide.runPython(`${PYTHON_MODULE}.get_game_state()`));
}

function runGameAction(expression) {
  try {
    runtimeError = "";
    pyodide.runPython(expression);
    readGameState();
    render();
  } catch (error) {
    runtimeError = `Sudoku could not complete that action: ${error.message || error}`;
    render();
  }
}

function isSelected(row, column) {
  return gameState.selected
    && gameState.selected[0] === row
    && gameState.selected[1] === column;
}

function render() {
  statusElement.textContent = runtimeError || gameState.status;
  statusBar.dataset.state = runtimeError ? "error" : gameState.status_kind;

  const selected = gameState.selected;
  const selectedValue = selected ? gameState.grid[selected[0]][selected[1]] : 0;
  const wrongCells = new Set(gameState.wrong_cells.map(([row, column]) => `${row},${column}`));
  boardElement.replaceChildren();

  for (let row = 0; row < SIZE; row += 1) {
    for (let column = 0; column < SIZE; column += 1) {
      const cell = document.createElement("button");
      cell.type = "button";
      cell.className = "sudoku-cell";
      cell.setAttribute("role", "gridcell");
      cell.dataset.row = String(row);
      cell.dataset.column = String(column);
      cell.disabled = !gameReady;
      if (column === 2 || column === 5) {
        cell.classList.add("box-right");
      }
      if (row === 2 || row === 5) {
        cell.classList.add("box-bottom");
      }
      if (gameState.given[row][column]) {
        cell.classList.add("is-given");
      }
      if (selected && (
        row === selected[0]
        || column === selected[1]
        || (Math.floor(row / 3) === Math.floor(selected[0] / 3)
          && Math.floor(column / 3) === Math.floor(selected[1] / 3))
      )) {
        cell.classList.add("is-peer");
      }
      if (selectedValue && gameState.grid[row][column] === selectedValue) {
        cell.classList.add("is-same-number");
      }
      if (isSelected(row, column)) {
        cell.classList.add("is-selected");
      }
      if (wrongCells.has(`${row},${column}`)) {
        cell.classList.add("is-wrong");
      }

      const value = gameState.grid[row][column];
      cell.setAttribute(
        "aria-label",
        `Row ${row + 1}, column ${column + 1}${value ? `, ${value}` : ", empty"}${gameState.given[row][column] ? ", clue" : ""}`,
      );
      if (value) {
        const number = document.createElement("span");
        number.className = "cell-value";
        number.textContent = String(value);
        cell.append(number);
      } else if (gameState.notes[row][column].length) {
        const notes = document.createElement("span");
        notes.className = "cell-notes";
        notes.setAttribute("aria-hidden", "true");
        for (let note = 1; note <= SIZE; note += 1) {
          const noteElement = document.createElement("span");
          if (gameState.notes[row][column].includes(note)) {
            noteElement.textContent = String(note);
          }
          notes.append(noteElement);
        }
        cell.append(notes);
      }

      cell.addEventListener("click", () => selectCell(row, column));
      boardElement.append(cell);
    }
  }

  numberPad.querySelectorAll("button").forEach((button) => {
    button.disabled = !gameReady;
  });
  for (const button of [
    difficultySelect,
    newGameButton,
    eraseButton,
    notesButton,
    checkButton,
  ]) {
    button.disabled = !gameReady;
  }
  notesButton.textContent = gameState.note_mode ? "Notes: On" : "Notes: Off";
  notesButton.setAttribute("aria-pressed", String(gameState.note_mode));
}

function showInitializationError(error) {
  const details = error instanceof Error ? error.message : String(error);
  const punctuation = details.endsWith(".") ? "" : ".";
  const hint = window.location.protocol === "file:"
    ? " Run sudoku_browser.py from VS Code to serve the game correctly."
    : " Check your internet connection and make sure the Sudoku Python files are served beside this page.";
  runtimeError = `Unable to load Sudoku: ${details}${punctuation}${hint}`;
  render();
}

function selectCell(row, column) {
  runGameAction(`${PYTHON_MODULE}.select_cell(${row}, ${column})`);
}

function enterNumber(number) {
  if (!gameReady) {
    return;
  }
  runGameAction(`${PYTHON_MODULE}.enter_number(${number})`);
}

function startNewGame(difficulty = difficultySelect.value) {
  if (!gameReady) {
    return;
  }
  if (difficulty !== "Easy" && difficulty !== "Medium" && difficulty !== "Hard") {
    runtimeError = "Choose Easy, Medium, or Hard difficulty.";
    render();
    return;
  }
  runtimeError = "";
  runGameAction(`${PYTHON_MODULE}.new_game("${difficulty}")`);
}

function moveSelection(rowOffset, columnOffset) {
  const [row, column] = gameState.selected || [0, 0];
  const nextRow = Math.max(0, Math.min(SIZE - 1, row + rowOffset));
  const nextColumn = Math.max(0, Math.min(SIZE - 1, column + columnOffset));
  selectCell(nextRow, nextColumn);
  boardElement.querySelector(
    `[data-row="${nextRow}"][data-column="${nextColumn}"]`,
  )?.focus();
}

function handleKeydown(event) {
  if (!gameReady || event.altKey || event.ctrlKey || event.metaKey) {
    return;
  }
  const target = event.target;
  if (target instanceof HTMLSelectElement || target instanceof HTMLInputElement) {
    return;
  }

  if (/^[1-9]$/.test(event.key)) {
    event.preventDefault();
    enterNumber(Number(event.key));
  } else if (event.key === "Backspace" || event.key === "Delete") {
    event.preventDefault();
    runGameAction(`${PYTHON_MODULE}.erase_cell()`);
  } else if (event.key.toLowerCase() === "n") {
    event.preventDefault();
    runGameAction(`${PYTHON_MODULE}.toggle_notes()`);
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    moveSelection(-1, 0);
  } else if (event.key === "ArrowDown") {
    event.preventDefault();
    moveSelection(1, 0);
  } else if (event.key === "ArrowLeft") {
    event.preventDefault();
    moveSelection(0, -1);
  } else if (event.key === "ArrowRight") {
    event.preventDefault();
    moveSelection(0, 1);
  }
}

async function initializeGame() {
  render();
  for (let number = 1; number <= SIZE; number += 1) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "number-button";
    button.textContent = String(number);
    button.setAttribute("aria-label", `Enter ${number}`);
    button.disabled = true;
    button.addEventListener("click", () => enterNumber(number));
    numberPad.append(button);
  }

  try {
    await loadPyodideScript();
    if (typeof globalThis.loadPyodide !== "function") {
      throw new Error("The Pyodide loader was not available after download.");
    }

    pyodide = await globalThis.loadPyodide();
    for (const module of ["sudoku_logic", PYTHON_MODULE]) {
      const response = await fetch(new URL(`./${module}.py`, window.location.href));
      if (!response.ok) {
        throw new Error(`Could not load ${module}.py (HTTP ${response.status}).`);
      }
      pyodide.FS.writeFile(`/${module}.py`, await response.text());
    }

    pyodide.runPython(`
import sys
sys.path.insert(0, "/")
import ${PYTHON_MODULE}
`);
    pyodide.runPython(`${PYTHON_MODULE}.new_game("Easy")`);
    readGameState();
    gameReady = true;
    render();
  } catch (error) {
    showInitializationError(error);
  }
}

newGameButton.addEventListener("click", () => startNewGame());
difficultySelect.addEventListener("change", () => startNewGame());
eraseButton.addEventListener("click", () => {
  runtimeError = "";
  runGameAction(`${PYTHON_MODULE}.erase_cell()`);
});
notesButton.addEventListener("click", () => {
  runtimeError = "";
  runGameAction(`${PYTHON_MODULE}.toggle_notes()`);
});
checkButton.addEventListener("click", () => {
  runtimeError = "";
  runGameAction(`${PYTHON_MODULE}.check_board()`);
});
document.addEventListener("keydown", handleKeydown);
initializeGame();
