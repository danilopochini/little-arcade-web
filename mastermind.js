"use strict";

const CODE_LENGTH = 4;
const MAX_TURNS = 10;
const PALETTE = [
  { name: "Ruby", color: "#dc4054" },
  { name: "Tangerine", color: "#ed8a35" },
  { name: "Sunshine", color: "#e7c43c" },
  { name: "Jade", color: "#35a879" },
  { name: "Ocean", color: "#3986cb" },
  { name: "Violet", color: "#8958b5" },
];

function generateSecretCode(random = Math.random) {
  return Array.from(
    { length: CODE_LENGTH },
    () => Math.floor(random() * PALETTE.length),
  );
}

function createGameState(secretCode = generateSecretCode()) {
  if (
    !Array.isArray(secretCode)
    || secretCode.length !== CODE_LENGTH
    || secretCode.some((pin) => !Number.isInteger(pin) || pin < 0 || pin >= PALETTE.length)
  ) {
    throw new Error("The secret code must contain four valid colors.");
  }

  return {
    palette: PALETTE,
    code_length: CODE_LENGTH,
    max_turns: MAX_TURNS,
    secret_code: [...secretCode],
    guesses: [],
    current_guess: [],
    turn: 1,
    finished: false,
    won: false,
    status: "Choose four colors to make your first guess.",
    status_kind: "info",
  };
}

function scoreGuess(secret, guess) {
  let exact = 0;
  const remainingSecret = Array(PALETTE.length).fill(0);
  const remainingGuess = Array(PALETTE.length).fill(0);

  for (let index = 0; index < CODE_LENGTH; index += 1) {
    if (secret[index] === guess[index]) {
      exact += 1;
    } else {
      remainingSecret[secret[index]] += 1;
      remainingGuess[guess[index]] += 1;
    }
  }

  const colorOnly = remainingSecret.reduce(
    (total, count, color) => total + Math.min(count, remainingGuess[color]),
    0,
  );
  return { exact, color_only: colorOnly };
}

function addPin(state, pin) {
  if (!Number.isInteger(pin)) {
    throw new TypeError("Color selection must be an integer.");
  }
  if (pin < 0 || pin >= PALETTE.length) {
    throw new RangeError(`Choose a color from 1 to ${PALETTE.length}.`);
  }
  if (state.finished) {
    state.status = "Start a new game to play again.";
    state.status_kind = "muted";
  } else if (state.current_guess.length >= CODE_LENGTH) {
    state.status = "Your guess already has four pegs. Submit it or clear it.";
    state.status_kind = "muted";
  } else {
    state.current_guess.push(pin);
    state.status = `${state.current_guess.length} of ${CODE_LENGTH} pegs selected.`;
    state.status_kind = "info";
  }
  return state;
}

function clearGuess(state) {
  if (!state.finished) {
    state.current_guess = [];
    state.status = "Guess cleared. Choose four colors.";
    state.status_kind = "info";
  }
  return state;
}

function removePin(state) {
  if (!state.finished && state.current_guess.length > 0) {
    state.current_guess.pop();
    state.status = "Last peg removed.";
    state.status_kind = "info";
  }
  return state;
}

function submitGuess(state) {
  if (state.finished) {
    state.status = "Start a new game to play again.";
    state.status_kind = "muted";
    return state;
  }
  if (state.current_guess.length !== CODE_LENGTH) {
    const missing = CODE_LENGTH - state.current_guess.length;
    state.status = `Choose ${missing} more peg${missing !== 1 ? "s" : ""} before submitting.`;
    state.status_kind = "error";
    return state;
  }

  const pins = [...state.current_guess];
  const feedback = scoreGuess(state.secret_code, pins);
  state.guesses.push({ pins, feedback });
  state.current_guess = [];
  state.turn = state.guesses.length + 1;

  if (feedback.exact === CODE_LENGTH) {
    state.finished = true;
    state.won = true;
    state.status = "Code cracked! You win — click New Game to play again.";
    state.status_kind = "success";
  } else if (state.guesses.length === MAX_TURNS) {
    state.finished = true;
    const secret = state.secret_code.map((pin) => PALETTE[pin].name).join("  ");
    state.status = `Out of guesses! The code was ${secret}.`;
    state.status_kind = "error";
  } else {
    state.status = (
      `${feedback.exact} exact match${feedback.exact !== 1 ? "es" : ""}, `
      + `${feedback.color_only} right color${feedback.color_only !== 1 ? "s" : ""} in another spot.`
    );
    state.status_kind = "info";
  }
  return state;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    CODE_LENGTH,
    MAX_TURNS,
    PALETTE,
    addPin,
    clearGuess,
    createGameState,
    generateSecretCode,
    removePin,
    scoreGuess,
    submitGuess,
  };
}

if (typeof document !== "undefined" && typeof window !== "undefined") {
  const statusBar = document.querySelector("#status-bar");
  const statusElement = document.querySelector("#game-status");
  const turnCounter = document.querySelector("#turn-counter");
  const board = document.querySelector("#game-board");
  const paletteElement = document.querySelector("#color-palette");
  const clearButton = document.querySelector("#clear-guess");
  const submitButton = document.querySelector("#submit-guess");
  const newGameButton = document.querySelector("#new-game");

  let gameState = createGameState();

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
      button.disabled = gameState.finished || gameState.current_guess.length >= gameState.code_length;
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
      button.addEventListener("click", () => runAction(addPin, index));
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
        const pin = guess
          ? guess.pins[pegIndex]
          : isCurrent ? gameState.current_guess[pegIndex] : undefined;
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
        feedbackPegs.append(makePeg(marker, { feedback: true, hollow: marker === undefined }));
      }
      row.append(feedbackPegs);
      board.append(row);
    }
  }

  function render() {
    statusElement.textContent = gameState.status;
    statusBar.dataset.state = gameState.status_kind;
    if (gameState.finished) {
      turnCounter.textContent = gameState.won ? "CODE CRACKED" : "CODE REVEALED";
    } else {
      turnCounter.textContent = `GUESS ${gameState.turn} / ${gameState.max_turns}`;
    }
    renderBoard();
    renderPalette();
    clearButton.disabled = gameState.finished || gameState.current_guess.length === 0;
    submitButton.disabled = gameState.finished;
    newGameButton.disabled = false;
  }

  function runAction(action, ...args) {
    action(gameState, ...args);
    render();
  }

  clearButton.addEventListener("click", () => runAction(clearGuess));
  submitButton.addEventListener("click", () => runAction(submitGuess));
  newGameButton.addEventListener("click", () => {
    gameState = createGameState();
    render();
  });

  document.addEventListener("keydown", (event) => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.repeat) {
      return;
    }
    if (/^[1-6]$/.test(event.key)) {
      event.preventDefault();
      if (!gameState.finished) {
        runAction(addPin, Number(event.key) - 1);
      }
    } else if (event.key === "Backspace" || event.key === "Delete") {
      event.preventDefault();
      if (gameState.current_guess.length > 0) {
        runAction(removePin);
      }
    } else if (event.key === "Enter" && !gameState.finished) {
      event.preventDefault();
      runAction(submitGuess);
    }
  });

  render();
}
