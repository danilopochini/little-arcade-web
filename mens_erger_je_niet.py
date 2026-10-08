import random


PLAYER_IDS = ("red", "blue", "yellow", "green")
PLAYER_LABELS = ("You", "Computer 1", "Computer 2", "Computer 3")
PLAYER_STARTS = (38, 51, 12, 25)
PAWNS_PER_PLAYER = 4
FINISH_PROGRESS = 57

TRACK = (
    (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    (5, 6), (4, 6), (3, 6), (2, 6), (1, 6), (0, 6),
    (0, 7), (0, 8), (1, 8), (2, 8), (3, 8), (4, 8), (5, 8),
    (6, 9), (6, 10), (6, 11), (6, 12), (6, 13), (6, 14),
    (7, 14), (8, 14), (8, 13), (8, 12), (8, 11), (8, 10), (8, 9),
    (9, 8), (10, 8), (11, 8), (12, 8), (13, 8), (14, 8),
    (14, 7), (14, 6), (13, 6), (12, 6), (11, 6), (10, 6), (9, 6),
    (8, 5), (8, 4), (8, 3), (8, 2), (8, 1), (8, 0),
    (7, 0), (6, 0),
)

HOME_LANES = (
    ((13, 7), (12, 7), (11, 7), (10, 7), (9, 7)),
    ((7, 1), (7, 2), (7, 3), (7, 4), (7, 5)),
    ((1, 7), (2, 7), (3, 7), (4, 7), (5, 7)),
    ((7, 13), (7, 12), (7, 11), (7, 10), (7, 9)),
)

BASE_SPACES = (
    ((11, 1), (11, 3), (13, 1), (13, 3)),
    ((1, 1), (1, 3), (3, 1), (3, 3)),
    ((1, 11), (1, 13), (3, 11), (3, 13)),
    ((11, 11), (11, 13), (13, 11), (13, 13)),
)

GOAL_SPACES = ((8, 7), (7, 6), (6, 7), (7, 8))


def get_board_layout():
    """Return the static board coordinates for the browser client."""
    return {
        "track": TRACK,
        "starts": PLAYER_STARTS,
        "home_lanes": HOME_LANES,
        "base_spaces": BASE_SPACES,
        "goal_spaces": GOAL_SPACES,
    }


class MensErgerJeNietGame:
    """Rules engine for a four-player, roll-and-move Ludo-style game."""

    def __init__(self):
        self.new_game()

    def new_game(self):
        self.pawns = [[-1] * PAWNS_PER_PLAYER for _ in PLAYER_IDS]
        self.current_player = 0
        self.roll = None
        self.legal_moves = []
        self.phase = "awaiting_roll"
        self.finished = False
        self.winner = None
        self.status = "Your turn. Roll the die."
        self.last_action = None

    def get_state(self):
        """Return a browser-safe snapshot of the current game."""
        return {
            "board": get_board_layout(),
            "players": [
                {
                    "id": player_id,
                    "label": PLAYER_LABELS[index],
                    "pawns": list(self.pawns[index]),
                }
                for index, player_id in enumerate(PLAYER_IDS)
            ],
            "current_player": self.current_player,
            "roll": self.roll,
            "legal_moves": list(self.legal_moves),
            "phase": self.phase,
            "finished": self.finished,
            "winner": self.winner,
            "status": self.status,
            "last_action": self.last_action,
        }

    def roll_die(self):
        """Roll for the active player, skipping the turn if no pawn can move."""
        if self.finished or self.phase != "awaiting_roll":
            raise ValueError("You cannot roll right now.")

        player = self.current_player
        self.roll = random.randint(1, 6)
        die_roll = self.roll
        self.legal_moves = self._legal_pawns(player, self.roll)
        self.last_action = {"type": "roll", "player": player, "roll": die_roll}
        if self.legal_moves:
            self.phase = "awaiting_move"
            self.status = (
                f"{self._player_label(player)} rolled a {self.roll}. "
                "Choose a pawn to move."
            )
        else:
            self._end_turn()
            self.status = (
                f"{self._player_label(player)} rolled a {die_roll}, "
                f"but {'have' if player == 0 else 'has'} no legal move. "
                "The next player's turn begins."
            )
        return self.get_state()

    def move_pawn(self, pawn_index):
        """Move one legal pawn and apply captures, victory, and extra rolls."""
        if self.finished or self.phase != "awaiting_move":
            raise ValueError("Roll the die before moving a pawn.")
        if (
            isinstance(pawn_index, bool)
            or not isinstance(pawn_index, int)
            or pawn_index not in self.legal_moves
        ):
            raise ValueError("Choose one of the highlighted pawns.")

        player = self.current_player
        old_progress = self.pawns[player][pawn_index]
        previous_roll = self.roll
        new_progress = 0 if old_progress == -1 else old_progress + previous_roll
        self.pawns[player][pawn_index] = new_progress
        captured = self._capture_opponents(player, new_progress)
        self.last_action = {
            "type": "move",
            "player": player,
            "pawn": pawn_index,
            "from": old_progress,
            "to": new_progress,
            "roll": previous_roll,
            "captured": captured,
        }

        if all(progress == FINISH_PROGRESS for progress in self.pawns[player]):
            self.finished = True
            self.winner = player
            self.phase = "finished"
            self.legal_moves = []
            ending = "win!" if player == 0 else "wins!"
            self.status = f"{self._player_label(player)} got all four pawns home and {ending}"
            return self.get_state()

        self.roll = None
        self.legal_moves = []
        if previous_roll == 6:
            self.phase = "awaiting_roll"
            self.status = "You rolled a six. Roll again." if player == 0 else (
                f"{self._player_label(player)} rolled a six and gets another turn."
            )
        else:
            self._end_turn()
            self.status = "Your turn." if self.current_player == 0 else (
                f"{self._player_label(self.current_player)}'s turn."
            )

        if captured:
            names = ", ".join(
                self._pawn_label(item["player"], item["pawn"])
                for item in captured
            )
            self.status += f" Captured {names}; sent back to base."
        if new_progress == FINISH_PROGRESS:
            self.status += " A pawn reached home!"
        elif new_progress == 0 and old_progress == -1:
            self.status += f" Pawn {pawn_index + 1} entered the track."
        return self.get_state()

    def computer_turn(self):
        """Play one computer roll and move, returning the updated state."""
        if self.finished or self.phase != "awaiting_roll" or self.current_player == 0:
            raise ValueError("It is not a computer player's turn.")

        state = self.roll_die()
        if self.phase == "awaiting_move":
            pawn_index = self._choose_computer_pawn()
            return self.move_pawn(pawn_index)
        return state

    def _legal_pawns(self, player, die_roll):
        legal = []
        for pawn_index, progress in enumerate(self.pawns[player]):
            if progress == -1:
                destination = 0
                if die_roll != 6 or self._own_pawn_at(player, destination, pawn_index):
                    continue
            else:
                destination = progress + die_roll
                if destination > FINISH_PROGRESS:
                    continue
                if self._own_pawn_at(player, destination, pawn_index):
                    continue
            legal.append(pawn_index)
        return legal

    def _own_pawn_at(self, player, progress, excluded_pawn):
        return any(
            index != excluded_pawn and other_progress == progress
            for index, other_progress in enumerate(self.pawns[player])
        )

    def _capture_opponents(self, player, progress):
        if progress > 51:
            return []

        destination = self._track_index(player, progress)
        captured = []
        for opponent, pawns in enumerate(self.pawns):
            if opponent == player:
                continue
            for pawn_index, opponent_progress in enumerate(pawns):
                if (
                    0 <= opponent_progress <= 51
                    and self._track_index(opponent, opponent_progress) == destination
                ):
                    pawns[pawn_index] = -1
                    captured.append({"player": opponent, "pawn": pawn_index})
        return captured

    def _track_index(self, player, progress):
        return (PLAYER_STARTS[player] + progress) % len(TRACK)

    def _choose_computer_pawn(self):
        player = self.current_player
        best_score = None
        best_pawns = []
        for pawn_index in self.legal_moves:
            old_progress = self.pawns[player][pawn_index]
            new_progress = 0 if old_progress == -1 else old_progress + self.roll
            score = new_progress
            if old_progress == -1:
                score += 35
            if new_progress == FINISH_PROGRESS:
                score += 1000
            elif new_progress >= 52:
                score += 20
            if new_progress <= 51:
                destination = self._track_index(player, new_progress)
                if any(
                    opponent != player
                    and 0 <= progress <= 51
                    and self._track_index(opponent, progress) == destination
                    for opponent, pawns in enumerate(self.pawns)
                    for progress in pawns
                ):
                    score += 100
            if best_score is None or score > best_score:
                best_score = score
                best_pawns = [pawn_index]
            elif score == best_score:
                best_pawns.append(pawn_index)
        return random.choice(best_pawns)

    def _end_turn(self):
        self.current_player = (self.current_player + 1) % len(PLAYER_IDS)
        self.roll = None
        self.legal_moves = []
        self.phase = "awaiting_roll"

    @staticmethod
    def _player_label(player):
        return PLAYER_LABELS[player]

    @staticmethod
    def _pawn_label(player, pawn_index):
        owner = "your" if player == 0 else f"{PLAYER_LABELS[player]}'s"
        return f"{owner} pawn {pawn_index + 1}"
