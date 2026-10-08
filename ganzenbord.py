import random


MAX_SQUARE = 63
GOOSE_SQUARES = frozenset((5, 9, 14, 18, 23, 27, 32, 36, 41, 45, 50, 54, 59))
BRIDGE_SQUARE = 6
BRIDGE_DESTINATION = 12
INN_SQUARE = 19
WELL_SQUARE = 31
MAZE_SQUARE = 42
MAZE_DESTINATION = 30
PRISON_SQUARE = 52
DEATH_SQUARE = 58
DEATH_DESTINATION = 1

PLAYER_STYLES = (
    {"name": "Rood", "color": "#b7443b", "shape": "●"},
    {"name": "Blauw", "color": "#426d91", "shape": "◆"},
    {"name": "Geel", "color": "#c3932f", "shape": "▲"},
    {"name": "Groen", "color": "#587a58", "shape": "■"},
)


def _spiral_coordinates():
    """Number 63 contiguous spaces in an inward, clockwise square spiral."""
    coordinates = []
    coordinates.extend((8, column) for column in range(9))
    coordinates.extend((row, 8) for row in range(7, -1, -1))
    coordinates.extend((0, column) for column in range(7, -1, -1))
    coordinates.extend((row, 0) for row in range(1, 8))
    coordinates.extend((7, column) for column in range(1, 8))
    coordinates.extend((row, 7) for row in range(6, 0, -1))
    coordinates.extend((1, column) for column in range(6, 0, -1))
    coordinates.extend((row, 1) for row in range(2, 7))
    coordinates.extend((6, column) for column in range(2, 7))
    coordinates.extend(((5, 6), (4, 6)))
    if len(coordinates) != MAX_SQUARE or len(set(coordinates)) != MAX_SQUARE:
        raise RuntimeError("The Ganzenbord spiral layout must contain 63 unique spaces.")
    if any(
        abs(first[0] - second[0]) + abs(first[1] - second[1]) != 1
        for first, second in zip(coordinates, coordinates[1:])
    ):
        raise RuntimeError("Every Ganzenbord space must touch the next one.")
    return tuple(coordinates)


BOARD_COORDINATES = _spiral_coordinates()


def board_layout():
    return {
        "coordinates": BOARD_COORDINATES,
        "goose_squares": sorted(GOOSE_SQUARES),
        "special_squares": {
            "bridge": BRIDGE_SQUARE,
            "inn": INN_SQUARE,
            "well": WELL_SQUARE,
            "maze": MAZE_SQUARE,
            "prison": PRISON_SQUARE,
            "death": DEATH_SQUARE,
        },
    }


class GanzenbordGame:
    """Traditional Dutch Goose Game rules with two dice."""

    def __init__(self, player_count=2):
        self.new_game(player_count)

    def new_game(self, player_count=None):
        if player_count is None:
            player_count = len(self.players)
        if (
            isinstance(player_count, bool)
            or not isinstance(player_count, int)
            or player_count not in (2, 3, 4)
        ):
            raise ValueError("Kies twee, drie of vier spelers.")

        self.player_count = player_count
        self.players = [
            {
                "name": "Jij" if index == 0 else f"Speler {index + 1}",
                "color": PLAYER_STYLES[index]["color"],
                "shape": PLAYER_STYLES[index]["shape"],
                "position": 0,
                "skip_turns": 0,
                "blocked_on_well": False,
                "blocked_in_prison": False,
            }
            for index in range(player_count)
        ]
        self.current_player = 0
        self.dice = None
        self.phase = "awaiting_roll"
        self.finished = False
        self.winner = None
        self.turn_count = 0
        self.special_note = "Gooi de dobbelstenen om te beginnen."
        self.last_roll = None
        self.turn_effect = None
        self._pending_path = []

    def get_state(self):
        return {
            "board": board_layout(),
            "players": [dict(player) for player in self.players],
            "player_count": self.player_count,
            "current_player": self.current_player,
            "dice": list(self.dice) if self.dice else None,
            "phase": self.phase,
            "finished": self.finished,
            "winner": self.winner,
            "turn_count": self.turn_count,
            "special_note": self.special_note,
            "last_roll": dict(self.last_roll) if self.last_roll else None,
            "turn_effect": self.turn_effect,
        }

    def roll_dice(self):
        if self.finished or self.phase != "awaiting_roll":
            raise ValueError("Wacht tot je weer mag gooien.")

        player_index = self.current_player
        player = self.players[player_index]
        if player["blocked_on_well"] or player["blocked_in_prison"]:
            raise ValueError("Deze speler wacht op bevrijding.")
        if player["skip_turns"]:
            raise ValueError("Je beurt bij de Herberg wordt automatisch overgeslagen.")

        first_roll = self.turn_count == 0
        die_one, die_two = random.randint(1, 6), random.randint(1, 6)
        total = die_one + die_two
        player["position"] = self._advance(player_index, player["position"], total)
        self.turn_count += 1
        self.dice = (die_one, die_two)
        self.last_roll = {
            "player": player_index,
            "dice": [die_one, die_two],
            "total": total,
        }

        note = f"{player['name']} gooit {die_one} en {die_two}."
        if first_roll and {die_one, die_two} == {3, 6}:
            player["position"] = 26
            note += (
                " De eerste worp 6+3 brengt je volgens de oude regel "
                "rechtstreeks naar vak 26."
            )
        elif first_roll and {die_one, die_two} == {4, 5}:
            player["position"] = 53
            note += (
                " De eerste worp 5+4 brengt je volgens de oude regel "
                "rechtstreeks naar vak 53."
            )

        self.phase = "animating"
        self.turn_effect = {
            "player": player_index,
            "dice": [die_one, die_two],
            "path": [],
            "message": note,
        }
        self.special_note = note
        self._resolve_landing(player_index, total, first_roll)
        return self.get_state()

    def finish_animation(self):
        if self.phase != "animating" or self.finished:
            return self.get_state()
        self.turn_effect = None
        if self.finished:
            return self.get_state()
        self.current_player = (self.last_roll["player"] + 1) % self.player_count
        self.phase = "awaiting_roll"
        skipped = []
        for _ in range(self.player_count):
            player = self.players[self.current_player]
            if not (player["blocked_on_well"] or player["blocked_in_prison"]):
                break
            skipped.append(player["name"])
            self.current_player = (self.current_player + 1) % self.player_count
        else:
            released = next(
                (
                    player
                    for player in self.players
                    if player["blocked_on_well"]
                ),
                None,
            )
            if released is not None:
                released["blocked_on_well"] = False
                released["position"] = 0
                self.current_player = self.players.index(released)
                self.special_note = (
                    f"Alle spelers stonden vast. {released['name']} is uit de Put "
                    "bevrijd en keert terug naar start."
                )
                return self.get_state()
        if skipped:
            self.special_note += (
                f" {', '.join(skipped)} wacht vast in de Put of Gevangenis; "
                f"{self.players[self.current_player]['name']} is nu aan de beurt."
            )
        elif self.current_player == 0:
            self.special_note = "Jij bent aan de beurt. Gooi de dobbelstenen."
        else:
            self.special_note = (
                f"{self.players[self.current_player]['name']} is aan de beurt."
            )
        return self.get_state()

    def skip_turn(self):
        if self.finished or self.phase != "awaiting_roll":
            raise ValueError("Deze beurt kan nu niet worden overgeslagen.")
        player = self.players[self.current_player]
        if player["skip_turns"] <= 0:
            raise ValueError("Deze speler hoeft geen beurt over te slaan.")
        player["skip_turns"] -= 1
        note = (
            f"{player['name']} slaat een beurt over in de Herberg. "
            f"{'Nog één beurt wachten.' if player['skip_turns'] else 'De rust is voorbij.'}"
        )
        self.current_player = (self.current_player + 1) % self.player_count
        skipped = []
        for _ in range(self.player_count):
            waiting = self.players[self.current_player]
            if not (waiting["blocked_on_well"] or waiting["blocked_in_prison"]):
                break
            skipped.append(waiting["name"])
            self.current_player = (self.current_player + 1) % self.player_count
        if skipped:
            note += (
                f" {', '.join(skipped)} wachten vast in de Put of Gevangenis. "
                f"{self.players[self.current_player]['name']} is nu aan de beurt."
            )
        self.special_note = note
        return self.get_state()

    def computer_turn(self):
        if (
            self.finished
            or self.phase != "awaiting_roll"
            or self.current_player == 0
        ):
            raise ValueError("Er is nu geen computerbeurt.")
        return self.roll_dice()

    def _advance(self, player_index, position, total):
        overshoot = position + total - MAX_SQUARE
        destination = MAX_SQUARE - overshoot if overshoot > 0 else position + total
        if position == 0:
            path = list(range(1, total + 1))
        elif overshoot > 0:
            path = list(range(position + 1, MAX_SQUARE + 1))
            path.extend(range(MAX_SQUARE - 1, destination - 1, -1))
        else:
            path = list(range(position + 1, destination + 1))
        self._pending_path = path
        return destination

    def _resolve_landing(self, player_index, total, first_roll):
        player = self.players[player_index]
        note = self.special_note
        path = list(getattr(self, "_pending_path", []))
        self._pending_path = []

        if first_roll and player["position"] in (26, 53):
            self.turn_effect["path"] = [player["position"]]
            self.turn_effect["message"] = note
            self.special_note = note
            return

        position = player["position"]
        if position in GOOSE_SQUARES:
            goose_path = []
            while position in GOOSE_SQUARES and position < MAX_SQUARE:
                next_position = position + total
                if next_position > MAX_SQUARE:
                    next_position = MAX_SQUARE - (next_position - MAX_SQUARE)
                if next_position == position:
                    break
                goose_path.append(next_position)
                position = next_position
            player["position"] = position
            path.extend(goose_path)
            note += (
                f" Gans! Je gaat met dezelfde worp door naar vak {position}. "
                "Opnieuw een gans? Dan vlieg je verder."
            )

        if player["position"] == BRIDGE_SQUARE:
            player["position"] = BRIDGE_DESTINATION
            path.append(BRIDGE_DESTINATION)
            note += " De Brug brengt je van vak 6 naar vak 12."
        elif player["position"] == INN_SQUARE:
            player["skip_turns"] = 2
            note += " De Herberg op vak 19: je slaapt hier twee beurten."
        elif player["position"] == WELL_SQUARE:
            if self._release_waiting_player(player_index, "blocked_on_well"):
                note += " Je neemt de plek in van een speler die al in de Put zat."
            player["blocked_on_well"] = True
            note += " De Put op vak 31: wacht tot iemand je plek overneemt."
        elif player["position"] == MAZE_SQUARE:
            player["position"] = MAZE_DESTINATION
            path.append(MAZE_DESTINATION)
            note += " Verdwaald in het Doolhof op vak 42: terug naar vak 30."
        elif player["position"] == PRISON_SQUARE:
            if self._release_waiting_player(player_index, "blocked_in_prison"):
                note += " Je neemt de plek in van een speler die al gevangen zat."
            player["blocked_in_prison"] = True
            note += " De Gevangenis op vak 52: wacht tot iemand je plek overneemt."
        elif player["position"] == DEATH_SQUARE:
            player["position"] = DEATH_DESTINATION
            player["skip_turns"] = 0
            path.append(DEATH_DESTINATION)
            note += " De Dood op vak 58! Terug naar start."

        if player["position"] == MAX_SQUARE:
            self.finished = True
            self.winner = player_index
            self.phase = "finished"
            note += f" Vak 63! {player['name']} heeft gewonnen!"
        self.turn_effect["path"] = path
        self.turn_effect["message"] = note
        self.special_note = note

    def _release_waiting_player(self, arriving_player, flag):
        for player_index, player in enumerate(self.players):
            if player_index != arriving_player and player[flag]:
                player[flag] = False
                player["position"] = 0
                player["skip_turns"] = 0
                return True
        return False

    def _next_player(self):
        self.current_player = (self.current_player + 1) % self.player_count
        self.phase = "awaiting_roll"
        self.dice = None
