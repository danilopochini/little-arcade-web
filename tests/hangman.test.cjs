"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const {
  MAX_WRONG_GUESSES,
  chooseWord,
  createGameState,
  getPublicGameState,
  submitGuess,
} = require("../hangman.js");

test("the static word list preserves the Python wordfreq filter", () => {
  const words = JSON.parse(
    fs.readFileSync(path.join(__dirname, "..", "hangman_words.json"), "utf8"),
  );

  assert.equal(words.length, 780);
  assert.ok(words.every((word) => /^[A-Z]{4,9}$/.test(word)));
  assert.equal(chooseWord(words, () => 0), words[0]);
});

test("guesses are trimmed and normalized, and correct letters are revealed", () => {
  const state = createGameState("APPLE");

  submitGuess(state, " a ");

  assert.equal(state.status, "Correct! A is in the word.");
  assert.equal(state.status_kind, "success");
  assert.equal(getPublicGameState(state).word_display, "A _ _ _ _");
});

test("invalid guesses do not change game progress", () => {
  const state = createGameState("APPLE");

  assert.throws(
    () => submitGuess(state, "AB"),
    { message: "Enter one letter from A to Z, or type QUIT to reveal the word." },
  );
  assert.equal(state.wrong_guesses, 0);
  assert.deepEqual([...state.guessed_letters], []);
});

test("repeated guesses are muted and do not count as incorrect", () => {
  const state = createGameState("APPLE");
  submitGuess(state, "Z");
  submitGuess(state, " z ");

  assert.equal(state.wrong_guesses, 1);
  assert.equal(state.status, "You already guessed Z. Try another letter.");
  assert.equal(state.status_kind, "muted");
});

test("QUIT ends the round, reveals the word, and adds no mistake", () => {
  const state = createGameState("APPLE");

  submitGuess(state, " quit ");

  assert.equal(state.finished, true);
  assert.equal(state.wrong_guesses, 0);
  assert.equal(state.status, "You quit! The word was APPLE.");
  assert.equal(state.status_kind, "muted");
  assert.equal(getPublicGameState(state).word_display, "A P P L E");
});

test("winning reveals the word and reports success", () => {
  const state = createGameState("ABBA");
  for (const letter of ["A", "B"]) {
    submitGuess(state, letter);
  }

  assert.equal(state.finished, true);
  assert.equal(state.status, "You won! The word was ABBA.");
  assert.equal(state.status_kind, "success");
  assert.equal(getPublicGameState(state).word_display, "A B B A");
});

test("the tenth distinct incorrect guess ends the game and reveals the word", () => {
  const state = createGameState("ABCD");
  for (const letter of "EFGHIJKLMN") {
    submitGuess(state, letter);
  }

  const publicState = getPublicGameState(state);
  assert.equal(MAX_WRONG_GUESSES, 10);
  assert.equal(state.finished, true);
  assert.equal(state.wrong_guesses, MAX_WRONG_GUESSES);
  assert.equal(state.status, "Game over! The word was ABCD.");
  assert.equal(state.status_kind, "error");
  assert.equal(publicState.word_display, "A B C D");
});

test("new game state is independent", () => {
  const first = createGameState("APPLE");
  const second = createGameState("PEAR");
  submitGuess(first, "Z");

  assert.equal(first.wrong_guesses, 1);
  assert.equal(second.wrong_guesses, 0);
  assert.deepEqual([...second.guessed_letters], []);
});
