# Classic Games Arcade

The arcade homepage and shared site styles live in `arcade/`. Its game cards open the existing Chess, Checkers, Connect Four, Sudoku, Mastermind, and Hangman browser pages.

Start the arcade and its local game APIs from this folder:

```bash
python -m pip install -r hangman-requirements.txt
python arcade_server.py
```

The server opens the homepage in Chrome. Keep the terminal window open while playing, and press **Ctrl+C** there to stop it. Chess, Checkers, Connect Four, and Sudoku load their Python game logic in the browser using Pyodide, so those games need an internet connection on first load. Mastermind and Hangman use the local arcade server for game actions.

# Hangman game

Run the game by executing `hangman.py` from this folder:

```bash
python -m pip install -r hangman-requirements.txt
python hangman.py
```

The game uses the `wordfreq` package's 1,000 most common English words and randomly chooses from those that are 4–9 letters long. The list is available locally after installation, so an internet connection is not needed while playing. Enter a letter and press **Guess** or **Enter**; type `quit` to reveal the word and end the round. Choose **New Game** to start another round.

### Hangman in Chrome

Run the browser version from this folder with:

```bash
python hangman_browser.py
```

The script starts a local web server and opens Hangman in Google Chrome. Keep the terminal window open while playing; press **Ctrl+C** there to stop the server. The browser game uses the same local `wordfreq` word list as the desktop game and does not require an internet connection after installing the requirements.

## Connect Four (browser)

Run the browser version from this folder with:

```bash
python connect_four_browser.py
```

The script starts a local web server and opens the game in Google Chrome. Keep the terminal window open while playing; press **Ctrl+C** there to stop the server. Pyodide is loaded from its CDN, so an internet connection is required.

## Minesweeper

Run the Minesweeper game with:

```bash
python minesweeper.py
```

Left-click a square to reveal it and right-click to place or remove a flag. The first click is always safe. Choose a difficulty and use **New Game** to start a fresh board. The game uses Tkinter and the Python standard library only.

## Checkers

Run the human-vs-computer checkers game with:

```bash
python checkers.py
```

It uses Tkinter from Python's standard library. Red moves first; captures are mandatory, and a piece must continue a capture sequence when another jump is available.

### Checkers in Chrome

Run the browser version from this folder with:

```bash
python checkers_browser.py
```

The script starts a local web server and opens Checkers in Google Chrome. Keep the terminal window open while playing; press **Ctrl+C** there to stop the server. The browser version uses the same Python rules and computer opponent as the desktop game, loaded by Pyodide, so an internet connection is required.

## Chess

Install the chess-rules library and start the human-vs-computer chess game with:

```bash
python -m pip install -r chess-requirements.txt
python chess_game.py
```

The game uses Tkinter for its resizable board and `python-chess` for legal moves, check, castling, en passant, promotion, checkmate, and draws. White moves first.

### Chess in Chrome

Run the browser version from this folder with:

```bash
python chess_browser.py
```

The script starts a local web server and opens Chess in Google Chrome. Keep the terminal window open while playing; press **Ctrl+C** there to stop the server. The browser version uses the same Python chess rules and computer opponent as the desktop game, loaded by Pyodide. It downloads and verifies the `python-chess` source at startup, so an internet connection is required. Choose a promotion piece with the selector below the board.

## Sudoku

Run the Sudoku game with:

```bash
python sudoku.py
```

It uses Tkinter and the Python standard library only. Choose a difficulty, enter numbers with the keyboard or number pad, toggle pencil notes, and use **Check** to highlight incorrect entries.

### Sudoku in Chrome

Run the browser version from this folder with:

```bash
python sudoku_browser.py
```

The script starts a local web server and opens Sudoku in Google Chrome. Keep the terminal window open while playing; press **Ctrl+C** there to stop the server. The browser version uses the same Python puzzle generator and solver as `sudoku.py`, loaded by Pyodide, so an internet connection is required.

## Mastermind

Run the Mastermind code-breaking game with:

```bash
python mastermind.py
```

Choose four colored pegs (repeats are allowed) and submit your guess. Feedback shows how many pegs have the right color and position and how many have the right color in another position. The game uses Tkinter and the Python standard library only.

### Mastermind in Chrome

Run the browser version from this folder with:

```bash
python mastermind_browser.py
```

The script starts a local web server and opens Mastermind in Google Chrome. Keep the terminal window open while playing; press **Ctrl+C** there to stop the server. The browser version uses the same Python code-breaking rules as the desktop game and does not require an internet connection.

## Mens erger je niet (browser)

Start the browser game from this folder with:

```bash
python mens_erger_je_niet_browser.py
```

The script starts a local web server and opens the game in Google Chrome. Keep the terminal window open while playing; press **Ctrl+C** there to stop the server. You play the red pawns against three computer opponents.

### How to play

Each player has four pawns and tries to move them around the board and into their colored home lane. Roll a **6** to bring a pawn out of its base onto its start space. On your turn, roll and click one of the highlighted pawns to move it clockwise by the number shown; moving with a six earns another roll. You can pass other pawns, but you cannot land on one of your own pawns. Land exactly on an opponent's pawn to send it back to its base; the track has no protected spaces.

After a pawn completes a lap, it enters its colored home lane. You must roll the exact number needed to reach home, and the first player to get all four pawns home wins. These are the rules used in this version; house rules can vary.

## Ganzenbord (browser)

Start het Nederlandse Ganzenbord in Chrome vanuit deze map:

```bash
python ganzenbord_browser.py
```

Kies twee, drie of vier spelers; jij speelt tegen de andere pionnen. Laat het terminalvenster open tijdens het spelen en druk daar op **Ctrl+C** om de lokale spelserver te stoppen. De spelregels verschijnen vanzelf bij bijzondere vakjes; open **De spelregels, voor wie ze nog eens wil lezen** voor een kort overzicht.

Deze versie gebruikt de bekende 63 vakjes: op een gans vlieg je met dezelfde worp verder; de brug op 6 brengt je naar 12; in de herberg op 19 rust je twee beurten; in de put op 31 wacht je tot iemand je plek overneemt; het doolhof op 42 brengt je terug naar 30; in de gevangenis op 52 wacht je tot iemand je plek overneemt; en de dood op 58 stuurt je terug naar start. Je moet met een exacte worp op 63 eindigen; bij te hoog gooien tel je vanaf 63 terug. Bij de eerste worp van het spel brengt 6+3 je rechtstreeks naar 26 en 5+4 rechtstreeks naar 53; daarna is de volgende speler aan de beurt. Historische uitgaven en huisregels verschillen soms; deze gekozen regels worden ook in het spel uitgelegd.

Het bord is opnieuw vormgegeven als een vierkante, handgetekende spiraal met kleurrijke prentjes, een Hollands landschap en een eigen tekening voor elk bijzonder vak. Voor de beeldtaal zijn onder meer de [Spear's ganzenbord uit de collectie van Museum Rotterdam (1933)](https://www.europeana.eu/item/2021609/resource_document_museum_rotterdam_http_museumrotterdam_nl_collectie_item_30085_A_I) en een [Spear-vouwbord uit de collectie van Museon](https://www.europeana.eu/item/2021657/resource_document_museon_95364) bekeken. Er is geen Nederlandse uitgave uit de jaren 80 of 90 met verifieerbare datering gevonden; de illustraties zijn dus geïnspireerd op historische voorbeelden, niet bedoeld als exacte reproductie van één editie.
