"use strict";

const statusBar = document.querySelector("#status-bar");
const statusElement = document.querySelector("#game-status");
const turnCounter = document.querySelector("#turn-counter");
const board = document.querySelector("#game-board");
const paletteElement = document.querySelector("#color-palette");
const clearButton = document.querySelector("#clear-guess");
const submitButton = document.querySelector("#submit-guess");
const newGameButton = document.querySelector("#new-game");

const ARCADE_MODE = new URLSearchParams(window.location.search).get("arcade") === "1";
const API_BASE = ARCADE_MODE ? "/api/mastermind" : "/api";
const SERVER_INSTRUCTIONS = ARCADE_MODE
  ? "Start the arcade with `python arcade_server.py` and keep its terminal window open while playing."
  : "Run `python mastermind_browser.py` and keep its terminal window open while playing.";

let gameState = null;
let requestPending = false;
let requestError = "";

async function sendAction(path, payload = {}) {
  if (window.location.protocol === "file:") {
    throw new Error(`Opening mastermind.html directly cannot reach the game server. ${SERVER_INSTRUCTIONS}`);
  }

  let response;
  try {
    response = await fetch(`${API_BASE}${path.slice(4)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(`The local Mastermind game server is unreachable. ${SERVER_INSTRUCTIONS}`);
    }
    throw error;
  }
  if (!response.headers.get("content-type")?.includes("application/json")) {
    throw new Error(`This page is not connected to the Mastermind game server. ${SERVER_INSTRUCTIONS}`);
  }
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || `The game server returned HTTP ${response.status}.`);
  }
  return result;
}

function makePeg(colorIndex, { hollow = false, feedback = false } = {}) {
  const peg = document.createElement("span");
  peg.className = feedback ? "feedback-dot" : "guess-peg";
  if (hollow) {
    peg.classList.add("is-empty");
  } else if (feedback) {
    peg.classList.add(colorIndex === 0 ? "is-exact" : "is-color-only");
  } else {
    const color = gameState.palette[colorIndex];
    peg.classList.add("is-filled");
    peg.style.setProperty("--peg-color", color.color);
    peg.setAttribute("aria-label", color.name);
  }
  return peg;
}

function renderPalette() {
  paletteElement.replaceChildren();
  for (const [index, color] of gameState.palette.entries()) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "color-choice";
    button.disabled = requestPending || gameState.finished || gameState.current_guess.length >= gameState.code_length;
    button.setAttribute("aria-label", `Add ${color.name}`);
    button.title = `${index + 1}: ${color.name}`;

    const swatch = document.createElement("span");
    swatch.className = "color-swatch";
    swatch.style.setProperty("--peg-color", color.color);
    swatch.setAttribute("aria-hidden", "true");
    const name = document.createElement("span");
    name.className = "color-name";
    name.textContent = `${index + 1} ${color.name}`;
    button.append(swatch, name);
    button.addEventListener("click", () => runAction("/api/pin", { pin: index }));
    paletteElement.append(button);
  }
}

function renderBoard() {
  board.replaceChildren();
  for (let rowIndex = 0; rowIndex < gameState.max_turns; rowIndex += 1) {
    const row = document.createElement("div");
    row.className = "board-row";
    const number = document.createElement("span");
    number.className = "row-number";
    number.textContent = String(rowIndex + 1).padStart(2, "0");
    row.append(number);

    const guess = gameState.guesses[rowIndex];
    const isCurrent = !guess && rowIndex === gameState.guesses.length && !gameState.finished;
    const guessPegs = document.createElement("div");
    guessPegs.className = `guess-pegs${isCurrent ? " is-current" : ""}`;
    for (let pegIndex = 0; pegIndex < gameState.code_length; pegIndex += 1) {
      const pin = guess ? guess.pins[pegIndex] : isCurrent ? gameState.current_guess[pegIndex] : undefined;
      guessPegs.append(makePeg(pin, { hollow: pin === undefined }));
    }
    row.append(guessPegs);

    const feedbackPegs = document.createElement("div");
    feedbackPegs.className = "feedback-pegs";
    const feedback = guess?.feedback;
    const markers = feedback
      ? Array(feedback.exact).fill(0).concat(Array(feedback.color_only).fill(1))
      : [];
    for (let pegIndex = 0; pegIndex < gameState.code_length; pegIndex += 1) {
      const marker = markers[pegIndex];
      feedbackPegs.append(
        makePeg(marker, { feedback: true, hollow: marker === undefined }),
      );
    }
    row.append(feedbackPegs);
    board.append(row);
  }
}

function render() {
  if (!gameState) {
    statusElement.textContent = requestError || "Loading game...";
    statusBar.dataset.state = requestError ? "error" : "loading";
    newGameButton.disabled = requestPending;
    return;
  }

  statusElement.textContent = requestError || gameState.status;
  statusBar.dataset.state = requestError ? "error" : gameState.status_kind;
  if (gameState.finished) {
    turnCounter.textContent = gameState.won ? "CODE CRACKED" : "CODE REVEALED";
  } else {
    turnCounter.textContent = `GUESS ${gameState.turn} / ${gameState.max_turns}`;
  }
  renderBoard();
  renderPalette();
  clearButton.disabled = requestPending || gameState.finished || gameState.current_guess.length === 0;
  submitButton.disabled = requestPending || gameState.finished;
  newGameButton.disabled = requestPending;
}

function setRequestError(error) {
  requestError = `Could not update the game: ${error instanceof Error ? error.message : String(error)}`;
}

async function runAction(path, payload = {}) {
  if (requestPending) {
    return;
  }
  requestPending = true;
  render();
  try {
    gameState = await sendAction(path, payload);
    requestError = "";
  } catch (error) {
    setRequestError(error);
  } finally {
    requestPending = false;
    render();
  }
}

clearButton.addEventListener("click", () => void runAction("/api/clear"));
submitButton.addEventListener("click", () => void runAction("/api/submit"));
newGameButton.addEventListener("click", () => void runAction("/api/new"));

document.addEventListener("keydown", (event) => {
  if (event.altKey || event.ctrlKey || event.metaKey || event.repeat) {
    return;
  }
  if (/^[1-6]$/.test(event.key)) {
    event.preventDefault();
    if (gameState && !requestPending && !gameState.finished) {
      void runAction("/api/pin", { pin: Number(event.key) - 1 });
    }
  } else if (event.key === "Backspace" || event.key === "Delete") {
    event.preventDefault();
    if (gameState?.current_guess.length) {
      void runAction("/api/remove");
    }
  } else if (event.key === "Enter" && gameState && !gameState.finished) {
    event.preventDefault();
    void runAction("/api/submit");
  }
});

async function initializeGame() {
  try {
    gameState = await sendAction("/api/new");
    requestError = "";
  } catch (error) {
    setRequestError(error);
  } finally {
    render();
  }
}

render();
void initializeGame();
