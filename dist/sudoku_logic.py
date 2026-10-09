import random


SIZE = 9
BOX_SIZE = 3
DIFFICULTIES = {
    "Easy": 40,
    "Medium": 34,
    "Hard": 29,
}


class SudokuPuzzle:
    """Sudoku grid, randomized generation, solving, and uniqueness checks."""

    def __init__(self):
        self.solution = [[0] * SIZE for _ in range(SIZE)]
        self.grid = [[0] * SIZE for _ in range(SIZE)]

    @staticmethod
    def candidates(grid, row, column):
        used = set(grid[row])
        used.update(grid[r][column] for r in range(SIZE))
        box_row = row // BOX_SIZE * BOX_SIZE
        box_column = column // BOX_SIZE * BOX_SIZE
        used.update(
            grid[r][c]
            for r in range(box_row, box_row + BOX_SIZE)
            for c in range(box_column, box_column + BOX_SIZE)
        )
        return [number for number in range(1, SIZE + 1) if number not in used]

    @staticmethod
    def conflicts(grid, row, column, number):
        """Return conflicting cells in the same row, column, or 3x3 box."""
        conflicts = set()
        for index in range(SIZE):
            if grid[row][index] == number and index != column:
                conflicts.add((row, index))
            if grid[index][column] == number and index != row:
                conflicts.add((index, column))

        box_row = row // BOX_SIZE * BOX_SIZE
        box_column = column // BOX_SIZE * BOX_SIZE
        for other_row in range(box_row, box_row + BOX_SIZE):
            for other_column in range(box_column, box_column + BOX_SIZE):
                if (
                    (other_row, other_column) != (row, column)
                    and grid[other_row][other_column] == number
                ):
                    conflicts.add((other_row, other_column))
        return conflicts

    @classmethod
    def solve(cls, grid, limit=1, randomized=False):
        """Return up to limit solutions using MRV-guided backtracking."""
        solutions = []

        def search():
            if len(solutions) >= limit:
                return

            best_cell = None
            best_options = None
            for row in range(SIZE):
                for column in range(SIZE):
                    if grid[row][column] != 0:
                        continue
                    options = cls.candidates(grid, row, column)
                    if not options:
                        return
                    if best_options is None or len(options) < len(best_options):
                        best_cell = (row, column)
                        best_options = options
                        if len(best_options) == 1:
                            break
                if best_options is not None and len(best_options) == 1:
                    break

            if best_cell is None:
                solutions.append([line[:] for line in grid])
                return

            row, column = best_cell
            if randomized:
                random.shuffle(best_options)
            for number in best_options:
                grid[row][column] = number
                search()
                grid[row][column] = 0
                if len(solutions) >= limit:
                    return

        search()
        return solutions

    def generate(self, difficulty):
        self.solution = self.solve(
            [[0] * SIZE for _ in range(SIZE)],
            limit=1,
            randomized=True,
        )[0]
        self.grid = [row[:] for row in self.solution]

        target_clues = DIFFICULTIES[difficulty]
        cells = [(row, column) for row in range(SIZE) for column in range(SIZE)]
        random.shuffle(cells)
        clues = SIZE * SIZE
        for row, column in cells:
            if clues <= target_clues:
                break
            previous = self.grid[row][column]
            self.grid[row][column] = 0
            if len(self.solve([line[:] for line in self.grid], limit=2)) != 1:
                self.grid[row][column] = previous
            else:
                clues -= 1
