"use strict";

const PYODIDE_VERSION = "314.0.7";
const PYODIDE_SCRIPT_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.js`;
const PYTHON_MODULE = "checkers_browser";
const BOARD_SIZE = 8;
const RED = "red";
const BLACK = "black";

const boardElement = document.querySelector("#game-board");
const statusElement = document.querySelector("#game-status");
const statusBar = document.querySelector("#status-bar");
const humanCard = document.querySelector("#human-card");
const computerCard = document.querySelector("#computer-card");
const humanCount = document.querySelector("#human-count");
const computerCount = document.querySelector("#computer-count");
const newGameButton = document.querySelector("#new-game");

let pyodide = null;
let gameReady = false;
let computerThinking = false;
let runtimeError = "";
let computerTimer = null;
let selected = null;
let notice = "";
let gameState = {
  board: Array.from({ length: BOARD_SIZE }, () => Array(BOARD_SIZE).fill(null)),
  turn: RED,
  winner: null,
  is_draw: false,
  game_over: false,
  forced_piece: null,
  legal_moves: [],
  last_move: null,
  last_captured: [],
  piece_counts: { [RED]: 12, [BLACK]: 12 },
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

function samePosition(first, second) {
  return first !== null && second !== null
    && first[0] === second[0]
    && first[1] === second[1];
}

function squareName(row, column) {
  return `${String.fromCharCode(65 + column)}${BOARD_SIZE - row}`;
}

function statusMessage() {
  if (runtimeError) {
    return { text: runtimeError, state: "error" };
  }
  if (notice) {
    return { text: notice, state: "human" };
  }
  if (gameState.winner === RED) {
    return { text: "You win! Click New Game to play again.", state: "human" };
  }
  if (gameState.winner === BLACK) {
    return { text: "The computer wins! Click New Game to play again.", state: "computer" };
  }
  if (gameState.is_draw) {
    return { text: "It's a draw! Click New Game to play again.", state: "finished" };
  }
  if (!gameReady) {
    return { text: "Loading game...", state: "loading" };
  }
  if (computerThinking) {
    return { text: "Computer is thinking...", state: "computer" };
  }
  if (gameState.forced_piece) {
    return { text: "Continue capturing with the highlighted piece.", state: "human" };
  }
  if (gameState.turn === BLACK) {
    return { text: "Computer is thinking...", state: "computer" };
  }
  if (gameState.legal_moves.some((move) => move.captures.length > 0)) {
    return { text: "Your turn — a capture is mandatory.", state: "human" };
  }
  return { text: "Your turn — select a red piece.", state: "human" };
}

function render() {
  const message = statusMessage();
  statusElement.textContent = message.text;
  statusBar.dataset.state = message.state;

  const activePlayer = gameState.game_over ? null : gameState.turn;
  humanCard.classList.toggle("is-active", activePlayer === RED);
  computerCard.classList.toggle("is-active", activePlayer === BLACK);
  humanCount.textContent = `Red · ${gameState.piece_counts[RED]} pieces`;
  computerCount.textContent = `Black · ${gameState.piece_counts[BLACK]} pieces`;

  const canPlay = (
    gameReady
    && !computerThinking
    && !runtimeError
    && !gameState.game_over
    && gameState.turn === RED
  );
  const legalDestinations = new Map();
  if (selected !== null && canPlay) {
    for (const move of gameState.legal_moves) {
      if (samePosition(move.start, selected)) {
        legalDestinations.set(
          `${move.path[0][0]},${move.path[0][1]}`,
          move.captures.length > 0,
        );
      }
    }
  }

  const lastSquares = new Set();
  if (gameState.last_move) {
    lastSquares.add(`${gameState.last_move.start[0]},${gameState.last_move.start[1]}`);
    for (const [row, column] of gameState.last_move.path) {
      lastSquares.add(`${row},${column}`);
    }
    for (const [row, column] of gameState.last_captured) {
      lastSquares.add(`${row},${column}`);
    }
  }

  boardElement.replaceChildren();
  for (let row = 0; row < BOARD_SIZE; row += 1) {
    for (let column = 0; column < BOARD_SIZE; column += 1) {
      const position = [row, column];
      const key = `${row},${column}`;
      const playable = (row + column) % 2 === 1;
      const piece = gameState.board[row][column];
      const isSelected = samePosition(selected, position);
      const isDestination = legalDestinations.has(key);
      const square = document.createElement("button");
      square.type = "button";
      square.className = `checkers-square ${playable ? "is-dark" : "is-light"}`;
      square.disabled = !canPlay || !playable;
      square.setAttribute("aria-label", [
        `Square ${squareName(row, column)}`,
        piece ? `${piece.color}${piece.king ? " king" : " piece"}` : "empty",
        isSelected ? "selected" : "",
        isDestination ? `legal${legalDestinations.get(key) ? " capture" : ""} destination` : "",
      ].filter(Boolean).join(", "));
      if (isSelected) {
        square.classList.add("is-selected");
      }
      if (isDestination) {
        square.classList.add("is-destination");
        if (legalDestinations.get(key)) {
          square.classList.add("is-capture");
        }
      }
      if (lastSquares.has(key)) {
        square.classList.add("is-last-move");
      }
      square.addEventListener("click", () => handleSquareClick(row, column));

      if (piece) {
        const checker = document.createElement("span");
        checker.className = `checker-piece${piece.color === BLACK ? " is-black" : ""}${piece.king ? " is-king" : ""}`;
        checker.setAttribute("aria-hidden", "true");
        square.append(checker);
      }
      boardElement.append(square);
    }
  }

  newGameButton.disabled = !gameReady;
}

function showInitializationError(error) {
  const details = error instanceof Error ? error.message : String(error);
  const punctuation = details.endsWith(".") ? "" : ".";
  const localFileHint = window.location.protocol === "file:"
    ? " Run checkers_browser.py from VS Code to serve the game correctly."
    : " Check your internet connection and make sure checkers_browser.py is served next to this page.";
  runtimeError = `Unable to load the game: ${details}${punctuation}${localFileHint}`;
  render();
}

function handleSquareClick(row, column) {
  if (!gameReady || computerThinking || runtimeError || gameState.turn !== RED) {
    return;
  }
  const position = [row, column];
  const destination = selected !== null && gameState.legal_moves.some(
    (move) => samePosition(move.start, selected) && samePosition(move.path[0], position),
  );
  if (destination) {
    playHumanMove(position);
    return;
  }

  const piece = gameState.board[row][column];
  const legalSource = piece?.color === RED && gameState.legal_moves.some(
    (move) => samePosition(move.start, position),
  );
  if (legalSource) {
    notice = "";
    if (samePosition(selected, position) && gameState.forced_piece === null) {
      selected = null;
    } else {
      selected = position;
    }
    render();
    return;
  }

  if (gameState.forced_piece) {
    selected = gameState.forced_piece;
    notice = "This piece must continue capturing.";
  } else if (piece?.color === BLACK) {
    selected = null;
    notice = "You can only move red pieces.";
  } else {
    notice = selected === null
      ? "Select a red piece with a legal move."
      : "That square is not a legal destination.";
  }
  render();
}

function playHumanMove(destination) {
  if (selected === null) {
    return;
  }
  notice = "";
  try {
    const accepted = pyodide.runPython(
      `${PYTHON_MODULE}.player_move(${selected[0]}, ${selected[1]}, ${destination[0]}, ${destination[1]})`,
    );
    if (!accepted) {
      throw new Error("The game did not accept that legal move.");
    }
    readGameState();
    if (gameState.forced_piece) {
      selected = gameState.forced_piece;
      render();
      return;
    }

    selected = null;
    render();
    if (!gameState.game_over) {
      computerThinking = true;
      render();
      computerTimer = window.setTimeout(playComputerMove, 180);
    }
  } catch (error) {
    runtimeError = `Your move could not be played: ${error.message || error}`;
    render();
  }
}

function playComputerMove() {
  computerTimer = null;
  if (!gameReady || !computerThinking) {
    return;
  }
  try {
    const accepted = pyodide.runPython(`${PYTHON_MODULE}.computer_move()`);
    if (!accepted) {
      throw new Error("The Python game did not accept the computer's turn.");
    }
    readGameState();
    computerThinking = false;
    render();
  } catch (error) {
    computerThinking = false;
    runtimeError = `The computer could not make its move: ${error.message || error}`;
    render();
  }
}

function startNewGame() {
  if (!gameReady) {
    return;
  }
  if (computerTimer !== null) {
    window.clearTimeout(computerTimer);
    computerTimer = null;
  }
  try {
    pyodide.runPython(`${PYTHON_MODULE}.new_game()`);
    selected = null;
    notice = "";
    computerThinking = false;
    runtimeError = "";
    readGameState();
    render();
  } catch (error) {
    runtimeError = `A new game could not be started: ${error.message || error}`;
    render();
  }
}

async function initializeGame() {
  render();
  try {
    await loadPyodideScript();
    if (typeof globalThis.loadPyodide !== "function") {
      throw new Error("The Pyodide loader was not available after download.");
    }

    pyodide = await globalThis.loadPyodide();
    const checkersUrl = new URL("./checkers.py", window.location.href);
    const moduleUrl = new URL(`./${PYTHON_MODULE}.py`, window.location.href);
    const [checkersResponse, moduleResponse] = await Promise.all([
      fetch(checkersUrl),
      fetch(moduleUrl),
    ]);
    if (!checkersResponse.ok) {
      throw new Error(`Could not load checkers.py (HTTP ${checkersResponse.status}).`);
    }
    if (!moduleResponse.ok) {
      throw new Error(`Could not load ${PYTHON_MODULE}.py (HTTP ${moduleResponse.status}).`);
    }

    pyodide.FS.writeFile("/checkers.py", await checkersResponse.text());
    pyodide.FS.writeFile(`/${PYTHON_MODULE}.py`, await moduleResponse.text());
    pyodide.runPython(`
import sys
sys.path.insert(0, "/")
import ${PYTHON_MODULE}
`);
    pyodide.runPython(`${PYTHON_MODULE}.new_game()`);
    readGameState();
    gameReady = true;
    render();
  } catch (error) {
    showInitializationError(error);
  }
}

newGameButton.addEventListener("click", startNewGame);
initializeGame();
