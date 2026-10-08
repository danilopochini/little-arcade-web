"use strict";

const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

const statusElement = document.querySelector("#game-status");
const statusBar = document.querySelector("#status-bar");
const drawing = document.querySelector("#hangman-drawing");
const wordDisplay = document.querySelector("#word-display");
const mistakesCount = document.querySelector("#mistakes-count");
const keyboard = document.querySelector("#letter-keyboard");
const usedLetters = document.querySelector("#used-letters");
const guessForm = document.querySelector("#guess-form");
const guessInput = document.querySelector("#guess-input");
const guessButton = document.querySelector("#guess-button");
const newGameButton = document.querySelector("#new-game");

const ARCADE_MODE = new URLSearchParams(window.location.search).get("arcade") === "1";
const API_BASE = ARCADE_MODE ? "/api/hangman" : "/api";
const SERVER_INSTRUCTIONS = ARCADE_MODE
  ? "Start the arcade with `python arcade_server.py` and keep its terminal window open while playing."
  : "Run `python hangman_browser.py` and keep its terminal window open while playing.";

let gameState = null;
let requestPending = false;
let requestError = "";

async function sendAction(path, payload = {}) {
  if (window.location.protocol === "file:") {
    throw new Error(`Opening hangman.html directly cannot reach the game server. ${SERVER_INSTRUCTIONS}`);
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
      throw new Error(`The local Hangman game server is unreachable. ${SERVER_INSTRUCTIONS}`);
    }
    throw error;
  }
  if (!response.headers.get("content-type")?.includes("application/json")) {
    throw new Error(`This page is not connected to the Hangman game server. ${SERVER_INSTRUCTIONS}`);
  }
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || `The game server returned HTTP ${response.status}.`);
  }
  return result;
}

function renderKeyboard() {
  const guessed = new Set(gameState.guessed_letters);
  const correct = new Set(gameState.correct_letters);
  keyboard.replaceChildren();
  for (const letter of LETTERS) {
    const key = document.createElement("button");
    key.type = "button";
    key.className = "letter-key";
    key.textContent = letter;
    key.disabled = requestPending || gameState.finished || guessed.has(letter);
    if (correct.has(letter)) {
      key.classList.add("is-correct");
    }
    key.setAttribute(
      "aria-label",
      guessed.has(letter) ? `${letter}, already guessed` : `Guess ${letter}`,
    );
    key.addEventListener("click", () => submitGuess(letter));
    keyboard.append(key);
  }
}

function render() {
  if (!gameState) {
    statusElement.textContent = requestError || "Loading game...";
    statusBar.dataset.state = requestError ? "error" : "loading";
    return;
  }
  statusElement.textContent = requestError || gameState.status;
  statusBar.dataset.state = requestError ? "error" : gameState.status_kind;
  wordDisplay.textContent = gameState.word_display;
  wordDisplay.setAttribute("aria-label", `Word: ${gameState.word_display}`);
  mistakesCount.textContent = `Incorrect guesses: ${gameState.wrong_guesses}/${gameState.max_wrong_guesses}`;
  drawing.setAttribute(
    "aria-label",
    `Hangman drawing, ${gameState.wrong_guesses} of ${gameState.max_wrong_guesses} incorrect guesses`,
  );
  for (const part of drawing.querySelectorAll(".person-part")) {
    part.classList.toggle("is-visible", Number(part.dataset.part) <= gameState.wrong_guesses);
  }

  const guessed = gameState.guessed_letters;
  usedLetters.textContent = guessed.length
    ? `Used letters: ${guessed.join(", ")}`
    : "No letters guessed yet";
  guessInput.disabled = requestPending || gameState.finished;
  guessButton.disabled = requestPending || gameState.finished;
  newGameButton.disabled = requestPending;
  renderKeyboard();
}

function setRequestError(error) {
  const details = error instanceof Error ? error.message : String(error);
  requestError = `Could not update the game: ${details}`;
}

async function submitGuess(guess) {
  if (requestPending || !gameState || gameState.finished) {
    return;
  }
  requestPending = true;
  render();
  try {
    gameState = await sendAction("/api/guess", { guess });
    requestError = "";
    guessInput.value = "";
  } catch (error) {
    setRequestError(error);
  } finally {
    requestPending = false;
    render();
  }
}

async function startNewGame() {
  if (requestPending) {
    return;
  }
  requestPending = true;
  render();
  try {
    gameState = await sendAction("/api/new");
    requestError = "";
    guessInput.value = "";
  } catch (error) {
    setRequestError(error);
  } finally {
    requestPending = false;
    render();
  }
}

guessForm.addEventListener("submit", (event) => {
  event.preventDefault();
  void submitGuess(guessInput.value);
});
newGameButton.addEventListener("click", () => void startNewGame());

async function initializeGame() {
  try {
    gameState = await sendAction("/api/new");
    requestError = "";
    render();
  } catch (error) {
    setRequestError(error);
  } finally {
    newGameButton.disabled = false;
    render();
  }
}

render();
void initializeGame();
