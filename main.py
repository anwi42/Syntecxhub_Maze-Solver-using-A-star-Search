import maze as maze_module
from astar import astar
from visualizer import Visualizer

ROWS = 31
COLS = 31

m = maze_module.Maze(ROWS, COLS)
vis = Visualizer(m)
vis.run(maze_module, astar)