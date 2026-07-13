import random

class Maze:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[1 for _ in range(cols)] for _ in range(rows)]
        self.start = (1, 1)
        self.goal = (rows - 2, cols - 2)
        self._generate()

    def _generate(self):
        # recursive backtracking maze generation
        def carve(r, c):
            directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
            random.shuffle(directions)
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 1 <= nr < self.rows - 1 and 1 <= nc < self.cols - 1:
                    if self.grid[nr][nc] == 1:
                        self.grid[r + dr // 2][c + dc // 2] = 0
                        self.grid[nr][nc] = 0
                        carve(nr, nc)

        self.grid[1][1] = 0
        carve(1, 1)
        self.grid[self.goal[0]][self.goal[1]] = 0

    def is_walkable(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols and self.grid[r][c] == 0

    def neighbors(self, r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if self.is_walkable(nr, nc):
                yield (nr, nc)