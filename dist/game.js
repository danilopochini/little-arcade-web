"use strict";

const PYODIDE_VERSION = "314.0.7";
const PYODIDE_SCRIPT_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.js`;
const PYTHON_MODULE = "connect_four_browser";
const ROWS = 6;
const COLUMNS = 7;
const EMPTY = 0;
const HUMAN = 1;
const COMPUTER = 2;

const boardElement = document.querySelector("#game-board");
const statusElement = document.querySelector("#game-status");
const statusBar = document.querySelector("#status-bar");
const humanCard = document.querySelector("#human-card");
const computerCard = document.querySelector("#computer-card");
const newGameButton = document.querySelector("#new-game");

let pyodide = null;
let gameReady = false;
let computerThinking = false;
let runtimeError = "";
let computerTimer = null;
let audioContext = null;
let announcedWinner = EMPTY;
let gameState = {
  board: Array.from({ length: ROWS }, () => Array(COLUMNS).fill(EMPTY)),
  turn: HUMAN,
  winner: EMPTY,
  is_draw: false,
  winning_cells: [],
  valid_columns: Array.from({ length: COLUMNS }, (_, column) => column),
};

function unlockAudio() {
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) {
    return;
  }

  if (!audioContext) {
    try {
      audioContext = new AudioContextClass();
    } catch (error) {
      console.warn("Win sounds are unavailable in this browser.", error);
      return;
    }
  }

  if (audioContext.state === "suspended") {
    void audioContext.resume().catch((error) => {
      console.warn("Could not enable win sounds.", error);
    });
  }
}

function playOutcomeSound(winner) {
  if (!audioContext || winner === EMPTY || winner === announcedWinner) {
    return;
  }

  announcedWinner = winner;
  const notes = winner === HUMAN
    ? [523.25, 659.25, 783.99]
    : [392, 329.63, 261.63];
  const startTime = audioContext.currentTime;

  notes.forEach((frequency, index) => {
    const oscillator = audioContext.createOscillator();
    const volume = audioContext.createGain();
    const noteStart = startTime + index * 0.17;

    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(frequency, noteStart);
    volume.gain.setValueAtTime(0.0001, noteStart);
    volume.gain.exponentialRampToValueAtTime(0.16, noteStart + 0.025);
    volume.gain.exponentialRampToValueAtTime(0.0001, noteStart + 0.24);
    oscillator.connect(volume);
    volume.connect(audioContext.destination);
    oscillator.start(noteStart);
    oscillator.stop(noteStart + 0.25);
  });
}

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
  const board = JSON.parse(pyodide.runPython(`${PYTHON_MODULE}.get_board()`));
  const status = JSON.parse(pyodide.runPython(`${PYTHON_MODULE}.get_game_status()`));
  gameState = { board, ...status };
}

function statusMessage() {
  if (runtimeError) {
    return { text: runtimeError, state: "error" };
  }
  if (gameState.winner === HUMAN) {
    return { text: "You win! Click New Game to play again.", state: "human" };
  }
  if (gameState.winner === COMPUTER) {
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
  return { text: "Your turn - choose a column.", state: "human" };
}

function render() {
  const message = statusMessage();
  statusElement.textContent = message.text;
  statusBar.dataset.state = message.state;

  const activePlayer = gameState.winner || (gameState.is_draw ? EMPTY : gameState.turn);
  humanCard.classList.toggle("is-active", activePlayer === HUMAN);
  computerCard.classList.toggle("is-active", activePlayer === COMPUTER);

  const winningCells = new Set(
    gameState.winning_cells.map(([row, column]) => `${row},${column}`),
  );
  const canPlay = (
    gameReady
    && !computerThinking
    && !runtimeError
    && !gameState.winner
    && !gameState.is_draw
    && gameState.turn === HUMAN
  );

  boardElement.replaceChildren();
  for (let column = 0; column < COLUMNS; column += 1) {
    const columnButton = document.createElement("button");
    columnButton.type = "button";
    columnButton.className = "column-button";

    const columnIsOpen = gameState.valid_columns.includes(column);
    columnButton.disabled = !canPlay || !columnIsOpen;
    columnButton.setAttribute(
      "aria-label",
      columnIsOpen
        ? `Drop a red piece in column ${column + 1}`
        : `Column ${column + 1} is full`,
    );
    columnButton.addEventListener("click", () => playHumanMove(column));

    for (let row = 0; row < ROWS; row += 1) {
      const disc = document.createElement("span");
      disc.className = "disc";
      disc.setAttribute("aria-hidden", "true");
      const piece = gameState.board[row][column];
      if (piece === HUMAN) {
        disc.classList.add("is-human");
      } else if (piece === COMPUTER) {
        disc.classList.add("is-computer");
      } else {
        disc.classList.add("is-empty");
      }
      if (winningCells.has(`${row},${column}`)) {
        disc.classList.add("is-winning");
      }
      columnButton.append(disc);
    }

    boardElement.append(columnButton);
  }

  newGameButton.disabled = !gameReady;
}

function showInitializationError(error) {
  const details = error instanceof Error ? error.message : String(error);
  const punctuation = details.endsWith(".") ? "" : ".";
  const localFileHint = window.location.protocol === "file:"
    ? " Run connect_four_browser.py from VS Code to serve the game correctly."
    : " Check your internet connection and make sure connect_four_browser.py is served next to this page.";
  runtimeError = `Unable to load the game: ${details}${punctuation}${localFileHint}`;
  render();
}

function playHumanMove(column) {
  if (!gameReady || computerThinking || runtimeError) {
    return;
  }

  unlockAudio();
  try {
    const accepted = pyodide.runPython(`${PYTHON_MODULE}.player_move(${column})`);
    if (!accepted) {
      return;
    }
    readGameState();
    playOutcomeSound(gameState.winner);
    if (gameState.winner || gameState.is_draw) {
      render();
      return;
    }

    computerThinking = true;
    render();
    computerTimer = window.setTimeout(playComputerMove, 180);
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
    playOutcomeSound(gameState.winner);
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
    computerThinking = false;
    runtimeError = "";
    announcedWinner = EMPTY;
    unlockAudio();
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
    const sourceUrl = new URL(`./${PYTHON_MODULE}.py`, window.location.href);
    const response = await fetch(sourceUrl);
    if (!response.ok) {
      throw new Error(`Could not load ${PYTHON_MODULE}.py (HTTP ${response.status}).`);
    }

    pyodide.FS.writeFile(`/${PYTHON_MODULE}.py`, await response.text());
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
