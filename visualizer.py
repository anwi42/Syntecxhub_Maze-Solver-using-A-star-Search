import pygame
import sys
import ctypes

BG          = (246, 248, 250)
OPEN        = (240, 242, 245)
WALL        = (176, 184, 196)
EXPLORED    = (181, 212, 244)
PATH        = (9,   105, 218)
START       = (26,  127, 55)
GOAL        = (207, 34,  46)
SIDEBAR_BG  = (246, 248, 250)
WHITE       = (255, 255, 255)
BORDER      = (208, 215, 222)
TEXT_DARK   = (28,  33,  40)
TEXT_MUTED  = (87,  96,  106)
BLUE        = (9,   105, 218)
BLUE_LIGHT  = (234, 241, 251)
BLUE_BORDER = (181, 212, 244)

OPEN_SIZE = 18
WALL_SIZE = 5
SIDEBAR   = 260


class Button:
    def __init__(self, x, y, w, h, text, style="normal"):
        self.rect   = pygame.Rect(x, y, w, h)
        self.text   = text
        self.style  = style
        self.active = False

    def draw(self, screen, font):
        if self.style == "action":
            bg, border, tc = BLUE, (5, 80, 174), WHITE
        elif self.style == "outline":
            bg, border, tc = WHITE, BLUE, BLUE
        else:
            if self.active:
                bg, border, tc = BLUE, BLUE, WHITE
            else:
                bg, border, tc = WHITE, BORDER, TEXT_DARK

        pygame.draw.rect(screen, bg,     self.rect)
        pygame.draw.rect(screen, border, self.rect, 1)
        txt = font.render(self.text, True, tc)
        tx  = self.rect.x + (self.rect.w - txt.get_width())  // 2
        ty  = self.rect.y + (self.rect.h - txt.get_height()) // 2
        screen.blit(txt, (tx, ty))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class Visualizer:
    def __init__(self, maze):
        self.maze = maze
        self.rows = maze.rows
        self.cols = maze.cols

        pygame.init()

        info = pygame.display.Info()
        self.screen_w = info.current_w
        self.screen_h = info.current_h

        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 6
        )
        self.screen = pygame.display.set_mode(
            (self.screen_w, self.screen_h - 70), pygame.RESIZABLE
        )
        pygame.display.set_caption("A* Maze Solver")

        maze_area_w = self.screen_w - SIDEBAR
        maze_area_h = self.screen_h

        open_cols = (self.cols + 1) // 2
        wall_cols = self.cols - open_cols
        open_rows = (self.rows + 1) // 2
        wall_rows = self.rows - open_rows

        max_open_w = (maze_area_w - wall_cols * WALL_SIZE) // open_cols
        max_open_h = (maze_area_h - wall_rows * WALL_SIZE) // open_rows
        self.open_sz = max(10, min(max_open_w, max_open_h, 28))

        self.col_sizes = [
            WALL_SIZE if c % 2 == 0 else self.open_sz
            for c in range(self.cols)
        ]
        self.row_sizes = [
            WALL_SIZE if r % 2 == 0 else self.open_sz
            for r in range(self.rows)
        ]

        self.maze_w = sum(self.col_sizes)
        self.maze_h = sum(self.row_sizes)

        self.maze_offset_y = (self.screen_h - self.maze_h) // 2 - 50
        self.maze_offset_x = ((self.screen_w - SIDEBAR) - self.maze_w) // 2

        self.font       = pygame.font.SysFont("Segoe UI", 14)
        self.font_bold  = pygame.font.SysFont("Segoe UI", 15, bold=True)
        self.font_title = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.font_label = pygame.font.SysFont("Segoe UI", 11, bold=True)
        self.font_sm    = pygame.font.SysFont("Segoe UI", 13)
        self.font_tip   = pygame.font.SysFont("Segoe UI", 12)

        self.heuristic     = "manhattan"
        self.path          = []
        self.visited       = []
        self.stats         = {}
        self.pending_stats = {}
        self.fgh_scores    = {}
        self.solved        = False
        self.no_path       = False
        self.anim_index    = 0
        self.animating     = False
        self.speed         = 4

        self._build_buttons()

    def _build_buttons(self):
        sx = self.screen_w - SIDEBAR + 14
        bw = SIDEBAR - 28

        self.btn_manhattan = Button(sx, 100, bw, 34, "Manhattan")
        self.btn_euclidean = Button(sx, 140, bw, 34, "Euclidean")
        self.btn_manhattan.active = True

        self.btn_slow   = Button(sx, 240, bw, 30, "Slow   — 1 cell/frame")
        self.btn_medium = Button(sx, 276, bw, 30, "Medium — 4 cells/frame")
        self.btn_fast   = Button(sx, 312, bw, 30, "Fast   — 8 cells/frame")
        self.btn_medium.active = True

        self.btn_solve   = Button(sx, 365 , bw, 40, "Solve",    "action")
        self.btn_newmaze = Button(sx,412 , bw, 40, "New Maze", "outline")

    def _get_pixel(self, r, c):
        x = self.maze_offset_x + sum(self.col_sizes[:c])
        y = self.maze_offset_y + sum(self.row_sizes[:r])
        w = self.col_sizes[c]
        h = self.row_sizes[r]
        return x, y, w, h

    def _get_cell_from_mouse(self, mx, my):
        cx = mx - self.maze_offset_x
        cy = my - self.maze_offset_y

        if cx < 0 or cy < 0:
            return None

        acc = 0
        col = None
        for i, s in enumerate(self.col_sizes):
            if acc <= cx < acc + s:
                col = i
                break
            acc += s

        acc = 0
        row = None
        for i, s in enumerate(self.row_sizes):
            if acc <= cy < acc + s:
                row = i
                break
            acc += s

        if row is None or col is None:
            return None
        return (row, col)

    def draw_maze(self):
        for r in range(self.rows):
            for c in range(self.cols):
                x, y, w, h = self._get_pixel(r, c)
                if (r, c) == self.maze.start:
                    color = START
                elif (r, c) == self.maze.goal:
                    color = GOAL
                elif self.maze.grid[r][c] == 1:
                    color = WALL
                else:
                    color = OPEN
                pygame.draw.rect(self.screen, color, (x, y, w, h))

    def draw_visited(self, count):
        for i in range(min(count, len(self.visited))):
            r, c = self.visited[i]
            if (r, c) not in (self.maze.start, self.maze.goal):
                x, y, w, h = self._get_pixel(r, c)
                pygame.draw.rect(self.screen, EXPLORED, (x, y, w, h))

    def draw_path(self):
        for r, c in self.path:
            if (r, c) not in (self.maze.start, self.maze.goal):
                x, y, w, h = self._get_pixel(r, c)
                pygame.draw.rect(self.screen, PATH, (x, y, w, h))

    def draw_legend(self):
        # fixed at bottom left of screen
        lx = 10
        ly = self.screen_h - 290
        lw = 160
        lh = 195

        # background box
        pygame.draw.rect(self.screen, WHITE,  (lx, ly, lw, lh))
        pygame.draw.rect(self.screen, BORDER, (lx, ly, lw, lh), 1)

        y = ly + 10
        t = self.font_label.render("LEGEND", True, TEXT_MUTED)
        self.screen.blit(t, (lx + 10, y)); y += 20

        for color, label in [
            (START,    "Start"),
            (GOAL,     "Goal"),
            (WALL,     "Wall"),
            (OPEN,     "Open cell"),
            (EXPLORED, "Explored"),
            (PATH,     "Shortest path"),
        ]:
            pygame.draw.rect(self.screen, color,  (lx + 10, y, 14, 14))
            pygame.draw.rect(self.screen, BORDER, (lx + 10, y, 14, 14), 1)
            t = self.font_sm.render(label, True, TEXT_MUTED)
            self.screen.blit(t, (lx + 30, y))
            y += 26

    def draw_tooltip(self, mx, my):
        if not self.solved or not self.fgh_scores:
            return

        cell = self._get_cell_from_mouse(mx, my)
        if cell is None:
            return

        if cell not in self.fgh_scores:
            return

        if cell not in self.visited:
            return

        if self.maze.grid[cell[0]][cell[1]] == 1:
            return

        r, c = cell
        x, y, w, h = self._get_pixel(r, c)
        pygame.draw.rect(self.screen, (0, 0, 0), (x-2, y-2, w+4, h+4))
        pygame.draw.rect(self.screen, BLUE, (x, y, w, h), 3)

        scores = self.fgh_scores[cell]
        g = scores["g"]
        h = scores["h"]
        f = scores["f"]

        lines = [
            f"Cell ({cell[0]}, {cell[1]})",
            f"g = {g}",
            f"h = {h}",
            f"f = {f}",
        ]

        pad    = 8
        line_h = 18
        box_w  = 110
        box_h  = len(lines) * line_h + pad * 2

        tx = mx + 14
        ty = my + 14
        if tx + box_w > self.screen_w - SIDEBAR:
            tx = mx - box_w - 6
        if ty + box_h > self.screen_h - 70:
            ty = my - box_h - 6

        pygame.draw.rect(self.screen, WHITE, (tx, ty, box_w, box_h))
        pygame.draw.rect(self.screen, BLUE,  (tx, ty, box_w, box_h), 1)

        for i, line in enumerate(lines):
            color = BLUE if i == 0 else TEXT_DARK
            font  = self.font_bold if i == 0 else self.font_tip
            t = font.render(line, True, color)
            self.screen.blit(t, (tx + pad, ty + pad + i * line_h))

    def _show_loading(self):
        self.screen.fill((255, 255, 255))

        font_big  = pygame.font.SysFont("Segoe UI", 48, bold=True)
        font_sub  = pygame.font.SysFont("Segoe UI", 20)
        font_hint = pygame.font.SysFont("Segoe UI", 15)

        cx = self.screen_w // 2
        cy = self.screen_h // 2

        t = font_big.render("A* Maze Solver", True, (9, 105, 218))
        self.screen.blit(t, (cx - t.get_width() // 2, cy - 80))

        t = font_sub.render("Pathfinding Visualizer", True, (87, 96, 106))
        self.screen.blit(t, (cx - t.get_width() // 2, cy - 20))

        pygame.draw.line(self.screen, (208, 215, 222),
                         (cx - 120, cy + 20), (cx + 120, cy + 20), 1)

        t = font_hint.render("Setting up maze...", True, (181, 212, 244))
        self.screen.blit(t, (cx - t.get_width() // 2, cy + 36))

        t = font_hint.render("Press ESC anytime to exit", True, (208, 215, 222))
        self.screen.blit(t, (cx - t.get_width() // 2, cy + 64))

        pygame.display.flip()
        pygame.time.wait(1500)

    def draw_sidebar(self):
        sx = self.screen_w - SIDEBAR
        pygame.draw.rect(self.screen, SIDEBAR_BG, (sx, 0, SIDEBAR, self.screen_h))
        pygame.draw.line(self.screen, BORDER, (sx, 0), (sx, self.screen_h), 1)

        x  = sx + 14
        sh = self.screen_h

        t = self.font_title.render("A* Maze Solver", True, TEXT_DARK)
        self.screen.blit(t, (x, 22))
        t = self.font_sm.render("Pathfinding visualizer", True, TEXT_MUTED)
        self.screen.blit(t, (x, 48))
        pygame.draw.line(self.screen, BORDER, (sx, 72), (sx + SIDEBAR, 72), 1)

        t = self.font_label.render("HEURISTIC", True, TEXT_MUTED)
        self.screen.blit(t, (x, 82))
        self.btn_manhattan.draw(self.screen, self.font)
        self.btn_euclidean.draw(self.screen, self.font)

        pygame.draw.line(self.screen, BORDER, (sx, 188), (sx + SIDEBAR, 188), 1)

        t = self.font_label.render("ANIMATION SPEED", True, TEXT_MUTED)
        self.screen.blit(t, (x, 200))
        self.btn_slow.draw(self.screen, self.font_sm)
        self.btn_medium.draw(self.screen, self.font_sm)
        self.btn_fast.draw(self.screen, self.font_sm)

        pygame.draw.line(self.screen, BORDER, (sx, 352), (sx + SIDEBAR, 352), 1)

        self.btn_solve.draw(self.screen, self.font_bold)
        self.btn_newmaze.draw(self.screen, self.font_bold)

        pygame.draw.line(self.screen, BORDER, (sx, 462), (sx + SIDEBAR, 462), 1)

        # results fixed position
        y = 474
        t = self.font_label.render("RESULTS", True, TEXT_MUTED)
        self.screen.blit(t, (x, y)); y += 20

        if self.no_path:
            t = self.font_bold.render("No path found!", True, GOAL)
            self.screen.blit(t, (x, y)); y += 26

        elif self.stats:
            box_h = len(self.stats) * 24 + 16
            pygame.draw.rect(self.screen, BLUE_LIGHT,  (sx+10, y, SIDEBAR-20, box_h))
            pygame.draw.rect(self.screen, BLUE_BORDER, (sx+10, y, SIDEBAR-20, box_h), 1)
            y += 10
            for key, val in self.stats.items():
                k = self.font_sm.render(str(key),  True, TEXT_MUTED)
                v = self.font_bold.render(str(val), True, BLUE)
                self.screen.blit(k, (x + 6, y))
                self.screen.blit(v, (sx + SIDEBAR - 16 - v.get_width(), y))
                y += 24
            y += 10
        else:
            t = self.font_sm.render("Click Solve to see results", True, TEXT_MUTED)
            self.screen.blit(t, (x, y)); y += 24

        # hover hint
        if self.solved:
            t = self.font_tip.render("Hover cells to see f g h", True, TEXT_MUTED)
            self.screen.blit(t, (x, sh - 30))

    def handle_click(self, pos, maze_module, astar_fn):
        if pos[0] < self.screen_w - SIDEBAR:
            return

        if self.btn_manhattan.is_clicked(pos):
            self.heuristic = "manhattan"
            self.btn_manhattan.active = True
            self.btn_euclidean.active = False

        elif self.btn_euclidean.is_clicked(pos):
            self.heuristic = "euclidean"
            self.btn_euclidean.active = True
            self.btn_manhattan.active = False

        elif self.btn_slow.is_clicked(pos):
            self.speed = 1
            self.btn_slow.active   = True
            self.btn_medium.active = False
            self.btn_fast.active   = False

        elif self.btn_medium.is_clicked(pos):
            self.speed = 4
            self.btn_slow.active   = False
            self.btn_medium.active = True
            self.btn_fast.active   = False

        elif self.btn_fast.is_clicked(pos):
            self.speed = 8
            self.btn_slow.active   = False
            self.btn_medium.active = False
            self.btn_fast.active   = True

        elif self.btn_solve.is_clicked(pos):
            self.path          = []
            self.visited       = []
            self.stats         = {}
            self.solved        = False
            self.no_path       = False
            self.anim_index    = 0
            self.pending_stats = {}
            self.fgh_scores    = {}
            path, visited, elapsed, fgh_scores = astar_fn(self.maze, self.heuristic)
            self.visited    = visited
            self.fgh_scores = fgh_scores
            if path:
                self.path          = path
                self.pending_stats = {
                    "Heuristic"     : self.heuristic.capitalize(),
                    "Nodes explored": len(visited),
                    "Path length"   : len(path),
                    "Time (ms)"     : elapsed
                }
            else:
                self.no_path       = True
                self.pending_stats = {
                    "Nodes explored": len(visited),
                    "Time (ms)"     : elapsed
                }
            self.animating = True

        elif self.btn_newmaze.is_clicked(pos):
            self.maze          = maze_module.Maze(self.rows, self.cols)
            self.path          = []
            self.visited       = []
            self.solved        = False
            self.no_path       = False
            self.anim_index    = 0
            self.stats         = {}
            self.pending_stats = {}
            self.fgh_scores    = {}
            self.animating     = False

    def run(self, maze_module, astar_fn):
        self._show_loading()

        running = True
        while running:
            mx, my = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_click(event.pos, maze_module, astar_fn)

            self.screen.fill(BG)
            self.draw_maze()

            if self.animating:
                self.anim_index += self.speed
                self.draw_visited(self.anim_index)
                if self.anim_index >= len(self.visited):
                    self.animating = False
                    self.solved    = True
                    self.stats     = self.pending_stats
            elif self.solved:
                self.draw_visited(len(self.visited))
                self.draw_path()

            sr, sc = self.maze.start
            gr, gc = self.maze.goal
            sx, sy, sw, sh = self._get_pixel(sr, sc)
            gx, gy, gw, gh = self._get_pixel(gr, gc)
            pygame.draw.rect(self.screen, START, (sx, sy, sw, sh))
            pygame.draw.rect(self.screen, GOAL,  (gx, gy, gw, gh))

            self.draw_sidebar()
            self.draw_legend()
            self.draw_tooltip(mx, my)

            pygame.display.flip()
            pygame.time.Clock().tick(60)