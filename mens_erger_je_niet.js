"use strict";

const PLAYER_COLORS = ["red", "blue", "yellow", "green"];
const BOARD_SIZE = 15;
const statusBar = document.querySelector("#status-bar");
const statusElement = document.querySelector("#game-status");
const playersElement = document.querySelector("#players");
const boardElement = document.querySelector("#game-board");
const dieFace = document.querySelector("#die-face");
const rollButton = document.querySelector("#roll-die");
const newGameButton = document.querySelector("#new-game");

const SERVER_INSTRUCTIONS = "Run `python mens_erger_je_niet_browser.py` and keep its terminal window open while playing.";

let gameState = null;
let requestPending = false;
let requestError = "";
let computerTimer = null;

async function sendAction(path, payload = {}) {
  if (window.location.protocol === "file:") {
    throw new Error(`Opening the game page directly cannot reach its server. ${SERVER_INSTRUCTIONS}`);
  }

  let response;
  try {
    response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(`The local game server is unreachable. ${SERVER_INSTRUCTIONS}`);
    }
    throw error;
  }
  if (!response.headers.get("content-type")?.includes("application/json")) {
    throw new Error(`This page is not connected to the game server. ${SERVER_INSTRUCTIONS}`);
  }
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || `The game server returned HTTP ${response.status}.`);
  }
  return result;
}

function addBoardCell(row, column, classNames, label = "") {
  const cell = document.createElement("div");
  cell.className = `board-cell ${classNames}`.trim();
  cell.style.gridRow = String(row + 1);
  cell.style.gridColumn = String(column + 1);
  cell.setAttribute("role", "gridcell");
  if (label) {
    cell.setAttribute("aria-label", label);
  }
  boardElement.append(cell);
  return cell;
}

function buildBoard() {
  const rowClasses = {
    red: (row, column) => row >= 9 && column <= 5,
    blue: (row, column) => row <= 5 && column <= 5,
    yellow: (row, column) => row <= 5 && column >= 9,
    green: (row, column) => row >= 9 && column >= 9,
  };
  const trackByCell = new Map(
    gameState.board.track.map(([row, column], index) => [`${row},${column}`, index]),
  );
  const laneByCell = new Map();
  for (const [playerIndex, lane] of gameState.board.home_lanes.entries()) {
    for (const coordinate of lane) {
      laneByCell.set(coordinate.join(","), playerIndex);
    }
  }

  boardElement.replaceChildren();
  for (let row = 0; row < BOARD_SIZE; row += 1) {
    for (let column = 0; column < BOARD_SIZE; column += 1) {
      const key = `${row},${column}`;
      const basePlayer = PLAYER_COLORS.findIndex((color) => rowClasses[color](row, column));
      const classes = [];
      let label = `Board row ${row + 1}, column ${column + 1}`;
      if (basePlayer !== -1) {
        classes.push(`base-${PLAYER_COLORS[basePlayer]}`);
      }
      if (trackByCell.has(key)) {
        classes.push("track-space");
        const trackIndex = trackByCell.get(key);
        const startingPlayer = gameState.board.starts.indexOf(trackIndex);
        if (startingPlayer !== -1) {
          classes.push(`start-${PLAYER_COLORS[startingPlayer]}`);
          label = `${PLAYER_COLORS[startingPlayer]} start space`;
        } else {
          label = "Track space";
        }
      }
      if (laneByCell.has(key)) {
        const lanePlayer = laneByCell.get(key);
        classes.push(`home-lane-${PLAYER_COLORS[lanePlayer]}`);
        label = `${PLAYER_COLORS[lanePlayer]} home lane`;
      }
      if (row >= 6 && row <= 8 && column >= 6 && column <= 8) {
        classes.push("center-space");
      }
      const goalPlayer = gameState.board.goal_spaces.findIndex(
        ([goalRow, goalColumn]) => goalRow === row && goalColumn === column,
      );
      if (goalPlayer !== -1) {
        classes.push(`goal-${PLAYER_COLORS[goalPlayer]}`);
        label = `${PLAYER_COLORS[goalPlayer]} home`;
      }

      const cell = addBoardCell(row, column, classes.join(" "), label);
      if (basePlayer !== -1 && gameState.board.base_spaces[basePlayer].some(
        ([baseRow, baseColumn]) => baseRow === row && baseColumn === column,
      )) {
        cell.classList.add("base-socket");
      }
    }
  }
}

function boardCoordinate(playerIndex, progress, pawnIndex) {
  if (progress === -1) {
    return gameState.board.base_spaces[playerIndex][pawnIndex];
  }
  if (progress === 57) {
    return gameState.board.goal_spaces[playerIndex];
  }
  if (progress >= 52) {
    return gameState.board.home_lanes[playerIndex][progress - 52];
  }
  const trackIndex = (gameState.board.starts[playerIndex] + progress) % gameState.board.track.length;
  return gameState.board.track[trackIndex];
}

function renderPlayers() {
  playersElement.replaceChildren();
  for (const [index, player] of gameState.players.entries()) {
    const card = document.createElement("div");
    card.className = `player-card ludo-player-card${index === gameState.current_player ? " is-active" : ""}`;
    const disc = document.createElement("span");
    disc.className = `player-disc pawn-${PLAYER_COLORS[index]}`;
    disc.setAttribute("aria-hidden", "true");
    const details = document.createElement("span");
    details.className = "player-details";
    const name = document.createElement("span");
    name.className = "player-name";
    name.textContent = player.label;
    const homeCount = player.pawns.filter((progress) => progress === 57).length;
    const count = document.createElement("span");
    count.className = "player-color";
    count.textContent = `${homeCount}/4 home`;
    details.append(name, count);
    card.append(disc, details);
    playersElement.append(card);
  }
}

function renderPawns() {
  const cells = new Map();
  for (const [playerIndex, player] of gameState.players.entries()) {
    player.pawns.forEach((progress, pawnIndex) => {
      const [row, column] = boardCoordinate(playerIndex, progress, pawnIndex);
      const key = `${row},${column}`;
      if (!cells.has(key)) {
        cells.set(key, []);
      }
      cells.get(key).push({ playerIndex, pawnIndex });
    });
  }

  for (const cell of boardElement.querySelectorAll(".board-cell")) {
    const key = `${Number(cell.style.gridRow) - 1},${Number(cell.style.gridColumn) - 1}`;
    const pawns = cells.get(key) || [];
    for (const { playerIndex, pawnIndex } of pawns) {
      const color = PLAYER_COLORS[playerIndex];
      const button = document.createElement("button");
      button.type = "button";
      button.className = `pawn pawn-${color}`;
      button.textContent = String(pawnIndex + 1);
      button.setAttribute("aria-label", `${gameState.players[playerIndex].label}, pawn ${pawnIndex + 1}`);
      const canMove = playerIndex === 0
        && gameState.current_player === 0
        && gameState.phase === "awaiting_move"
        && gameState.legal_moves.includes(pawnIndex);
      button.disabled = requestPending || !canMove;
      if (canMove) {
        button.classList.add("is-selectable");
      }
      if (pawns.length > 1) {
        button.style.setProperty("--stack-index", String(pawns.findIndex(
          (pawn) => pawn.playerIndex === playerIndex && pawn.pawnIndex === pawnIndex,
        )));
      }
      button.addEventListener("click", () => void runAction("/api/move", { pawn: pawnIndex }));
      cell.append(button);
    }
  }
}

function render() {
  if (!gameState) {
    statusElement.textContent = requestError || "Loading game...";
    statusBar.dataset.state = requestError ? "error" : "loading";
    newGameButton.disabled = requestPending;
    rollButton.disabled = true;
    return;
  }

  statusElement.textContent = requestError || gameState.status;
  statusBar.dataset.state = requestError
    ? "error"
    : gameState.finished
      ? "success"
      : gameState.current_player === 0
        ? "human"
        : "computer";
  const displayedRoll = gameState.roll || gameState.last_action?.roll;
  dieFace.textContent = displayedRoll ? String(displayedRoll) : "—";
  dieFace.setAttribute(
    "aria-label",
    displayedRoll ? `Die rolled ${displayedRoll}` : "Die not rolled",
  );
  rollButton.disabled = requestPending
    || gameState.finished
    || gameState.phase !== "awaiting_roll"
    || gameState.current_player !== 0;
  newGameButton.disabled = requestPending;
  renderPlayers();
  buildBoard();
  renderPawns();
  scheduleComputerTurn();
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

function scheduleComputerTurn() {
  if (computerTimer !== null) {
    clearTimeout(computerTimer);
    computerTimer = null;
  }
  if (
    requestError
    || requestPending
    || !gameState
    || gameState.finished
    || gameState.phase !== "awaiting_roll"
    || gameState.current_player === 0
  ) {
    return;
  }
  computerTimer = setTimeout(() => {
    computerTimer = null;
    void runAction("/api/computer");
  }, 650);
}

rollButton.addEventListener("click", () => void runAction("/api/roll"));
newGameButton.addEventListener("click", () => void runAction("/api/new"));

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
