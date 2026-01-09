import random
from collections import deque


def generate_minesweeper_field(num_mines):
    height, width = 6, 10
    field: list = [[0 for _ in range(width)] for _ in range(height)]
    mines_placed = 0
    while mines_placed < num_mines:
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        if field[y][x] == "x" or (y, x) in ((0, 0), (0, 1), (0, 2)):
            continue
        field[y][x] = "x"
        mines_placed += 1
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if isinstance(field[ny][nx], int):
                        field[ny][nx] += 1
    return field


def pathfind(start, end, forbidden_cages=()):
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    queue = deque([(start, [start])])
    visited = set(forbidden_cages)
    visited.add(start)

    while queue:
        current, path = queue.popleft()
        if current == end:
            return path[1:]

        for dx, dy in directions:
            nx, ny = current[0] + dx, current[1] + dy
            if 0 <= nx < 6 and 0 <= ny < 10 and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))
    return []


class MinesweeperSolver:
    def __init__(self, player_position=(0, 0), move_to_world=(5, 0)):
        self.height = 6
        self.width = 10
        self.player_position = player_position
        self.move_to_world = move_to_world

        self.board = [["?" for _ in range(self.width)] for _ in range(self.height)]
        self.has_fallen = False
        self.safe_to_visit = deque()

    def get_unsafe_cages(self):
        return tuple((i, j) for i in range(self.height)
                     for j in range(self.width) if self.board[i][j] in ("x", "?"))

    def make_move(self) -> tuple[int, int]:
        forbidden_cages = self.get_unsafe_cages()
        path = pathfind(self.player_position, self.move_to_world, forbidden_cages)
        if path:
            print("не упал! путь есть")
            return -1, -1

        self.infer_board_info()
        while self.safe_to_visit:
            move = self.safe_to_visit.popleft()
            if self.board[move[0]][move[1]] == "s":
                return move

        unknown_cages = self.get_accessible_cages(symbols_set="?")
        if unknown_cages:
            move = random.choice(unknown_cages)
            return move
        return -1, -1

    def get_accessible_cages(self, symbols_set=("?", "s")):
        accessible = set()
        visited = set()
        queue = deque([self.player_position])

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            for neighbor in self.get_surroundings(current):
                cell_value = self.board[neighbor[0]][neighbor[1]]
                if str(cell_value) in symbols_set:
                    accessible.add(neighbor)
                elif isinstance(cell_value, int):
                    queue.append(neighbor)
        return sorted(accessible)

    def print_field(self):
        for i in range(self.height):
            for j in range(self.width):
                if (i, j) == self.player_position:
                    print("u", end=" ")
                    continue
                print(self.board[i][j], end=" ")
            print()

    def mark_cage_level(self, cage, danger_level):
        row, col = cage
        print(f"Made move from {self.player_position} to {cage}! Danger: {danger_level}")
        self.print_field()
        self.player_position = cage
        self.board[row][col] = danger_level

        if danger_level == "x":
            print("Я УПАЛ!!")
            self.has_fallen = True
            return

        if danger_level == 0:
            for neighbor in self.get_surroundings(cage):
                if self.board[neighbor[0]][neighbor[1]] == "?":
                    self.board[neighbor[0]][neighbor[1]] = "s"
                    self.safe_to_visit.append(neighbor)

    def infer_board_info(self):
        self.mark_safe_cages()
        for i in range(self.height):
            for j in range(self.width):
                self.check_cage_surroundings((i, j))

    def mark_safe_cages(self):
        for i in range(self.height):
            for j in range(self.width):
                if self.board[i][j] == 0:
                    self.mark_surroundings_as_safe((i, j))

    def mark_surroundings_as_safe(self, cage):
        for neighbor in self.get_surroundings(cage):
            if self.board[neighbor[0]][neighbor[1]] == "?":
                self.board[neighbor[0]][neighbor[1]] = "s"
                self.safe_to_visit.append(neighbor)

    def check_cage_surroundings(self, cage):
        if not isinstance(self.board[cage[0]][cage[1]], int):
            return

        surroundings = self.get_surroundings(cage)
        value = int(self.board[cage[0]][cage[1]])
        unknown = []
        mines = 0

        for neighbor in surroundings:
            cell = self.board[neighbor[0]][neighbor[1]]
            if cell == "x":
                mines += 1
            elif cell == "?":
                unknown.append(neighbor)

        if mines == value and unknown:
            for cell in unknown:
                self.board[cell[0]][cell[1]] = "s"
                self.safe_to_visit.append(cell)
        elif len(unknown) == value - mines and unknown:
            for cell in unknown:
                self.board[cell[0]][cell[1]] = "x"

    def get_surroundings(self, cage):
        row, col = cage
        return [(r, c) for r in range(max(0, row - 1), min(self.height, row + 2))
                for c in range(max(0, col - 1), min(self.width, col + 2))
                if (r, c) != cage]

#
# while not solver.has_fallen:
#     if solver.make_move():
#         break

