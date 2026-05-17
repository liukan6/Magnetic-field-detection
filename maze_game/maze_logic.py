import random
from collections import deque
from dataclasses import dataclass, field

import pygame


@dataclass
class MazeDefinition:
    rows: int
    cols: int
    start: tuple[int, int]
    goal: tuple[int, int]
    passages: list[tuple[tuple[int, int], tuple[int, int]]]
    maze_id: str = ""
    name: str = ""
    leaderboard: list[dict] = field(default_factory=list)


def edge_key(a, b):
    return tuple(sorted((a, b)))


def clone_maze(maze):
    return MazeDefinition(
        rows=maze.rows,
        cols=maze.cols,
        start=tuple(maze.start),
        goal=tuple(maze.goal),
        passages=[(tuple(a), tuple(b)) for a, b in maze.passages],
        maze_id=maze.maze_id,
        name=maze.name,
        leaderboard=[dict(item) for item in maze.leaderboard],
    )


def generate_passages(rows, cols):
    passages = set()
    visited = {(0, 0)}
    stack = [(0, 0)]

    while stack:
        row, col = stack[-1]
        neighbors = []

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr = row + dr
            nc = col + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                neighbors.append((nr, nc))

        if not neighbors:
            stack.pop()
            continue

        next_cell = random.choice(neighbors)
        visited.add(next_cell)
        stack.append(next_cell)
        passages.add(edge_key((row, col), next_cell))

    return passages


def is_solvable(rows, cols, passages, start, goal):
    queue = deque([start])
    visited = {start}

    while queue:
        current = queue.popleft()
        if current == goal:
            return True

        row, col = current
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr = row + dr
            nc = col + dc
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue

            neighbor = (nr, nc)
            if neighbor in visited:
                continue

            if edge_key(current, neighbor) not in passages:
                continue

            visited.add(neighbor)
            queue.append(neighbor)

    return False


def create_random_maze(rows, cols, name=""):
    start = (0, 0)
    goal = (rows - 1, cols - 1)

    for _ in range(50):
        passages = generate_passages(rows, cols)
        if is_solvable(rows, cols, passages, start, goal):
            return MazeDefinition(
                rows=rows,
                cols=cols,
                start=start,
                goal=goal,
                passages=sorted(passages),
                maze_id="",
                name=name,
                leaderboard=[],
            )

    raise RuntimeError("Failed to create a solvable maze.")


def serialize_maze(maze):
    return {
        "maze_id": maze.maze_id,
        "name": maze.name,
        "rows": maze.rows,
        "cols": maze.cols,
        "start": list(maze.start),
        "goal": list(maze.goal),
        "passages": [
            [list(cell_a), list(cell_b)]
            for cell_a, cell_b in sorted(maze.passages)
        ],
        "leaderboard": list(maze.leaderboard),
    }


def deserialize_maze(data):
    return MazeDefinition(
        rows=int(data["rows"]),
        cols=int(data["cols"]),
        start=tuple(data["start"]),
        goal=tuple(data["goal"]),
        passages=[
            (tuple(edge[0]), tuple(edge[1]))
            for edge in data["passages"]
        ],
        maze_id=data.get("maze_id", ""),
        name=data.get("name", ""),
        leaderboard=[dict(item) for item in data.get("leaderboard", [])],
    )


def build_wall_rects(maze, viewport):
    walls = []
    half = viewport.wall_thickness // 2
    left = viewport.left
    top = viewport.top
    maze_width = maze.cols * viewport.cell_size
    maze_height = maze.rows * viewport.cell_size
    passage_set = set(maze.passages)

    walls.append(
        pygame.Rect(
            left - half,
            top - half,
            maze_width + viewport.wall_thickness,
            viewport.wall_thickness,
        )
    )
    walls.append(
        pygame.Rect(
            left - half,
            top + maze_height - half,
            maze_width + viewport.wall_thickness,
            viewport.wall_thickness,
        )
    )
    walls.append(
        pygame.Rect(
            left - half,
            top - half,
            viewport.wall_thickness,
            maze_height + viewport.wall_thickness,
        )
    )
    walls.append(
        pygame.Rect(
            left + maze_width - half,
            top - half,
            viewport.wall_thickness,
            maze_height + viewport.wall_thickness,
        )
    )

    for row in range(maze.rows):
        for col in range(maze.cols - 1):
            edge = edge_key((row, col), (row, col + 1))
            if edge in passage_set:
                continue

            x = left + (col + 1) * viewport.cell_size - half
            y = top + row * viewport.cell_size + half
            height = viewport.cell_size - viewport.wall_thickness
            walls.append(pygame.Rect(x, y, viewport.wall_thickness, height))

    for row in range(maze.rows - 1):
        for col in range(maze.cols):
            edge = edge_key((row, col), (row + 1, col))
            if edge in passage_set:
                continue

            x = left + col * viewport.cell_size + half
            y = top + (row + 1) * viewport.cell_size - half
            width = viewport.cell_size - viewport.wall_thickness
            walls.append(pygame.Rect(x, y, width, viewport.wall_thickness))

    return walls
