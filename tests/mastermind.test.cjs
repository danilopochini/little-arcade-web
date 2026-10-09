"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const {
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
} = require("../mastermind.js");

test("game uses four pegs, six colors, and ten turns", () => {
  assert.equal(CODE_LENGTH, 4);
  assert.equal(PALETTE.length, 6);
  assert.equal(MAX_TURNS, 10);
});

test("secret codes are four randomly selected palette colors", () => {
  assert.deepEqual(generateSecretCode(() => 0), [0, 0, 0, 0]);
  assert.deepEqual(generateSecretCode(() => 0.99), [5, 5, 5, 5]);
});

test("feedback counts exact matches first and does not double-count duplicates", () => {
  assert.deepEqual(
    scoreGuess([0, 0, 1, 1], [0, 1, 0, 0]),
    { exact: 1, color_only: 2 },
  );
  assert.deepEqual(
    scoreGuess([0, 0, 0, 1], [0, 1, 1, 1]),
    { exact: 2, color_only: 0 },
  );
});

test("guess actions allow repeated colors, clear a guess, and remove its last peg", () => {
  const state = createGameState([0, 1, 2, 3]);
  addPin(state, 4);
  addPin(state, 4);
  addPin(state, 1);
  assert.deepEqual(state.current_guess, [4, 4, 1]);

  removePin(state);
  assert.deepEqual(state.current_guess, [4, 4]);
  assert.equal(state.status, "Last peg removed.");
  clearGuess(state);
  assert.deepEqual(state.current_guess, []);
  assert.equal(state.status, "Guess cleared. Choose four colors.");
});

test("incomplete guesses are rejected without changing turns", () => {
  const state = createGameState([0, 1, 2, 3]);
  addPin(state, 0);
  submitGuess(state);

  assert.equal(state.status, "Choose 3 more pegs before submitting.");
  assert.equal(state.status_kind, "error");
  assert.equal(state.turn, 1);
  assert.deepEqual(state.guesses, []);
});

test("winning a round records feedback and disables further play", () => {
  const state = createGameState([0, 1, 2, 3]);
  for (const pin of [0, 1, 2, 3]) {
    addPin(state, pin);
  }
  submitGuess(state);

  assert.equal(state.finished, true);
  assert.equal(state.won, true);
  assert.equal(state.status, "Code cracked! You win — click New Game to play again.");
  assert.equal(state.status_kind, "success");
  assert.deepEqual(state.guesses[0].feedback, { exact: 4, color_only: 0 });
  assert.deepEqual(state.current_guess, []);
});

test("the tenth missed guess loses and reveals the secret code", () => {
  const state = createGameState([0, 1, 2, 3]);
  for (let turn = 0; turn < MAX_TURNS; turn += 1) {
    for (const pin of [5, 5, 5, 5]) {
      addPin(state, pin);
    }
    submitGuess(state);
  }

  assert.equal(state.finished, true);
  assert.equal(state.won, false);
  assert.equal(state.guesses.length, MAX_TURNS);
  assert.equal(
    state.status,
    "Out of guesses! The code was Ruby  Tangerine  Sunshine  Jade.",
  );
  assert.equal(state.status_kind, "error");
});

test("new state creation starts an independent game", () => {
  const first = createGameState([0, 1, 2, 3]);
  const second = createGameState([3, 2, 1, 0]);
  addPin(first, 5);

  assert.deepEqual(first.current_guess, [5]);
  assert.deepEqual(second.current_guess, []);
  assert.deepEqual(second.secret_code, [3, 2, 1, 0]);
});
