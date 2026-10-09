"use strict";

const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
const MAX_WRONG_GUESSES = 10;

function chooseWord(words, random = Math.random) {
  if (!Array.isArray(words) || words.length === 0) {
    throw new Error("The Hangman word list is empty.");
  }
  return words[Math.floor(random() * words.length)];
}

function createGameState(secretWord) {
  return {
    secret_word: secretWord,
    guessed_letters: new Set(),
    wrong_guesses: 0,
    finished: false,
    status: "Guess a letter to reveal the word.",
    status_kind: "info",
  };
}

function getPublicGameState(state) {
  const secretLetters = new Set(state.secret_word);
  const won = [...secretLetters].every((letter) => state.guessed_letters.has(letter));
  const revealAll = state.finished && !won;
  const visibleLetters = revealAll
    ? secretLetters
    : state.guessed_letters;

  return {
    word_display: [...state.secret_word]
      .map((letter) => visibleLetters.has(letter) ? letter : "_")
      .join(" "),
    guessed_letters: [...state.guessed_letters].sort(),
    correct_letters: [...state.guessed_letters]
      .filter((letter) => secretLetters.has(letter))
      .sort(),
    wrong_guesses: state.wrong_guesses,
    max_wrong_guesses: MAX_WRONG_GUESSES,
    finished: state.finished,
    status: state.status,
    status_kind: state.status_kind,
  };
}

function submitGuess(state, guess) {
  if (typeof guess !== "string") {
    throw new TypeError("Guess must be text.");
  }
  const normalizedGuess = guess.trim().toUpperCase();

  if (state.finished) {
    return state;
  }
  if (normalizedGuess === "QUIT") {
    state.finished = true;
    state.status = `You quit! The word was ${state.secret_word}.`;
    state.status_kind = "muted";
    return state;
  }
  if (!/^[A-Z]$/.test(normalizedGuess)) {
    throw new Error("Enter one letter from A to Z, or type QUIT to reveal the word.");
  }
  if (state.guessed_letters.has(normalizedGuess)) {
    state.status = `You already guessed ${normalizedGuess}. Try another letter.`;
    state.status_kind = "muted";
    return state;
  }

  state.guessed_letters.add(normalizedGuess);
  if (state.secret_word.includes(normalizedGuess)) {
    state.status = `Correct! ${normalizedGuess} is in the word.`;
    state.status_kind = "success";
  } else {
    state.wrong_guesses += 1;
    state.status = `${normalizedGuess} is not in the word.`;
    state.status_kind = "error";
  }

  const won = [...new Set(state.secret_word)]
    .every((letter) => state.guessed_letters.has(letter));
  if (won) {
    state.finished = true;
    state.status = `You won! The word was ${state.secret_word}.`;
    state.status_kind = "success";
  } else if (state.wrong_guesses >= MAX_WRONG_GUESSES) {
    state.finished = true;
    state.status = `Game over! The word was ${state.secret_word}.`;
    state.status_kind = "error";
  }
  return state;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    LETTERS,
    MAX_WRONG_GUESSES,
    chooseWord,
    createGameState,
    getPublicGameState,
    submitGuess,
  };
}

if (typeof document !== "undefined" && typeof window !== "undefined") {
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

  let words = [];
  let gameState = null;
  let loadingWords = false;
  let requestError = "";

  function renderKeyboard() {
    const guessed = gameState ? gameState.guessed_letters : new Set();
    const correct = gameState
      ? new Set(getPublicGameState(gameState).correct_letters)
      : new Set();
    keyboard.replaceChildren();
    for (const letter of LETTERS) {
      const key = document.createElement("button");
      key.type = "button";
      key.className = "letter-key";
      key.textContent = letter;
      key.disabled = loadingWords || !gameState || gameState.finished || guessed.has(letter);
      if (correct.has(letter)) {
        key.classList.add("is-correct");
      }
      key.setAttribute(
        "aria-label",
        guessed.has(letter) ? `${letter}, already guessed` : `Guess ${letter}`,
      );
      key.addEventListener("click", () => submitLetter(letter));
      keyboard.append(key);
    }
  }

  function render() {
    if (!gameState) {
      statusElement.textContent = requestError || "Loading game...";
      statusBar.dataset.state = requestError ? "error" : "loading";
      guessInput.disabled = true;
      guessButton.disabled = true;
      newGameButton.disabled = loadingWords;
      renderKeyboard();
      return;
    }

    const publicState = getPublicGameState(gameState);
    statusElement.textContent = requestError || publicState.status;
    statusBar.dataset.state = requestError ? "error" : publicState.status_kind;
    wordDisplay.textContent = publicState.word_display;
    wordDisplay.setAttribute("aria-label", `Word: ${publicState.word_display}`);
    mistakesCount.textContent =
      `Incorrect guesses: ${publicState.wrong_guesses}/${publicState.max_wrong_guesses}`;
    drawing.setAttribute(
      "aria-label",
      `Hangman drawing, ${publicState.wrong_guesses} of ${publicState.max_wrong_guesses} incorrect guesses`,
    );
    for (const part of drawing.querySelectorAll(".person-part")) {
      part.classList.toggle(
        "is-visible",
        Number(part.dataset.part) <= publicState.wrong_guesses,
      );
    }

    const guessed = publicState.guessed_letters;
    usedLetters.textContent = guessed.length
      ? `Used letters: ${guessed.join(", ")}`
      : "No letters guessed yet";
    guessInput.disabled = gameState.finished;
    guessButton.disabled = gameState.finished;
    newGameButton.disabled = false;
    renderKeyboard();
  }

  function submitLetter(guess) {
    if (!gameState || gameState.finished || loadingWords) {
      return;
    }
    try {
      submitGuess(gameState, guess);
      requestError = "";
      guessInput.value = "";
    } catch (error) {
      requestError = `Could not update the game: ${error instanceof Error ? error.message : String(error)}`;
    }
    render();
  }

  function validateWordList(candidate) {
    return Array.isArray(candidate)
      && candidate.length > 0
      && candidate.every((word) => (
        typeof word === "string"
        && /^[A-Z]{4,9}$/.test(word)
      ));
  }

  async function loadWordList() {
    const response = await fetch("./hangman_words.json");
    if (!response.ok) {
      throw new Error(`The word list returned HTTP ${response.status}.`);
    }
    const candidate = await response.json();
    if (!validateWordList(candidate)) {
      throw new Error("The word list is invalid.");
    }
    words = candidate;
  }

  async function startNewGame() {
    if (loadingWords) {
      return;
    }
    if (words.length) {
      gameState = createGameState(chooseWord(words));
      requestError = "";
      guessInput.value = "";
      render();
      return;
    }

    loadingWords = true;
    requestError = "";
    render();
    try {
      await loadWordList();
      gameState = createGameState(chooseWord(words));
      guessInput.value = "";
    } catch (error) {
      requestError = `Unable to load Hangman words: ${error instanceof Error ? error.message : String(error)}`;
    } finally {
      loadingWords = false;
      render();
    }
  }

  guessForm.addEventListener("submit", (event) => {
    event.preventDefault();
    submitLetter(guessInput.value);
  });
  newGameButton.addEventListener("click", () => void startNewGame());

  render();
  void startNewGame();
}
