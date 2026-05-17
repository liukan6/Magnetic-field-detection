from dataclasses import dataclass

import pygame

from config import (
    BALL,
    BALL_RADIUS,
    BG,
    BUTTON,
    BUTTON_HOVER,
    BUTTON_TEXT,
    DATA_PANEL_HEIGHT,
    GOAL,
    GRID,
    INPUT_SCALE,
    PANEL,
    PANEL_ALT,
    STATUS_INFO,
    TEXT,
    TOP_BAR_HEIGHT,
    TRAIL,
    WALL,
)
from maze_logic import build_wall_rects


@dataclass
class MazeViewport:
    left: int
    top: int
    cell_size: int
    wall_thickness: int
    maze_width: int
    maze_height: int


@dataclass
class StartScreenLayout:
    preview_panel: pygame.Rect
    size_panel: pygame.Rect
    action_panel: pygame.Rect
    player_panel: pygame.Rect
    saved_panel: pygame.Rect
    leaderboard_panel: pygame.Rect
    buttons: dict
    saved_item_rects: list
    saved_scrollbar: pygame.Rect = None
    saved_thumb: pygame.Rect = None
    saved_visible_count: int = 0
    saved_total_count: int = 0
    leaderboard_item_rects: list = None
    leaderboard_scrollbar: pygame.Rect = None
    leaderboard_thumb: pygame.Rect = None
    leaderboard_visible_count: int = 0
    leaderboard_total_count: int = 0


def init_fonts():
    return {
        "title": pygame.font.Font(r"C:\Windows\Fonts\msyh.ttc", 34),
        "body": pygame.font.Font(r"C:\Windows\Fonts\msyh.ttc", 22),
        "button": pygame.font.Font(r"C:\Windows\Fonts\msyh.ttc", 21),
        "mono": pygame.font.Font(r"C:\Windows\Fonts\consola.ttf", 22),
        "status": pygame.font.Font(r"C:\Windows\Fonts\msyh.ttc", 20),
        "small": pygame.font.Font(r"C:\Windows\Fonts\msyh.ttc", 18),
    }


def build_game_buttons(width):
    menu_top = 6
    menu_height = TOP_BAR_HEIGHT - 12
    button_width = 158
    gap = 10
    names = ["menu", "save_maze", "new_maze", "recalibrate", "reset_ball"]
    labels = {
        "menu": "Start Menu",
        "save_maze": "Save Maze",
        "new_maze": "New Maze",
        "recalibrate": "Recalibrate",
        "reset_ball": "Reset Ball",
        "close": "Close",
    }

    rects = {}
    for index, name in enumerate(names):
        rects[name] = pygame.Rect(
            18 + index * (button_width + gap),
            menu_top,
            button_width,
            menu_height,
        )

    rects["close"] = pygame.Rect(width - button_width - 18, menu_top, button_width, menu_height)
    return rects, labels


def build_start_screen_layout(width, height, saved_count, saved_scroll=0, leaderboard_total=0, leaderboard_scroll=0):
    panel_top = 92
    outer_margin = 24
    panel_gap = 16
    preview_width = int(width * 0.52)
    preview_height = min(max(height - 430, 360), 460)
    preview_panel = pygame.Rect(outer_margin, panel_top, preview_width, preview_height)
    sidebar_x = preview_panel.right + 18
    sidebar_width = width - sidebar_x - outer_margin

    size_panel = pygame.Rect(sidebar_x, panel_top, sidebar_width, 152)
    player_panel = pygame.Rect(sidebar_x, size_panel.bottom + 14, sidebar_width, 90)
    action_panel = pygame.Rect(sidebar_x, player_panel.bottom + 14, sidebar_width, 190)

    lower_top = max(preview_panel.bottom, action_panel.bottom) + panel_gap
    lower_height = max(height - lower_top - 46, 220)
    lower_width = width - outer_margin * 2
    column_width = (lower_width - panel_gap) // 2

    saved_panel = pygame.Rect(outer_margin, lower_top, column_width, lower_height)
    leaderboard_panel = pygame.Rect(saved_panel.right + panel_gap, lower_top, lower_width - column_width - panel_gap, lower_height)

    buttons = {
        "rows_minus": pygame.Rect(size_panel.x + 24, size_panel.y + 84, 44, 34),
        "rows_plus": pygame.Rect(size_panel.x + 214, size_panel.y + 84, 44, 34),
        "cols_minus": pygame.Rect(size_panel.x + 24, size_panel.y + 122, 44, 34),
        "cols_plus": pygame.Rect(size_panel.x + 214, size_panel.y + 122, 44, 34),
        "player_name": pygame.Rect(player_panel.x + 20, player_panel.y + 42, sidebar_width - 40, 34),
        "generate": pygame.Rect(action_panel.x + 20, action_panel.y + 54, sidebar_width - 40, 40),
        "play": pygame.Rect(action_panel.x + 20, action_panel.y + 104, sidebar_width - 40, 40),
        "save_preview": pygame.Rect(action_panel.x + 20, action_panel.y + 154, sidebar_width - 40, 40),
        "maze_name": pygame.Rect(leaderboard_panel.x + 18, leaderboard_panel.y + 48, leaderboard_panel.width - 36, 36),
        "delete_record": pygame.Rect(leaderboard_panel.x + 20, leaderboard_panel.bottom - 42, leaderboard_panel.width - 40, 34),
        "load_saved": pygame.Rect(saved_panel.x + 20, saved_panel.bottom - 82, sidebar_width - 40, 34),
        "delete_saved": pygame.Rect(saved_panel.x + 20, saved_panel.bottom - 42, sidebar_width - 40, 34),
        "close": pygame.Rect(width - 178, 18, 140, 38),
    }
    buttons["load_saved"].width = saved_panel.width - 40
    buttons["delete_saved"].width = saved_panel.width - 40

    saved_item_rects = []
    saved_item_top = saved_panel.y + 52
    saved_item_height = 34
    saved_item_step = 40
    saved_items_bottom = saved_panel.bottom - 96
    saved_visible = max((saved_items_bottom - saved_item_top) // saved_item_step, 0)
    saved_total = saved_count

    saved_needs_bar = saved_total > saved_visible and saved_visible > 0
    saved_scrollbar = None
    saved_thumb = None

    saved_row_left = saved_panel.x + 16
    saved_row_width = saved_panel.width - 32
    if saved_needs_bar:
        saved_row_width -= 16

    saved_max_scroll = max(saved_total - saved_visible, 0)
    clamped_saved_scroll = max(0, min(saved_scroll, saved_max_scroll))

    for i in range(min(saved_total - clamped_saved_scroll, saved_visible)):
        absolute_index = clamped_saved_scroll + i
        rect = pygame.Rect(saved_row_left, saved_item_top + i * saved_item_step, saved_row_width, saved_item_height)
        saved_item_rects.append((absolute_index, rect))

    if saved_needs_bar:
        track_x = saved_panel.right - 18
        track_y = saved_item_top
        track_h = saved_visible * saved_item_step - (saved_item_step - saved_item_height)
        saved_scrollbar = pygame.Rect(track_x, track_y, 8, track_h)
        thumb_h = max(int(track_h * saved_visible / saved_total), 24)
        thumb_h = min(thumb_h, track_h)
        if saved_max_scroll > 0:
            thumb_y = track_y + int((track_h - thumb_h) * clamped_saved_scroll / saved_max_scroll)
        else:
            thumb_y = track_y
        saved_thumb = pygame.Rect(track_x, thumb_y, 8, thumb_h)

    leaderboard_item_rects = []
    leaderboard_scrollbar = None
    leaderboard_thumb = None
    leaderboard_item_top = leaderboard_panel.y + 124
    leaderboard_item_step = 38
    leaderboard_visible = max((leaderboard_panel.bottom - 56 - leaderboard_item_top) // leaderboard_item_step, 0)
    leaderboard_needs_bar = leaderboard_total > leaderboard_visible and leaderboard_visible > 0

    lb_row_left = leaderboard_panel.x + 18
    lb_row_width = leaderboard_panel.width - 36
    if leaderboard_needs_bar:
        lb_row_width -= 16

    leaderboard_max_scroll = max(leaderboard_total - leaderboard_visible, 0)
    clamped_lb_scroll = max(0, min(leaderboard_scroll, leaderboard_max_scroll))

    for i in range(min(leaderboard_total - clamped_lb_scroll, leaderboard_visible)):
        absolute_index = clamped_lb_scroll + i
        rect = pygame.Rect(lb_row_left, leaderboard_item_top + i * leaderboard_item_step, lb_row_width, leaderboard_item_step - 4)
        leaderboard_item_rects.append((absolute_index, rect))

    if leaderboard_needs_bar:
        track_x = leaderboard_panel.right - 20
        track_y = leaderboard_item_top
        track_h = leaderboard_visible * leaderboard_item_step
        leaderboard_scrollbar = pygame.Rect(track_x, track_y, 8, track_h)
        thumb_h = max(int(track_h * leaderboard_visible / leaderboard_total), 24)
        thumb_h = min(thumb_h, track_h)
        if leaderboard_max_scroll > 0:
            thumb_y = track_y + int((track_h - thumb_h) * clamped_lb_scroll / leaderboard_max_scroll)
        else:
            thumb_y = track_y
        leaderboard_thumb = pygame.Rect(track_x, thumb_y, 8, thumb_h)

    return StartScreenLayout(
        preview_panel=preview_panel,
        size_panel=size_panel,
        player_panel=player_panel,
        action_panel=action_panel,
        saved_panel=saved_panel,
        leaderboard_panel=leaderboard_panel,
        buttons=buttons,
        saved_item_rects=saved_item_rects,
        saved_scrollbar=saved_scrollbar,
        saved_thumb=saved_thumb,
        saved_visible_count=saved_visible,
        saved_total_count=saved_total,
        leaderboard_item_rects=leaderboard_item_rects,
        leaderboard_scrollbar=leaderboard_scrollbar,
        leaderboard_thumb=leaderboard_thumb,
        leaderboard_visible_count=leaderboard_visible,
        leaderboard_total_count=leaderboard_total,
    )


def build_game_viewport(width, height, rows, cols):
    content_top = TOP_BAR_HEIGHT + DATA_PANEL_HEIGHT + 34
    available_width = width - 72
    available_height = height - content_top - 36
    cell_size = int(min(available_width / cols, available_height / rows))
    cell_size = max(48, min(110, cell_size))
    wall_thickness = max(10, min(18, cell_size // 5))
    maze_width = cols * cell_size
    maze_height = rows * cell_size
    left = max((width - maze_width) // 2, 24)
    top = content_top + max((available_height - maze_height) // 2, 0)
    return MazeViewport(left, top, cell_size, wall_thickness, maze_width, maze_height)


def build_preview_viewport(panel_rect, rows, cols):
    padding_x = 28
    padding_y = 54
    available_width = panel_rect.width - padding_x * 2
    available_height = panel_rect.height - padding_y * 2
    cell_size = int(min(available_width / cols, available_height / rows))
    cell_size = max(26, min(54, cell_size))
    wall_thickness = max(6, min(12, cell_size // 5))
    maze_width = cols * cell_size
    maze_height = rows * cell_size
    left = panel_rect.x + (panel_rect.width - maze_width) // 2
    top = panel_rect.y + 36 + (panel_rect.height - 54 - maze_height) // 2
    return MazeViewport(left, top, cell_size, wall_thickness, maze_width, maze_height)


def cell_center(cell, viewport):
    row, col = cell
    return (
        viewport.left + col * viewport.cell_size + viewport.cell_size // 2,
        viewport.top + row * viewport.cell_size + viewport.cell_size // 2,
    )


def build_goal_rect(goal_cell, viewport):
    goal_rect = pygame.Rect(0, 0, max(viewport.cell_size // 2, 28), max(viewport.cell_size // 2, 28))
    goal_rect.center = cell_center(goal_cell, viewport)
    return goal_rect


def remap_point(x, y, old_viewport, new_viewport):
    if old_viewport.maze_width <= 0 or old_viewport.maze_height <= 0:
        return x, y

    normalized_x = (x - old_viewport.left) / old_viewport.maze_width
    normalized_y = (y - old_viewport.top) / old_viewport.maze_height
    return (
        new_viewport.left + normalized_x * new_viewport.maze_width,
        new_viewport.top + normalized_y * new_viewport.maze_height,
    )


def trim_label(text, max_length=28):
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def trim_center_label(text, max_length=34):
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def draw_button(screen, rect, label, hovered, fonts):
    color = BUTTON_HOVER if hovered else BUTTON
    pygame.draw.rect(screen, color, rect, border_radius=10)
    text_surface = fonts["button"].render(label, True, BUTTON_TEXT)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)


def draw_input_box(screen, rect, text, active, placeholder, fonts, composition=""):
    fill = BUTTON_HOVER if active else PANEL
    pygame.draw.rect(screen, fill, rect, border_radius=10)
    pygame.draw.rect(screen, GRID, rect, width=1, border_radius=10)

    if active:
        base_text = text
        if not base_text and not composition:
            placeholder_surface = fonts["small"].render(placeholder, True, STATUS_INFO)
            screen.blit(placeholder_surface, (rect.x + 10, rect.y + 8))
            return

        cursor_x = rect.x + 10
        if base_text:
            base_surface = fonts["small"].render(trim_center_label(base_text, 28), True, BUTTON_TEXT)
            screen.blit(base_surface, (rect.x + 10, rect.y + 8))
            cursor_x = rect.x + 10 + base_surface.get_width()

        if composition:
            comp_surface = fonts["small"].render(trim_center_label(composition, 12), True, STATUS_INFO)
            screen.blit(comp_surface, (cursor_x, rect.y + 8))
            cursor_x += comp_surface.get_width()

        cursor_surface = fonts["small"].render("|", True, BUTTON_TEXT)
        screen.blit(cursor_surface, (cursor_x + 2, rect.y + 8))
        return

    shown = text if text else placeholder
    color = BUTTON_TEXT if text else STATUS_INFO
    text_surface = fonts["small"].render(trim_center_label(shown, 36), True, color)
    screen.blit(text_surface, (rect.x + 10, rect.y + 8))


def draw_maze_panel(screen, viewport):
    maze_panel = pygame.Rect(
        viewport.left - 18,
        viewport.top - 18,
        viewport.maze_width + 36,
        viewport.maze_height + 36,
    )
    pygame.draw.rect(screen, PANEL_ALT, maze_panel, border_radius=16)
    pygame.draw.rect(screen, GRID, maze_panel, width=2, border_radius=16)

    for x in range(viewport.left, viewport.left + viewport.maze_width + 1, 40):
        pygame.draw.line(screen, GRID, (x, viewport.top), (x, viewport.top + viewport.maze_height))

    for y in range(viewport.top, viewport.top + viewport.maze_height + 1, 40):
        pygame.draw.line(screen, GRID, (viewport.left, y), (viewport.left + viewport.maze_width, y))


def draw_maze(screen, maze, viewport, goal_rect, trail, ball_pos):
    walls = build_wall_rects(maze, viewport)
    draw_maze_panel(screen, viewport)

    for wall in walls:
        pygame.draw.rect(screen, WALL, wall, border_radius=6)

    pygame.draw.rect(screen, GOAL, goal_rect, border_radius=10)

    for index, point in enumerate(trail):
        alpha = index / max(len(trail), 1)
        radius = int(BALL_RADIUS * alpha)
        if radius > 0:
            pygame.draw.circle(screen, TRAIL, (int(point[0]), int(point[1])), radius, 1)

    if ball_pos is not None:
        pygame.draw.circle(screen, BALL, (int(ball_pos[0]), int(ball_pos[1])), BALL_RADIUS)

    return walls


def draw_data_panel(screen, fonts, width, bx_filtered, by_filtered, bx0, by0, status_message, status_color, elapsed_time, timer_started):
    panel_rect = pygame.Rect(18, TOP_BAR_HEIGHT + 10, width - 36, DATA_PANEL_HEIGHT - 18)
    pygame.draw.rect(screen, PANEL_ALT, panel_rect, border_radius=14)
    pygame.draw.rect(screen, GRID, panel_rect, width=2, border_radius=14)

    title = fonts["status"].render("Monitoring", True, TEXT)
    info1 = fonts["mono"].render(f"Bx = {bx_filtered:.0f}", True, TEXT)
    info2 = fonts["mono"].render(f"By = {by_filtered:.0f}", True, TEXT)
    info3 = fonts["mono"].render(
        f"scaled = ({bx_filtered * INPUT_SCALE:.2f}, {by_filtered * INPUT_SCALE:.2f})",
        True,
        TEXT,
    )
    info4 = fonts["mono"].render(f"baseline = ({bx0:.0f}, {by0:.0f})", True, TEXT)

    if timer_started:
        timer_text = f"timer = {elapsed_time:0.2f}s"
    else:
        timer_text = "timer = waiting for movement"

    info5 = fonts["mono"].render(timer_text, True, TEXT)
    status_surface = fonts["status"].render(status_message, True, status_color)

    screen.blit(title, (panel_rect.x + 16, panel_rect.y + 10))
    screen.blit(status_surface, (panel_rect.x + 170, panel_rect.y + 12))
    screen.blit(info1, (panel_rect.x + 16, panel_rect.y + 42))
    screen.blit(info2, (panel_rect.x + 216, panel_rect.y + 42))
    screen.blit(info3, (panel_rect.x + 420, panel_rect.y + 42))
    screen.blit(info4, (panel_rect.x + 16, panel_rect.y + 72))
    screen.blit(info5, (panel_rect.x + 720, panel_rect.y + 72))


def draw_start_screen(
    screen,
    fonts,
    width,
    height,
    preview_maze,
    rows_setting,
    cols_setting,
    saved_mazes,
    selected_saved_index,
    status_message,
    mouse_pos,
    player_name,
    editing_player_name,
    editing_maze_name,
    maze_name_text,
    ime_preview_text,
    original_input_value,
    saved_scroll=0,
    leaderboard_scroll=0,
    selected_leaderboard_index=None,
):
    screen.fill(BG)

    selected_maze = None
    if selected_saved_index is not None and 0 <= selected_saved_index < len(saved_mazes):
        selected_maze = saved_mazes[selected_saved_index]

    leaderboard_total = len(selected_maze.leaderboard) if selected_maze else 0
    layout = build_start_screen_layout(
        width,
        height,
        len(saved_mazes),
        saved_scroll=saved_scroll,
        leaderboard_total=leaderboard_total,
        leaderboard_scroll=leaderboard_scroll,
    )

    title = fonts["title"].render("Magnetic Maze Setup", True, TEXT)
    subtitle = fonts["status"].render(
        "Choose a size, set player name, generate or reuse a maze, and check the leaderboard.",
        True,
        STATUS_INFO,
    )
    screen.blit(title, (24, 22))
    screen.blit(subtitle, (24, 58))

    pygame.draw.rect(screen, PANEL_ALT, layout.preview_panel, border_radius=18)
    pygame.draw.rect(screen, GRID, layout.preview_panel, width=2, border_radius=18)
    pygame.draw.rect(screen, PANEL_ALT, layout.size_panel, border_radius=18)
    pygame.draw.rect(screen, GRID, layout.size_panel, width=2, border_radius=18)
    pygame.draw.rect(screen, PANEL_ALT, layout.player_panel, border_radius=18)
    pygame.draw.rect(screen, GRID, layout.player_panel, width=2, border_radius=18)
    pygame.draw.rect(screen, PANEL_ALT, layout.action_panel, border_radius=18)
    pygame.draw.rect(screen, GRID, layout.action_panel, width=2, border_radius=18)
    pygame.draw.rect(screen, PANEL_ALT, layout.saved_panel, border_radius=18)
    pygame.draw.rect(screen, GRID, layout.saved_panel, width=2, border_radius=18)
    pygame.draw.rect(screen, PANEL_ALT, layout.leaderboard_panel, border_radius=18)
    pygame.draw.rect(screen, GRID, layout.leaderboard_panel, width=2, border_radius=18)

    preview_title = fonts["body"].render("Preview Maze", True, TEXT)
    size_title = fonts["body"].render("Maze Size", True, TEXT)
    player_title = fonts["body"].render("Player Name", True, TEXT)
    action_title = fonts["body"].render("Actions", True, TEXT)
    saved_title = fonts["body"].render("Saved Mazes", True, TEXT)
    leaderboard_title = fonts["body"].render("Leaderboard", True, TEXT)
    preview_info = fonts["small"].render(
        f"{preview_maze.cols} cols x {preview_maze.rows} rows",
        True,
        STATUS_INFO,
    )

    screen.blit(preview_title, (layout.preview_panel.x + 18, layout.preview_panel.y + 14))
    screen.blit(preview_info, (layout.preview_panel.x + 180, layout.preview_panel.y + 17))
    screen.blit(size_title, (layout.size_panel.x + 18, layout.size_panel.y + 14))
    screen.blit(player_title, (layout.player_panel.x + 18, layout.player_panel.y + 14))
    screen.blit(action_title, (layout.action_panel.x + 18, layout.action_panel.y + 14))
    screen.blit(saved_title, (layout.saved_panel.x + 18, layout.saved_panel.y + 14))
    screen.blit(leaderboard_title, (layout.leaderboard_panel.x + 18, layout.leaderboard_panel.y + 14))

    draw_input_box(
        screen,
        layout.buttons["player_name"],
        player_name,
        editing_player_name,
        original_input_value if editing_player_name else "Click here to enter player name",
        fonts,
        ime_preview_text if editing_player_name else "",
    )
    if editing_player_name:
        player_hint_text = "Typing is saved automatically. Press Esc or click away to finish."
    else:
        player_hint_text = "A saved maze records your time under this player name."
    player_hint = fonts["small"].render(player_hint_text, True, STATUS_INFO)
    screen.blit(player_hint, (layout.player_panel.x + 20, layout.player_panel.y + 48 + 38))

    preview_viewport = build_preview_viewport(layout.preview_panel, preview_maze.rows, preview_maze.cols)
    preview_goal = build_goal_rect(preview_maze.goal, preview_viewport)
    preview_walls = build_wall_rects(preview_maze, preview_viewport)
    draw_maze_panel(screen, preview_viewport)
    for wall in preview_walls:
        pygame.draw.rect(screen, WALL, wall, border_radius=4)
    pygame.draw.rect(screen, GOAL, preview_goal, border_radius=8)
    start_center = cell_center(preview_maze.start, preview_viewport)
    pygame.draw.circle(screen, BALL, (int(start_center[0]), int(start_center[1])), max(preview_viewport.cell_size // 5, 8))

    rows_text = fonts["body"].render(f"Rows: {rows_setting}", True, TEXT)
    cols_text = fonts["body"].render(f"Cols: {cols_setting}", True, TEXT)
    screen.blit(rows_text, (layout.size_panel.x + 84, layout.size_panel.y + 86))
    screen.blit(cols_text, (layout.size_panel.x + 84, layout.size_panel.y + 124))

    draw_button(screen, layout.buttons["rows_minus"], "-", layout.buttons["rows_minus"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["rows_plus"], "+", layout.buttons["rows_plus"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["cols_minus"], "-", layout.buttons["cols_minus"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["cols_plus"], "+", layout.buttons["cols_plus"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["generate"], "Generate Random Maze", layout.buttons["generate"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["play"], "Play Selected Maze", layout.buttons["play"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["save_preview"], "Save Preview Maze", layout.buttons["save_preview"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["load_saved"], "Load Highlighted Maze", layout.buttons["load_saved"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["delete_saved"], "Delete Highlighted Maze", layout.buttons["delete_saved"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["close"], "Close", layout.buttons["close"].collidepoint(mouse_pos), fonts)

    if not saved_mazes:
        empty_text = fonts["small"].render("No saved mazes yet. Save one from the preview or gameplay.", True, STATUS_INFO)
        screen.blit(empty_text, (layout.saved_panel.x + 18, layout.saved_panel.y + 58))
    else:
        for index, rect in layout.saved_item_rects:
            maze = saved_mazes[index]
            is_selected = index == selected_saved_index
            fill = BUTTON_HOVER if is_selected else PANEL
            pygame.draw.rect(screen, fill, rect, border_radius=10)
            label = trim_label(maze.name or f"maze_{maze.cols}x{maze.rows}")
            text_surface = fonts["small"].render(label, True, BUTTON_TEXT if is_selected else TEXT)
            meta_surface = fonts["small"].render(f"{maze.cols}x{maze.rows}", True, STATUS_INFO)
            screen.blit(text_surface, (rect.x + 10, rect.y + 7))
            screen.blit(meta_surface, (rect.right - 70, rect.y + 7))

        if layout.saved_scrollbar is not None:
            pygame.draw.rect(screen, PANEL, layout.saved_scrollbar, border_radius=4)
            pygame.draw.rect(screen, GRID, layout.saved_scrollbar, width=1, border_radius=4)
            if layout.saved_thumb is not None:
                pygame.draw.rect(screen, BUTTON_HOVER, layout.saved_thumb, border_radius=4)

    if selected_maze is None:
        leaderboard_empty = fonts["small"].render("Select a saved maze to see its best times.", True, STATUS_INFO)
        rename_hint = fonts["small"].render("Tip: press F2 to rename the selected saved maze.", True, STATUS_INFO)
        screen.blit(leaderboard_empty, (layout.leaderboard_panel.x + 18, layout.leaderboard_panel.y + 56))
        screen.blit(rename_hint, (layout.leaderboard_panel.x + 18, layout.leaderboard_panel.y + 88))
    else:
        if editing_maze_name:
            meta_text = f"Enter confirm   Esc cancel   size {selected_maze.cols}x{selected_maze.rows}"
        else:
            meta_text = f"F2 rename   size {selected_maze.cols}x{selected_maze.rows}"
        selected_meta = fonts["small"].render(meta_text, True, STATUS_INFO)
        draw_input_box(
            screen,
            layout.buttons["maze_name"],
            maze_name_text if editing_maze_name else selected_maze.name,
            editing_maze_name,
            original_input_value if editing_maze_name else "Maze name",
            fonts,
            ime_preview_text if editing_maze_name else "",
        )
        screen.blit(selected_meta, (layout.leaderboard_panel.x + 18, layout.leaderboard_panel.y + 90))

        if not selected_maze.leaderboard:
            no_record = fonts["small"].render("No records yet for this maze.", True, STATUS_INFO)
            record_tip = fonts["small"].render("Play this saved maze to add a score.", True, STATUS_INFO)
            screen.blit(no_record, (layout.leaderboard_panel.x + 18, layout.leaderboard_panel.y + 126))
            screen.blit(record_tip, (layout.leaderboard_panel.x + 18, layout.leaderboard_panel.y + 156))
        else:
            for absolute_index, rect in layout.leaderboard_item_rects:
                item = selected_maze.leaderboard[absolute_index]
                rank = absolute_index + 1
                is_selected = absolute_index == selected_leaderboard_index
                if is_selected:
                    pygame.draw.rect(screen, BUTTON_HOVER, rect, border_radius=8)
                line_color = BUTTON_TEXT if is_selected else TEXT
                ts_color = BUTTON_TEXT if is_selected else STATUS_INFO
                line = f"{rank}. {item['player']}  {item['time']:.2f}s"
                timestamp = item.get("timestamp", "")
                line_surface = fonts["small"].render(trim_center_label(line, 36), True, line_color)
                ts_surface = fonts["small"].render(timestamp, True, ts_color)
                screen.blit(line_surface, (rect.x + 6, rect.y))
                screen.blit(ts_surface, (rect.x + 6, rect.y + 18))

            if layout.leaderboard_scrollbar is not None:
                pygame.draw.rect(screen, PANEL, layout.leaderboard_scrollbar, border_radius=4)
                pygame.draw.rect(screen, GRID, layout.leaderboard_scrollbar, width=1, border_radius=4)
                if layout.leaderboard_thumb is not None:
                    pygame.draw.rect(screen, BUTTON_HOVER, layout.leaderboard_thumb, border_radius=4)

        draw_button(
            screen,
            layout.buttons["delete_record"],
            "Delete Selected Record",
            layout.buttons["delete_record"].collidepoint(mouse_pos),
            fonts,
        )

    footer = fonts["status"].render(status_message, True, STATUS_INFO)
    screen.blit(footer, (24, height - 28))
    return layout


def draw_game_screen(screen, fonts, width, height, buttons, labels, maze, viewport, goal_rect, trail, ball_pos, bx_filtered, by_filtered, bx0, by0, status_message, status_color, elapsed_time, timer_started, mouse_pos):
    screen.fill(BG)

    pygame.draw.rect(screen, PANEL, (0, 0, width, TOP_BAR_HEIGHT))
    pygame.draw.line(screen, GRID, (0, TOP_BAR_HEIGHT), (width, TOP_BAR_HEIGHT), 2)

    for name, rect in buttons.items():
        draw_button(screen, rect, labels[name], rect.collidepoint(mouse_pos), fonts)

    app_title = fonts["status"].render("Magnetic Maze Control", True, TEXT)
    app_title_rect = app_title.get_rect(center=(width // 2, TOP_BAR_HEIGHT // 2 + 1))
    screen.blit(app_title, app_title_rect)

    draw_data_panel(
        screen,
        fonts,
        width,
        bx_filtered,
        by_filtered,
        bx0,
        by0,
        status_message,
        status_color,
        elapsed_time,
        timer_started,
    )

    walls = draw_maze(screen, maze, viewport, goal_rect, trail, ball_pos)
    size_text = fonts["status"].render(f"maze size: {maze.cols} x {maze.rows}", True, STATUS_INFO)
    screen.blit(size_text, (viewport.left, viewport.top - 34))
    return walls


def build_victory_dialog_rects(width, height):
    dialog = pygame.Rect(0, 0, 620, 310)
    dialog.center = (width // 2, height // 2)
    play_again = pygame.Rect(dialog.x + 38, dialog.bottom - 70, 170, 44)
    back_to_menu = pygame.Rect(dialog.centerx - 85, dialog.bottom - 70, 170, 44)
    close_game = pygame.Rect(dialog.right - 208, dialog.bottom - 70, 170, 44)
    return dialog, play_again, back_to_menu, close_game


def draw_victory_dialog(screen, fonts, width, height, elapsed_time, mouse_pos):
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    overlay.fill((5, 10, 18, 190))
    screen.blit(overlay, (0, 0))

    dialog, play_again, back_to_menu, close_game = build_victory_dialog_rects(width, height)
    pygame.draw.rect(screen, PANEL_ALT, dialog, border_radius=18)
    pygame.draw.rect(screen, GRID, dialog, width=2, border_radius=18)

    title = fonts["title"].render("Goal Reached!", True, (255, 255, 120))
    subtitle = fonts["body"].render(f"Time: {elapsed_time:0.2f}s", True, TEXT)
    tip = fonts["status"].render("Replay, go back to the menu, or close the game.", True, STATUS_INFO)

    screen.blit(title, title.get_rect(center=(dialog.centerx, dialog.y + 60)))
    screen.blit(subtitle, subtitle.get_rect(center=(dialog.centerx, dialog.y + 118)))
    screen.blit(tip, tip.get_rect(center=(dialog.centerx, dialog.y + 158)))

    draw_button(screen, play_again, "Play Again", play_again.collidepoint(mouse_pos), fonts)
    draw_button(screen, back_to_menu, "Back to Menu", back_to_menu.collidepoint(mouse_pos), fonts)
    draw_button(screen, close_game, "Close", close_game.collidepoint(mouse_pos), fonts)
    return dialog, play_again, back_to_menu, close_game
