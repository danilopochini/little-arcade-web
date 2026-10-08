"use strict";

const GOOSE_SPACES = new Set([5, 9, 14, 18, 23, 27, 32, 36, 41, 45, 50, 54, 59]);
const SPECIALS = {
  6: {
    label: "DE BRUG",
    tone: "bridge",
    art: `<svg viewBox="0 0 100 80">
      <path d="M2 58q20-8 39 0t39 0q10-4 19 0v22H2Z" fill="#78bfd0" stroke="#315b76" stroke-width="2.5"/>
      <path d="M12 56q12-27 31-5 16-24 38 5" fill="none" stroke="#a55732" stroke-width="6" stroke-linecap="round"/>
      <path d="M9 57h76M12 49l-5-5m16-3-3-7m19 9 1-9m16 9 4-8m14 14 7-5" fill="none" stroke="#723e2b" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M4 69q12-5 24 0m37 2q13-6 30 0" fill="none" stroke="#f8efc2" stroke-width="2"/>
      <path d="M8 56V40m81 16V39" stroke="#426b46" stroke-width="3"/>
      <path d="m6 43 4-7 3 7m73-4 5-8 3 8" fill="#6d9955" stroke="#426b46" stroke-width="2"/>
    </svg>`,
  },
  19: {
    label: "DE HERBERG",
    tone: "inn",
    art: `<svg viewBox="0 0 100 80">
      <path d="M18 37 51 13l33 24v37H18Z" fill="#f1ce78" stroke="#5a4231" stroke-width="3" stroke-linejoin="round"/>
      <path d="m12 39 39-30 39 30-5 6-34-25-34 25Z" fill="#bf553c" stroke="#693b30" stroke-width="3" stroke-linejoin="round"/>
      <path d="M38 47h22v27H38Zm-14-3h12v13H24Zm38 0h12v13H62Z" fill="#83b4c0" stroke="#5a4231" stroke-width="2.5"/>
      <path d="M43 63q6-8 12 0v11H43Z" fill="#a45537" stroke="#5a4231" stroke-width="2.5"/>
      <path d="M44 32h19v8H44Z" fill="#f8edc2" stroke="#5a4231" stroke-width="2"/>
      <path d="M47 37h13" stroke="#a54335" stroke-width="2"/>
      <circle cx="54" cy="67" r="1" fill="#f7db84"/>
    </svg>`,
  },
  31: {
    label: "DE PUT",
    tone: "well",
    art: `<svg viewBox="0 0 100 80">
      <path d="M24 39h51v34H24Z" fill="#a6bd94" stroke="#4b5945" stroke-width="3"/>
      <path d="m19 39 9-10h44l9 10-7 7H26Z" fill="#c6aa70" stroke="#665239" stroke-width="3" stroke-linejoin="round"/>
      <path d="M30 48h39m-39 9h39m-39 9h39" stroke="#70815c" stroke-width="2"/>
      <path d="M23 30V8m53 22V8M19 9h58" stroke="#634734" stroke-width="4" stroke-linecap="round"/>
      <path d="M47 9v26q0 7 7 8t7-2" fill="none" stroke="#9d6540" stroke-width="2.5"/>
      <path d="M49 47h13l-2 9H51Z" fill="#c66a46" stroke="#65402f" stroke-width="2"/>
      <path d="M51 52h9" stroke="#f6d990" stroke-width="1.5"/>
    </svg>`,
  },
  42: {
    label: "HET DOOLHOF",
    tone: "maze",
    art: `<svg viewBox="0 0 100 80">
      <path d="M11 13h78v55H11Z" fill="#d6e8a6" stroke="#496c45" stroke-width="3"/>
      <path d="M20 22h17v12H25v24h17V43h14v15h21V45H64V32h15M48 22v8h11v11h13M20 64v-3m0-8h-1m27-31h-7v10m4 19v9m14-2V31h-8" fill="none" stroke="#64894d" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="m75 20 8 6-8 6" fill="none" stroke="#cf6843" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="20" cy="20" r="3" fill="#e2a342"/><circle cx="80" cy="61" r="3" fill="#df7549"/>
    </svg>`,
  },
  52: {
    label: "DE GEVANGENIS",
    tone: "prison",
    art: `<svg viewBox="0 0 100 80">
      <path d="M16 72V29q0-24 34-24t34 24v43Z" fill="#d8b98a" stroke="#594536" stroke-width="3"/>
      <path d="M25 71V33q0-17 25-17t25 17v38Z" fill="#7c9da0" stroke="#594536" stroke-width="3"/>
      <path d="M30 31v39m12-41v41m13-41v41m13-39v39" stroke="#e4d7ae" stroke-width="4"/>
      <path d="M12 72h76M24 28h52" stroke="#6b5138" stroke-width="4" stroke-linecap="round"/>
      <path d="M48 47q4-7 8 0l2 11H45Z" fill="#efcb72" stroke="#594536" stroke-width="2"/>
      <circle cx="50" cy="43" r="4" fill="#efcb72" stroke="#594536" stroke-width="2"/>
      <path d="M48 44h1m4 0h1" stroke="#594536" stroke-width="1.5"/>
    </svg>`,
  },
  58: {
    label: "DE DOOD",
    tone: "death",
    art: `<svg viewBox="0 0 100 80">
      <path d="M13 68q23-13 38 0t38 0v12H13Z" fill="#78935c" stroke="#435f43" stroke-width="2"/>
      <path d="M27 72 59 20m-4-3q15-7 22 3-11 7-22-3Z" fill="#dfd7b9" stroke="#625d4b" stroke-width="3" stroke-linejoin="round"/>
      <path d="M30 52q-3-22 17-31 21-5 26 18l-4 16q-6 10-18 11-13-1-19-14Z" fill="#484c5b" stroke="#343944" stroke-width="3"/>
      <path d="M40 24q1-15 15-16 13 2 14 17l-5 12H43Z" fill="#f1dca5" stroke="#4c4650" stroke-width="3"/>
      <circle cx="49" cy="25" r="3" fill="#fff9dc"/><circle cx="62" cy="25" r="3" fill="#fff9dc"/>
      <circle cx="49" cy="26" r="1.5" fill="#394555"/><circle cx="62" cy="26" r="1.5" fill="#394555"/>
      <path d="M51 33q5 5 10 0M44 34l-5 3m27-3 4 4" fill="none" stroke="#bd6546" stroke-width="2.5" stroke-linecap="round"/>
      <path d="m53 45 4 5-4 4 6 7m-12-1-4 5" fill="none" stroke="#eee2bd" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`,
  },
};
const TILE_COLORS = ["#ffe58c", "#f7bd80", "#bce1bd", "#a9d8e5", "#f3b6a5", "#d6c4e8"];
const ORDINARY_ART = [
  `<svg viewBox="0 0 100 80"><path d="M49 72V39m0 18L32 42m17 8 18-19" fill="none" stroke="#477444" stroke-width="4" stroke-linecap="round"/><path d="M48 41q-2-20 9-24 10 11-1 25m-9 6q-19-15-23-3 8 14 24 10m0-1q13-22 24-14-2 16-24 20" fill="#df604a" stroke="#713f42" stroke-width="2.5"/><path d="M38 70q11-6 23 0" fill="none" stroke="#9e713b" stroke-width="3"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M20 69h58M48 68V25h12v43Z" fill="#e2b451" stroke="#604637" stroke-width="3"/><path d="m53 26 1-16m6 17 22-7M53 23 35 9m22 17 1 21m0-21-19 7" fill="none" stroke="#ad4c3b" stroke-width="4" stroke-linecap="round"/><path d="m55 11 27-1-22 15m-7-1L32 8l3 27m22-9 2 25-17-16" fill="#f1d276" stroke="#684a35" stroke-width="2.5"/><circle cx="84" cy="15" r="5" fill="#e9864e"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="m16 42 35-28 35 28v29H16Z" fill="#f0cb77" stroke="#594936" stroke-width="3"/><path d="m10 42 41-34 41 34-6 6-35-28-35 28Z" fill="#cf5941" stroke="#684130" stroke-width="3"/><path d="M43 48h17v23H43Zm-19-2h12v12H24Zm43 0h12v12H67Z" fill="#87c5d1" stroke="#594936" stroke-width="2.5"/><path d="M12 72h78" stroke="#59824f" stroke-width="4"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M14 61q17-10 35 0t38 0v12H14Z" fill="#75b9ce" stroke="#315d78" stroke-width="2.5"/><path d="m34 51 30 0-6 12H28Z" fill="#cf6849" stroke="#5d4637" stroke-width="2.5"/><path d="M48 19v32H34Z" fill="#f5e6b7" stroke="#594939" stroke-width="2.5"/><path d="m51 24 19 27H51Z" fill="#e49b47" stroke="#594939" stroke-width="2.5"/><path d="M48 18v-5m-9 55q10-5 17 0m12-1q6-4 13 0" fill="none" stroke="#fff1c5" stroke-width="2.5" stroke-linecap="round"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M15 68h72M25 67V37l27-21 27 21v30Z" fill="#f0d080" stroke="#554637" stroke-width="3"/><path d="m20 39 32-27 32 27-6 6-26-22-26 22Z" fill="#ad5140" stroke="#554637" stroke-width="3"/><path d="M43 48h18v19H43Z" fill="#84b9c2" stroke="#554637" stroke-width="2.5"/><path d="M13 67V52m74 15V50M7 53l6-13 7 13m58-2 6-15 8 15" fill="#6b9c56" stroke="#4b7149" stroke-width="2"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M17 64q3-21 21-21 16 0 21 17 20-12 26 4l-2 7H19Z" fill="#d9c1a0" stroke="#584c3e" stroke-width="3"/><path d="M29 47q-3-10 2-14l9 12m4 0q7-10 13-7l-4 15" fill="#d9c1a0" stroke="#584c3e" stroke-width="3" stroke-linejoin="round"/><circle cx="43" cy="51" r="2" fill="#443b32"/><path d="m45 56 4 1-3 2m-1 10v4m10-5v5" fill="none" stroke="#584c3e" stroke-width="2.5" stroke-linecap="round"/><path d="M63 69q5-7 11 0l-2 3h-8Z" fill="#da7b59" stroke="#6a4937" stroke-width="2"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M51 69V43m0 12L35 43m16 4 16-17" fill="none" stroke="#4c7948" stroke-width="4"/><path d="M48 42q-12-14 0-19 13 5 3 19m-1 6q-14-13-20-3 5 13 20 11m2-2q9-17 18-9-2 13-19 16" fill="#efb84e" stroke="#9b5540" stroke-width="2.5"/><circle cx="75" cy="21" r="5" fill="#e98351"/><path d="m74 13 1-5m7 11 5-2M67 19l-5-2" stroke="#d46946" stroke-width="2"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M48 42 75 18l10 28-27 25Z" fill="#e66f58" stroke="#674737" stroke-width="3" stroke-linejoin="round"/><path d="m48 42 27-24m-6 56q8-14 13-16m-13 16q-6-3-13-1" fill="none" stroke="#59483b" stroke-width="2.5"/><path d="M19 69q30-7 58 0" stroke="#6c9957" stroke-width="3" fill="none"/><path d="M24 18q10-8 20 0t20 0" stroke="#84bfd1" stroke-width="3" fill="none"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M20 67q1-18 13-18 12 0 13 18m4 0q1-18 14-18 12 0 13 18" fill="#c96a48" stroke="#624838" stroke-width="3"/><path d="M17 50q16-23 32 0Zm33 0q16-26 32 0Z" fill="#f3d184" stroke="#624838" stroke-width="3"/><path d="M13 68h75M28 61v7m33-7v7" stroke="#fff0bd" stroke-width="2.5"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M20 59q0-19 20-22 19 3 20 22v13H20Z" fill="#d8bd8d" stroke="#584b3d" stroke-width="3"/><path d="M17 59q22-9 46 0v8H17Z" fill="#b94e40" stroke="#584b3d" stroke-width="2.5"/><path d="M64 65q5-19 15-19t11 19" fill="#f0cc73" stroke="#584b3d" stroke-width="3"/><path d="M70 49v15m7-17v17m7-14v14" stroke="#a86043" stroke-width="2.5"/><circle cx="28" cy="27" r="4" fill="#e68b4b"/><circle cx="43" cy="17" r="3" fill="#e5b649"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M16 67h68M25 64V34h50v30Z" fill="#dfc987" stroke="#554839" stroke-width="3"/><path d="M20 38 51 15l30 23" fill="#8bac67" stroke="#554839" stroke-width="3" stroke-linejoin="round"/><path d="M32 43v18m15-18v18m15-18v18" stroke="#678650" stroke-width="3"/><path d="M39 47q10-12 19 0m-19 3h19" fill="none" stroke="#f8edc4" stroke-width="2.5"/><circle cx="51" cy="43" r="3" fill="#d76e49"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M18 68q4-24 17-24t17 24m6 0q2-17 13-17t13 17" fill="#d99b4f" stroke="#594837" stroke-width="3"/><path d="M28 49q7-12 14 0m28 9q5-9 11 0" fill="#e9d18f" stroke="#594837" stroke-width="2.5"/><circle cx="37" cy="56" r="2" fill="#453b32"/><circle cx="72" cy="65" r="2" fill="#453b32"/><path d="M23 68h59" stroke="#638a4d" stroke-width="3"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M50 67V39m0 15L35 43m15 2 15-15" fill="none" stroke="#4f7945" stroke-width="4"/><path d="M49 39q-13-13-1-19 12 5 3 19m0 7q14-15 20-5-5 13-19 13m-2-6q-14-12-20-2 6 12 21 11" fill="#f2d36f" stroke="#a45a40" stroke-width="2.5"/><circle cx="78" cy="19" r="5" fill="#e9884a"/><path d="M77 12V7m7 10 5-2m-17-1-4-4" stroke="#c45e45" stroke-width="2"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M17 66q16-8 34 0t33 0" fill="none" stroke="#5a8b50" stroke-width="4"/><path d="M24 54q-4-21 11-25 13 1 12 25Z" fill="#e2764b" stroke="#594637" stroke-width="3"/><path d="M22 53q13-7 28 0" fill="#f5dfa0" stroke="#594637" stroke-width="2.5"/><path d="M57 64q2-19 17-19t16 19" fill="#d7bd98" stroke="#594637" stroke-width="3"/><circle cx="68" cy="56" r="1.8" fill="#473b33"/><circle cx="79" cy="56" r="1.8" fill="#473b33"/><path d="m73 59 3 2-3 2" fill="#d7755a"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M13 67h75M24 67V41l25-18 26 18v26Z" fill="#f2d278" stroke="#594837" stroke-width="3"/><path d="m18 43 31-24 32 24-6 5-26-19-25 19Z" fill="#5787a3" stroke="#594837" stroke-width="3"/><path d="M39 49h19v18H39Z" fill="#d56a4b" stroke="#594837" stroke-width="2.5"/><path d="M27 47h8v10h-8Zm40 0h8v10h-8Z" fill="#8ecbd0" stroke="#594837" stroke-width="2"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M50 70V37m0 17L36 41m14 8 15-15" fill="none" stroke="#4b7948" stroke-width="4"/><path d="M48 38q-12-13 0-20 13 7 3 20m-2 9q-13-13-20-3 8 14 22 11m1-1q13-17 20-8-5 15-21 16" fill="#dd6550" stroke="#764640" stroke-width="2.5"/><path d="M76 56q10-6 14 0l-4 3 4 3q-6 5-13 0l-5-3Z" fill="#edc74f" stroke="#504841" stroke-width="2"/><circle cx="82" cy="57" r="1" fill="#3e4141"/></svg>`,
  `<svg viewBox="0 0 100 80"><path d="M50 68V37m0 14L35 39m15 6 15-16" fill="none" stroke="#4f7845" stroke-width="4"/><path d="M48 38q-10-14 2-21 12 8 2 21m-2 7q-14-11-20-1 7 12 22 10m0-3q10-16 20-7-4 14-20 16" fill="#e9b449" stroke="#9b5640" stroke-width="2.5"/><path d="M76 21q7-10 14 0-7 11-14 0Zm-6 1-5-4m24 4 5-4m-13-7V8" fill="#78aebf" stroke="#3c6171" stroke-width="2"/></svg>`,
];
const GOOSE_ART = `<svg viewBox="0 0 100 80">
  <path d="M12 62q-2-13 11-18 11-4 19 4 7-4 13-2 8 2 12 9-4 10-17 12-10 2-19-3-10 4-19-2Z" fill="#f9efc8" stroke="#425d48" stroke-width="3" stroke-linejoin="round"/>
  <path d="M35 52q8-12 17-5 5 5 1 13-7 6-15 1" fill="#d6dfaa" stroke="#526849" stroke-width="2.5" stroke-linejoin="round"/>
  <path d="M43 51q4-4 7 0m-4 4q3-2 5 0" fill="none" stroke="#809065" stroke-width="2"/>
  <path d="M59 52q8-5 7-15-1-8 5-13 8 7 5 15 5-2 11 1l-10 5q-1 10-9 14" fill="#fff2c8" stroke="#425d48" stroke-width="3" stroke-linejoin="round"/>
  <circle cx="72" cy="31" r="2.2" fill="#33423a"/>
  <path d="m79 37 12 1-10 5" fill="#e98943" stroke="#81473a" stroke-width="2.3" stroke-linejoin="round"/>
  <path d="m34 68-2 7m11-6-1 7m-15-2h8m4 0h7" fill="none" stroke="#d5743e" stroke-width="2.6" stroke-linecap="round"/>
  <path d="M9 72q8-4 14 0m52 1q8-4 14 0" fill="none" stroke="#54834b" stroke-width="2"/>
</svg>`;
const DIE_FACES = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"];
const AUTO_DELAY = 560;

const boardElement = document.querySelector("#goose-board");
const statusElement = document.querySelector("#game-status");
const playerList = document.querySelector("#player-list");
const dieOne = document.querySelector("#die-one");
const dieTwo = document.querySelector("#die-two");
const rollButton = document.querySelector("#roll-button");
const newGameButton = document.querySelector("#new-game");
const playerCount = document.querySelector("#player-count");
const statusPaper = document.querySelector("#status-paper");

const SERVER_INSTRUCTIONS = "Start het spel met `python ganzenbord_browser.py` en laat het terminalvenster open.";

let gameState = null;
let requestPending = false;
let requestError = "";
let animationTimer = null;
let autoTimer = null;
let animationSequence = 0;

async function sendAction(path, payload = {}) {
  if (window.location.protocol === "file:") {
    throw new Error(`Dit bestand kan niet rechtstreeks worden geopend. ${SERVER_INSTRUCTIONS}`);
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
      throw new Error(`De lokale spelserver is niet bereikbaar. ${SERVER_INSTRUCTIONS}`);
    }
    throw error;
  }
  if (!response.headers.get("content-type")?.includes("application/json")) {
    throw new Error(`Deze pagina is niet verbonden met de spelserver. ${SERVER_INSTRUCTIONS}`);
  }
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.error || `De spelserver gaf fout ${response.status}.`);
  }
  return result;
}

function createCell(square, row, column) {
  const cell = document.createElement("div");
  const special = SPECIALS[square];
  const goose = GOOSE_SPACES.has(square);
  cell.className = [
    "board-cell",
    goose ? "goose-square" : "",
    special ? `special-${special.tone}` : "",
    square === 1 ? "start-square" : "",
    square === 63 ? "goal-square" : "",
  ].filter(Boolean).join(" ");
  cell.style.gridRow = String(row + 1);
  cell.style.gridColumn = String(column + 1);
  cell.style.setProperty("--tile-color", TILE_COLORS[(square * 5 + Math.floor(square / 3)) % TILE_COLORS.length]);
  cell.style.setProperty("--goose-tilt", `${(square % 3 - 1) * 5}deg`);
  cell.dataset.square = String(square);
  cell.setAttribute("role", "gridcell");
  cell.setAttribute(
    "aria-label",
    special ? `Vak ${square}, ${special.label.toLowerCase()}` : goose ? `Vak ${square}, de gans` : `Vak ${square}`,
  );

  const number = document.createElement("span");
  number.className = "square-number";
  number.textContent = String(square);
  cell.append(number);
  if (goose || special || square === 1 || square === 63) {
    const artwork = document.createElement("span");
    artwork.className = `tile-art${goose ? " goose-illustration" : ""}`;
    artwork.setAttribute("aria-hidden", "true");
    artwork.innerHTML = goose
      ? GOOSE_ART
      : special
        ? special.art
        : square === 1
          ? `<svg viewBox="0 0 100 80"><path d="M16 69h69M25 67V39l26-21 27 21v28Z" fill="#f3cd71" stroke="#594637" stroke-width="3"/><path d="m19 41 32-27 34 27-7 6-27-21-27 21Z" fill="#bf5140" stroke="#594637" stroke-width="3"/><path d="M41 49h19v18H41Z" fill="#80b9ca" stroke="#594637" stroke-width="2.5"/><path d="M14 68V52m75 16V50M9 54l5-13 7 13m59-1 7-15 8 15" fill="#63934d" stroke="#4c7147" stroke-width="2"/></svg>`
          : `<svg viewBox="0 0 100 80"><path d="M9 66h82" stroke="#57864b" stroke-width="4"/><path d="M22 65q-2-13 11-18 11-4 19 4 8-5 17-2 9 3 12 11-8 9-21 7-13 3-22-3-9 5-16 1Z" fill="#fbefc4" stroke="#47604a" stroke-width="3"/><path d="M60 53q8-4 7-14-1-7 6-12 8 7 5 15 6-2 12 1l-10 5q-2 8-9 11" fill="#fff2cc" stroke="#47604a" stroke-width="3" stroke-linejoin="round"/><circle cx="73" cy="32" r="2" fill="#33433a"/><path d="m80 38 11 1-9 4" fill="#e88943" stroke="#7c4836" stroke-width="2"/></svg>`;
    cell.append(artwork);
  } else {
    const illustration = document.createElement("span");
    illustration.className = "tile-art";
    illustration.setAttribute("aria-hidden", "true");
    illustration.innerHTML = ORDINARY_ART[(square * 7 + Math.floor(square / 2)) % ORDINARY_ART.length];
    cell.append(illustration);
  }
  if (goose) {
    const caption = document.createElement("span");
    caption.className = "tile-caption";
    caption.textContent = "DE GANS";
    cell.append(caption);
  } else if (special) {
    const caption = document.createElement("span");
    caption.className = "tile-caption";
    caption.textContent = special.label;
    cell.append(caption);
  } else if (square === 1) {
    const caption = document.createElement("span");
    caption.className = "tile-caption";
    caption.textContent = "START";
    cell.append(caption);
  } else if (square === 63) {
    const caption = document.createElement("span");
    caption.className = "tile-caption";
    caption.textContent = "THUIS!";
    cell.append(caption);
  }
  boardElement.append(cell);
}

function buildBoard() {
  boardElement.replaceChildren();
  for (const [index, [row, column]] of gameState.board.coordinates.entries()) {
    createCell(index + 1, row, column);
  }
  const centre = document.createElement("div");
  centre.className = "board-centre";
  centre.setAttribute("aria-hidden", "true");
  centre.innerHTML = `<svg class="centre-landscape" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice">
    <path d="M0 0h400v300H0Z" fill="#b9deea"/>
    <circle cx="333" cy="48" r="23" fill="#f7cf62" stroke="#c78645" stroke-width="3"/>
    <path d="M0 153q55-36 112 0t113-2q74-36 175 4v145H0Z" fill="#91ba70" stroke="#597d51" stroke-width="3"/>
    <path d="M0 195q62-36 132-1t134 1q72-38 134-4v109H0Z" fill="#75a65c" stroke="#4b7848" stroke-width="3"/>
    <path d="M39 133 79 99l43 34v48H39Z" fill="#f2cf7c" stroke="#554737" stroke-width="4"/>
    <path d="m31 137 48-43 51 43-8 8-43-35-40 35Z" fill="#c75943" stroke="#603e36" stroke-width="4"/>
    <path d="M69 152h24v29H69Z" fill="#81bdc9" stroke="#554737" stroke-width="3"/>
    <path d="M269 167V87h14v80m-19-79h23m-18-2 3-40m8 41 47-14m-56 11-37-35m41 38 2 46m1-46-40 16" fill="none" stroke="#684b36" stroke-width="5" stroke-linecap="round"/>
    <path d="m271 48 4-42 49-13-47 37m-4 15-42-38 4 47m40-11 3 49 34-36" fill="#f3d276" stroke="#684b36" stroke-width="3" stroke-linejoin="round"/>
    <path d="M176 212q-1-24 23-34 18-6 31 8 15-9 33-3 17 5 21 20-12 16-37 12-20 10-39-1-18 9-32-2Z" fill="#fff1c9" stroke="#405d49" stroke-width="5" stroke-linejoin="round"/>
    <path d="M214 191q16-17 31-7 8 9 1 20-11 9-27 1" fill="#d6dda8" stroke="#526b4c" stroke-width="4" stroke-linejoin="round"/>
    <path d="M251 193q13-8 11-25-2-15 11-24 15 13 9 28 12-5 23 2l-17 7q-3 17-17 21" fill="#fff2cf" stroke="#405d49" stroke-width="5" stroke-linejoin="round"/>
    <circle cx="274" cy="151" r="3" fill="#33443c"/><path d="m285 162 22 2-18 8" fill="#e98540" stroke="#794538" stroke-width="3" stroke-linejoin="round"/>
    <path d="m211 218-3 12m18-11-2 12m-17-2h14m1 2h14" fill="none" stroke="#d8773e" stroke-width="4" stroke-linecap="round"/>
    <path d="M166 241q19-14 39 0m88-2q20-14 42 1m-202 5q12-9 25 0" fill="none" stroke="#fff1c8" stroke-width="3" stroke-linecap="round"/>
  </svg><span class="centre-title">OP REIS<br>MET DE GANS</span>`;
  boardElement.append(centre);
}

function makeToken(player, playerIndex) {
  const token = document.createElement("span");
  token.className = `playing-piece piece-${playerIndex}`;
  token.style.setProperty("--piece-color", player.color);
  token.textContent = player.shape;
  token.setAttribute("aria-label", `${player.name}, pion`);
  return token;
}

function renderPlayers() {
  playerList.replaceChildren();
  for (const [index, player] of gameState.players.entries()) {
    const card = document.createElement("div");
    card.className = `player-card${index === gameState.current_player && !gameState.finished ? " is-current" : ""}`;
    card.style.setProperty("--piece-color", player.color);
    const token = makeToken(player, index);
    const description = document.createElement("span");
    description.className = "player-description";
    const name = document.createElement("strong");
    name.textContent = player.name;
    const position = document.createElement("small");
    position.textContent = player.position ? `Vak ${player.position}` : "Bij de start";
    description.append(name, position);
    card.append(token, description);
    playerList.append(card);
  }
}

function renderPieces() {
  for (const cell of boardElement.querySelectorAll(".board-cell")) {
    cell.querySelectorAll(".playing-piece").forEach((piece) => piece.remove());
  }
  for (const [playerIndex, player] of gameState.players.entries()) {
    if (!player.position) {
      continue;
    }
    const cell = boardElement.querySelector(`[data-square="${player.position}"]`);
    if (cell) {
      const token = makeToken(player, playerIndex);
      token.dataset.player = String(playerIndex);
      token.dataset.piece = String(playerIndex);
      cell.append(token);
    }
  }
}

function setStatus(text, kind = "normal") {
  statusElement.textContent = text;
  statusPaper.dataset.state = kind;
}

function render() {
  if (!gameState) {
    setStatus(requestError || "Het bord wordt klaargezet...", requestError ? "error" : "normal");
    rollButton.disabled = true;
    return;
  }
  const note = gameState.finished
    ? gameState.special_note
    : requestError || gameState.special_note;
  setStatus(note, requestError ? "error" : gameState.finished ? "winner" : "normal");
  buildBoard();
  renderPlayers();
  renderPieces();

  if (gameState.last_roll) {
    dieOne.textContent = DIE_FACES[gameState.last_roll.dice[0] - 1];
    dieTwo.textContent = DIE_FACES[gameState.last_roll.dice[1] - 1];
  } else {
    dieOne.textContent = "⚀";
    dieTwo.textContent = "⚀";
  }
  const current = gameState.players[gameState.current_player];
  rollButton.disabled = requestPending
    || gameState.finished
    || gameState.phase !== "awaiting_roll"
    || gameState.current_player !== 0
    || current.skip_turns > 0
    || current.blocked_on_well
    || current.blocked_in_prison;
  newGameButton.disabled = requestPending;
  playerCount.disabled = requestPending;
  scheduleAutomaticTurn();
}

function scheduleAutomaticTurn() {
  if (autoTimer !== null) {
    clearTimeout(autoTimer);
    autoTimer = null;
  }
  if (
    requestPending
    || requestError
    || !gameState
    || gameState.finished
    || gameState.phase !== "awaiting_roll"
  ) {
    return;
  }
  const current = gameState.players[gameState.current_player];
  if (current.skip_turns > 0) {
    autoTimer = setTimeout(() => {
      autoTimer = null;
      void runAction("/api/skip");
    }, 850);
  } else if (gameState.current_player !== 0) {
    autoTimer = setTimeout(() => {
      autoTimer = null;
      void runAction("/api/computer");
    }, 1000);
  }
}

function animateDice() {
  dieOne.classList.add("is-rolling");
  dieTwo.classList.add("is-rolling");
  rollButton.disabled = true;
  const start = Date.now();
  animationTimer = setInterval(() => {
    dieOne.textContent = DIE_FACES[Math.floor(Math.random() * DIE_FACES.length)];
    dieTwo.textContent = DIE_FACES[Math.floor(Math.random() * DIE_FACES.length)];
    if (Date.now() - start > 700) {
      clearInterval(animationTimer);
      animationTimer = null;
      dieOne.classList.remove("is-rolling");
      dieTwo.classList.remove("is-rolling");
      if (gameState?.last_roll) {
        dieOne.textContent = DIE_FACES[gameState.last_roll.dice[0] - 1];
        dieTwo.textContent = DIE_FACES[gameState.last_roll.dice[1] - 1];
      }
    }
  }, 70);
}

function animatePawn(state) {
  const effect = state.turn_effect;
  if (!effect || effect.player === undefined || !effect.path.length) {
    return Promise.resolve();
  }
  const player = state.players[effect.player];
  const marker = document.createElement("span");
  marker.className = `moving-piece piece-${effect.player}`;
  marker.style.setProperty("--piece-color", player.color);
  marker.textContent = player.shape;
  const boardRect = boardElement.getBoundingClientRect();
  marker.style.left = "0";
  marker.style.top = "0";
  marker.style.marginLeft = "-50%";
  marker.style.marginTop = "-50%";
  boardElement.append(marker);
  const token = boardElement.querySelector(
    `.playing-piece[data-player="${effect.player}"]`,
  );
  if (token) {
    token.style.visibility = "hidden";
  }

  return new Promise((resolve) => {
    let index = 0;
    const moveNext = () => {
      if (index >= effect.path.length) {
        marker.remove();
        if (token) {
          token.style.visibility = "";
        }
        resolve();
        return;
      }
      const target = boardElement.querySelector(`[data-square="${effect.path[index]}"]`);
      if (target) {
        const targetRect = target.getBoundingClientRect();
        marker.style.transform = `translate(${targetRect.left - boardRect.left + targetRect.width / 2}px, ${targetRect.top - boardRect.top + targetRect.height / 2}px)`;
      }
      index += 1;
      window.setTimeout(moveNext, index < effect.path.length ? 90 : 160);
    };
    window.setTimeout(moveNext, 90);
  });
}

async function runAction(path, payload = {}) {
  if (requestPending) {
    return;
  }
  requestPending = true;
  render();
  if (path === "/api/roll" || path === "/api/computer") {
    animateDice();
  }
  try {
    const nextState = await sendAction(path, payload);
    requestError = "";
    if (path === "/api/roll" || path === "/api/computer") {
      gameState = nextState;
      render();
      await animatePawn(nextState);
      if (!nextState.finished) {
        gameState = await sendAction("/api/finish");
      }
    } else {
      gameState = nextState;
    }
  } catch (error) {
    requestError = `Het spel kon niet worden bijgewerkt: ${error instanceof Error ? error.message : String(error)}`;
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
    gameState = await sendAction("/api/new", { players: Number(playerCount.value) });
    requestError = "";
    dieOne.textContent = "⚀";
    dieTwo.textContent = "⚀";
  } catch (error) {
    requestError = `Het spel kon niet worden gestart: ${error instanceof Error ? error.message : String(error)}`;
  } finally {
    requestPending = false;
    render();
  }
}

rollButton.addEventListener("click", () => void runAction("/api/roll"));
newGameButton.addEventListener("click", () => void startNewGame());

async function initialize() {
  try {
    gameState = await sendAction("/api/new", { players: Number(playerCount.value) });
    requestError = "";
  } catch (error) {
    requestError = `De spelserver is niet bereikbaar: ${error instanceof Error ? error.message : String(error)}`;
  } finally {
    render();
  }
}

render();
void initialize();
