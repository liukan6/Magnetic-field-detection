import json
import time
import uuid
from pathlib import Path

from maze_logic import clone_maze, deserialize_maze, serialize_maze
from config import MAX_LEADERBOARD_ENTRIES


SAVE_FILE = Path(__file__).with_name("saved_mazes.json")


def load_saved_mazes():
    if not SAVE_FILE.exists():
        return []

    try:
        data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
        return [deserialize_maze(item) for item in data]
    except Exception:
        return []


def normalize_saved_mazes(mazes):
    normalized = []
    changed = False

    for maze in mazes:
        normalized_maze = clone_maze(maze)
        if not normalized_maze.maze_id:
            ensure_maze_identity(normalized_maze)
            changed = True
        if not isinstance(normalized_maze.leaderboard, list):
            normalized_maze.leaderboard = []
            changed = True
        normalized.append(normalized_maze)

    if changed:
        write_saved_mazes(normalized)

    return normalized


def write_saved_mazes(mazes):
    payload = [serialize_maze(maze) for maze in mazes]
    SAVE_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def build_maze_name(maze):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return f"maze_{maze.cols}x{maze.rows}_{timestamp}"


def ensure_maze_identity(maze):
    if not maze.maze_id:
        maze.maze_id = uuid.uuid4().hex
    return maze


def save_maze_copy(mazes, maze, name=None):
    saved_maze = clone_maze(maze)
    ensure_maze_identity(saved_maze)
    saved_maze.name = name or saved_maze.name or build_maze_name(saved_maze)

    replaced = False
    new_mazes = []
    for existing in mazes:
        if existing.maze_id == saved_maze.maze_id:
            new_mazes.append(saved_maze)
            replaced = True
        else:
            new_mazes.append(existing)

    if not replaced:
        new_mazes = [saved_maze] + new_mazes

    write_saved_mazes(new_mazes)
    return new_mazes, saved_maze


def delete_maze_at(mazes, index):
    if index < 0 or index >= len(mazes):
        return list(mazes), None

    deleted_name = mazes[index].name
    new_mazes = list(mazes)
    new_mazes.pop(index)
    write_saved_mazes(new_mazes)
    return new_mazes, deleted_name


def rename_maze_at(mazes, index, new_name):
    if index < 0 or index >= len(mazes):
        return list(mazes), None

    updated = list(mazes)
    updated[index] = clone_maze(updated[index])
    updated[index].name = new_name
    write_saved_mazes(updated)
    return updated, updated[index]


def replace_maze(mazes, updated_maze):
    new_mazes = []
    replaced = False

    for maze in mazes:
        if maze.maze_id == updated_maze.maze_id:
            new_mazes.append(clone_maze(updated_maze))
            replaced = True
        else:
            new_mazes.append(maze)

    if replaced:
        write_saved_mazes(new_mazes)

    return new_mazes, replaced


def add_leaderboard_record(mazes, maze_id, player_name, elapsed_time):
    if not maze_id:
        return list(mazes), None

    updated = list(mazes)
    changed_maze = None

    for index, maze in enumerate(updated):
        if maze.maze_id != maze_id:
            continue

        changed_maze = clone_maze(maze)
        new_entry = {
            "player": player_name,
            "time": round(float(elapsed_time), 2),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        leaderboard_by_player = {}
        for item in changed_maze.leaderboard:
            existing = leaderboard_by_player.get(item["player"])
            if existing is None or item["time"] < existing["time"]:
                leaderboard_by_player[item["player"]] = dict(item)

        existing_best = leaderboard_by_player.get(player_name)
        if existing_best is None or new_entry["time"] < existing_best["time"]:
            leaderboard_by_player[player_name] = new_entry

        changed_maze.leaderboard = sorted(
            leaderboard_by_player.values(),
            key=lambda item: item["time"],
        )[:MAX_LEADERBOARD_ENTRIES]
        updated[index] = changed_maze
        write_saved_mazes(updated)
        break

    return updated, changed_maze


def delete_leaderboard_entry(mazes, maze_id, entry_index):
    if not maze_id:
        return list(mazes), None

    updated = list(mazes)
    changed_maze = None

    for index, maze in enumerate(updated):
        if maze.maze_id != maze_id:
            continue

        if entry_index < 0 or entry_index >= len(maze.leaderboard):
            return updated, None

        changed_maze = clone_maze(maze)
        changed_maze.leaderboard = list(changed_maze.leaderboard)
        changed_maze.leaderboard.pop(entry_index)
        updated[index] = changed_maze
        write_saved_mazes(updated)
        break

    return updated, changed_maze
