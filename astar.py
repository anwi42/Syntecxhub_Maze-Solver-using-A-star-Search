import heapq
import math
import time

def heuristic(a, b, mode="manhattan"):
    if mode == "manhattan":
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    else:
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

def astar(maze, mode="manhattan"):
    start = maze.start
    goal  = maze.goal

    start_time = time.time()

    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score   = {start: 0}
    visited   = []
    fgh_scores = {}  # stores f g h for every explored cell

    while open_set:
        _, current = heapq.heappop(open_set)

        if current in visited:
            continue
        visited.append(current)

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()

            elapsed = round((time.time() - start_time) * 1000, 2)
            return path, visited, elapsed, fgh_scores

        for neighbor in maze.neighbors(*current):
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor]   = tentative_g
                h = heuristic(neighbor, goal, mode)
                f = tentative_g + h

                # store scores
                fgh_scores[neighbor] = {
                    "g": tentative_g,
                    "h": round(h, 2),
                    "f": round(f, 2)
                }

                heapq.heappush(open_set, (f, neighbor))

    elapsed = round((time.time() - start_time) * 1000, 2)
    return None, visited, elapsed, fgh_scores