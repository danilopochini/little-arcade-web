"use strict";

const PYODIDE_VERSION = "314.0.7";
const PYODIDE_SCRIPT_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.js`;
const PYTHON_MODULE = "chess_browser";
const CHESS_SOURCE_URL = "https://files.pythonhosted.org/packages/93/09/7d04d7581ae3bb8b598017941781bceb7959dd1b13e3ebf7b6a2cd843bc9/chess-1.11.2.tar.gz";
const BOARD_SIZE = 8;
const PIECE_NAMES = {
  king: "King",
  queen: "Queen",
  rook: "Rook",
  bishop: "Bishop",
  knight: "Knight",
  pawn: "Pawn",
};

const boardElement = document.querySelector("#game-board");
const statusElement = document.querySelector("#game-status");
const statusBar = document.querySelector("#status-bar");
const humanCard = document.querySelector("#human-card");
const computerCard = document.querySelector("#computer-card");
const humanCount = document.querySelector("#human-count");
const computerCount = document.querySelector("#computer-count");
const promotionChoice = document.querySelector("#promotion-choice");
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
  turn: "white",
  is_check: false,
  checked_king: null,
  game_over: false,
  winner: null,
  termination: null,
  legal_moves: [],
  last_move: null,
  piece_counts: { white: 16, black: 16 },
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

function squareName(row, column) {
  return `${String.fromCharCode(97 + column)}${BOARD_SIZE - row}`;
}

function samePosition(first, second) {
  return first !== null && second !== null
    && first[0] === second[0]
    && first[1] === second[1];
}

function statusMessage() {
  if (runtimeError) {
    return { text: runtimeError, state: "error" };
  }
  if (notice) {
    return { text: notice, state: "human" };
  }
  if (gameState.game_over) {
    if (gameState.winner === "white") {
      return {
        text: `You win — ${gameState.termination}. Click New Game to play again.`,
        state: "human",
      };
    }
    if (gameState.winner === "black") {
      return {
        text: `The computer wins — ${gameState.termination}. Click New Game to play again.`,
        state: "computer",
      };
    }
    return {
      text: `Draw — ${gameState.termination}. Click New Game to play again.`,
      state: "finished",
    };
  }
  if (!gameReady) {
    return { text: "Loading game...", state: "loading" };
  }
  if (computerThinking || gameState.turn === "black") {
    return { text: "Computer is thinking...", state: "computer" };
  }
  if (gameState.is_check) {
    return { text: "Check! Your move.", state: "human" };
  }
  return { text: "Your turn — select a white piece.", state: "human" };
}

function render() {
  const message = statusMessage();
  statusElement.textContent = message.text;
  statusBar.dataset.state = message.state;

  const activePlayer = gameState.game_over ? null : gameState.turn;
  humanCard.classList.toggle("is-active", activePlayer === "white");
  computerCard.classList.toggle("is-active", activePlayer === "black");
  humanCount.textContent = `White · ${gameState.piece_counts.white} pieces`;
  computerCount.textContent = `Black · ${gameState.piece_counts.black} pieces`;

  const canPlay = (
    gameReady
    && !computerThinking
    && !runtimeError
    && !gameState.game_over
    && gameState.turn === "white"
  );
  const movesFromSelected = selected === null || !canPlay
    ? []
    : gameState.legal_moves.filter((move) => move.from === selected);
  const destinations = new Map(movesFromSelected.map((move) => [
    move.to,
    move.capture,
  ]));
  const lastMoveSquares = new Set();
  if (gameState.last_move) {
    lastMoveSquares.add(gameState.last_move.slice(0, 2));
    lastMoveSquares.add(gameState.last_move.slice(2, 4));
  }

  boardElement.replaceChildren();
  for (let row = 0; row < BOARD_SIZE; row += 1) {
    for (let column = 0; column < BOARD_SIZE; column += 1) {
      const name = squareName(row, column);
      const piece = gameState.board[row][column];
      const isSelected = name === selected;
      const isDestination = destinations.has(name);
      const isLight = (row + column) % 2 === 0;
      const square = document.createElement("button");
      square.type = "button";
      square.className = `chess-square ${isLight ? "is-light" : "is-dark"}`;
      square.disabled = !canPlay;
      if (isSelected) {
        square.classList.add("is-selected");
      }
      if (isDestination) {
        square.classList.add("is-destination");
        if (destinations.get(name)) {
          square.classList.add("is-capture");
        }
      }
      if (lastMoveSquares.has(name)) {
        square.classList.add("is-last-move");
      }
      if (gameState.checked_king === name) {
        square.classList.add("is-check");
      }

      const rankLabel = String(BOARD_SIZE - row);
      const fileLabel = String.fromCharCode(97 + column);
      const description = piece
        ? `${piece.color} ${PIECE_NAMES[piece.type].toLowerCase()}`
        : "empty";
      const moveLabel = isDestination
        ? `, legal${destinations.get(name) ? " capture" : ""} destination`
        : "";
      square.setAttribute(
        "aria-label",
        `${name}, ${description}${isSelected ? ", selected" : ""}${moveLabel}`,
      );
      if (column === 0 || row === BOARD_SIZE - 1) {
        const coordinate = document.createElement("span");
        coordinate.className = "chess-coordinate";
        coordinate.setAttribute("aria-hidden", "true");
        coordinate.textContent = column === 0 && row === BOARD_SIZE - 1
          ? `${rankLabel} ${fileLabel}`
          : column === 0
            ? rankLabel
            : fileLabel;
        square.append(coordinate);
      }

      if (piece) {
        const chessPiece = document.createElement("span");
        chessPiece.className = `chess-piece is-${piece.color}`;
        chessPiece.setAttribute("aria-hidden", "true");
        chessPiece.textContent = piece.symbol;
        square.append(chessPiece);
      }
      square.addEventListener("click", () => handleSquareClick(row, column));
      boardElement.append(square);
    }
  }

  promotionChoice.disabled = !canPlay;
  newGameButton.disabled = !gameReady;
}

function showInitializationError(error) {
  const details = error instanceof Error ? error.message : String(error);
  const punctuation = details.endsWith(".") ? "" : ".";
  const localFileHint = window.location.protocol === "file:"
    ? " Run chess_browser.py from VS Code to serve the game correctly."
    : " Check your internet connection and make sure chess_browser.py is served next to this page.";
  runtimeError = `Unable to load the game: ${details}${punctuation}${localFileHint}`;
  render();
}

function handleSquareClick(row, column) {
  if (!gameReady || computerThinking || runtimeError || gameState.turn !== "white") {
    return;
  }
  const position = squareName(row, column);
  const move = selected === null
    ? null
    : gameState.legal_moves.find(
      (candidate) => candidate.from === selected && candidate.to === position,
    );
  if (move) {
    playHumanMove(move);
    return;
  }

  const piece = gameState.board[row][column];
  const hasLegalMoves = piece?.color === "white" && gameState.legal_moves.some(
    (candidate) => candidate.from === position,
  );
  if (hasLegalMoves) {
    selected = position;
    notice = "";
    render();
    return;
  }

  if (piece?.color === "black") {
    selected = null;
    notice = "You can only move white pieces.";
  } else {
    notice = selected === null
      ? "Select a white piece with a legal move."
      : "That is not a legal destination.";
  }
  render();
}

function playHumanMove(move) {
  notice = "";
  try {
    const promotion = move.promotion ? promotionChoice.value : "q";
    const accepted = pyodide.runPython(
      `${PYTHON_MODULE}.player_move('${move.from}', '${move.to}', '${promotion}')`,
    );
    if (!accepted) {
      throw new Error("The Python game did not accept the selected legal move.");
    }
    selected = null;
    readGameState();
    render();
    if (!gameState.game_over) {
      computerThinking = true;
      render();
      computerTimer = window.setTimeout(playComputerMove, 100);
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
    const chessResponse = await fetch(CHESS_SOURCE_URL);
    if (!chessResponse.ok) {
      throw new Error(`Could not download python-chess (HTTP ${chessResponse.status}).`);
    }
    pyodide.FS.writeFile(
      "/chess-1.11.2.tar.gz",
      new Uint8Array(await chessResponse.arrayBuffer()),
    );
    pyodide.runPython(`
import hashlib
import sys
import tarfile
from pathlib import Path, PurePosixPath

archive_path = Path("/chess-1.11.2.tar.gz")
expected_hash = "a8b43e5678fdb3000695bdaa573117ad683761e5ca38e591c4826eba6d25bb39"
if hashlib.sha256(archive_path.read_bytes()).hexdigest() != expected_hash:
    raise RuntimeError("The python-chess archive failed its SHA-256 check.")

source_root = Path("/python_chess")
package_prefix = "chess-1.11.2/chess/"
with tarfile.open(archive_path, "r:gz") as archive:
    for member in archive.getmembers():
        if not member.isfile() or not member.name.startswith(package_prefix):
            continue
        relative_path = PurePosixPath(member.name[len(package_prefix):])
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise RuntimeError("The python-chess archive contains an unsafe path.")
        destination = source_root / "chess" / Path(*relative_path.parts)
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = archive.extractfile(member)
        if source is None:
            raise RuntimeError(f"Could not read {member.name} from python-chess.")
        destination.write_bytes(source.read())

sys.path.insert(0, str(source_root))
import chess
`);

    const [engineResponse, moduleResponse] = await Promise.all([
      fetch(new URL("./chess_game.py", window.location.href)),
      fetch(new URL(`./${PYTHON_MODULE}.py`, window.location.href)),
    ]);
    if (!engineResponse.ok) {
      throw new Error(`Could not load chess_game.py (HTTP ${engineResponse.status}).`);
    }
    if (!moduleResponse.ok) {
      throw new Error(`Could not load ${PYTHON_MODULE}.py (HTTP ${moduleResponse.status}).`);
    }
    pyodide.FS.writeFile("/chess_game.py", await engineResponse.text());
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
