from dataclasses import dataclass

import pygame

from config import (
    ACCENT,
    ACCENT_HOVER,
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
        "menu": "返回主菜单",
        "save_maze": "保存当前迷宫",
        "new_maze": "随机新迷宫",
        "recalibrate": "重新校准",
        "reset_ball": "重置小球",
        "close": "关闭游戏",
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
    panel_top = 152
    outer_margin = 24
    panel_gap = 16
    preview_width = int(width * 0.52)
    preview_height = min(max(height - 430, 360), 460)
    preview_panel = pygame.Rect(outer_margin, panel_top, preview_width, preview_height)
    sidebar_x = preview_panel.right + 18
    sidebar_width = width - sidebar_x - outer_margin

    size_panel = pygame.Rect(sidebar_x, panel_top, sidebar_width, 152)
    player_panel = pygame.Rect(sidebar_x, size_panel.bottom + 14, sidebar_width, 90)
    action_panel = pygame.Rect(sidebar_x, player_panel.bottom + 14, sidebar_width, 204)

    lower_top = max(preview_panel.bottom, action_panel.bottom) + panel_gap
    lower_height = max(height - lower_top - 46, 220)
    lower_width = width - outer_margin * 2
    column_width = (lower_width - panel_gap) // 2

    saved_panel = pygame.Rect(outer_margin, lower_top, column_width, lower_height)
    leaderboard_panel = pygame.Rect(saved_panel.right + panel_gap, lower_top, lower_width - column_width - panel_gap, lower_height)

    buttons = {
        "rows_minus": pygame.Rect(size_panel.x + 20, size_panel.y + 50, 44, 34),
        "rows_plus": pygame.Rect(size_panel.right - 64, size_panel.y + 50, 44, 34),
        "cols_minus": pygame.Rect(size_panel.x + 20, size_panel.y + 96, 44, 34),
        "cols_plus": pygame.Rect(size_panel.right - 64, size_panel.y + 96, 44, 34),
        "player_name": pygame.Rect(player_panel.x + 20, player_panel.y + 42, sidebar_width - 40 - 42, 34),
        "player_name_dropdown": pygame.Rect(player_panel.x + 20 + sidebar_width - 40 - 36, player_panel.y + 42, 36, 34),
        "generate": pygame.Rect(action_panel.x + 20, action_panel.y + 54, sidebar_width - 40, 40),
        "play": pygame.Rect(action_panel.x + 20, action_panel.y + 104, sidebar_width - 40, 40),
        "save_preview": pygame.Rect(action_panel.x + 20, action_panel.y + 154, sidebar_width - 40, 40),
        "maze_name": pygame.Rect(leaderboard_panel.x + 18, leaderboard_panel.y + 48, leaderboard_panel.width - 36, 36),
        "delete_record": pygame.Rect(leaderboard_panel.x + 20, leaderboard_panel.bottom - 42, leaderboard_panel.width - 40, 34),
        "delete_saved": pygame.Rect(saved_panel.x + 20, saved_panel.bottom - 42, sidebar_width - 40, 34),
        "close": pygame.Rect(width - 178, 18, 140, 38),
    }
    buttons["delete_saved"].width = saved_panel.width - 40

    saved_item_rects = []
    saved_item_top = saved_panel.y + 52
    saved_item_height = 34
    saved_item_step = 40
    saved_items_bottom = saved_panel.bottom - 56
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


def build_player_dropdown_rects(layout, item_count, max_visible=8):
    if item_count <= 0:
        return None, []
    visible = min(item_count, max_visible)
    input_rect = layout.buttons["player_name"]
    dropdown_rect = layout.buttons["player_name_dropdown"]
    panel_x = input_rect.x
    panel_y = input_rect.bottom + 4
    panel_w = dropdown_rect.right - input_rect.x
    item_h = 30
    panel_h = visible * item_h + 8
    panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    item_rects = []
    for i in range(visible):
        item_rects.append(pygame.Rect(panel_x + 4, panel_y + 4 + i * item_h, panel_w - 8, item_h))
    return panel, item_rects


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


def draw_button(screen, rect, label, hovered, fonts, highlight=False):
    if highlight:
        color = ACCENT_HOVER if hovered else ACCENT
        text_color = BUTTON_TEXT
        border_color = ACCENT_HOVER
        border_width = 2
    else:
        color = BUTTON_HOVER if hovered else BUTTON
        text_color = BUTTON_TEXT if hovered else TEXT
        border_color = GRID
        border_width = 1
    pygame.draw.rect(screen, color, rect, border_radius=10)
    pygame.draw.rect(screen, border_color, rect, width=border_width, border_radius=10)
    text_surface = fonts["button"].render(label, True, text_color)
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
    color = TEXT if text else STATUS_INFO
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

    title = fonts["status"].render("传感器监测", True, TEXT)
    info1 = fonts["mono"].render(f"Bx = {bx_filtered:.0f}", True, TEXT)
    info2 = fonts["mono"].render(f"By = {by_filtered:.0f}", True, TEXT)
    info3 = fonts["mono"].render(
        f"scaled = ({bx_filtered * INPUT_SCALE:.2f}, {by_filtered * INPUT_SCALE:.2f})",
        True,
        TEXT,
    )
    info4 = fonts["mono"].render(f"baseline = ({bx0:.0f}, {by0:.0f})", True, TEXT)

    if timer_started:
        timer_text = f"用时 = {elapsed_time:0.2f}s"
    else:
        timer_text = "用时 = 等待开始移动"

    info5 = fonts["status"].render(timer_text, True, TEXT)
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
    player_dropdown_open=False,
    player_dropdown_items=None,
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

    title = fonts["title"].render("磁控迷宫小球", True, TEXT)
    subtitle = fonts["status"].render(
        "选择迷宫尺寸、设置玩家姓名，生成或加载迷宫，并查看排行榜。",
        True,
        STATUS_INFO,
    )

    intro_line1 = fonts["small"].render(
        "游戏玩法：通过轻推磁纤毛控制小球移动（类似操控杆），将小球引导至绿色终点。",
        True,
        STATUS_INFO,
    )
    intro_line2 = fonts["small"].render(
        "输入玩家姓名，每个迷宫会记录你的最佳成绩到排行榜。点击【已保存的迷宫】中的迷宫即可加载。",
        True,
        STATUS_INFO,
    )
    intro_line3 = fonts["small"].render(
        "准备好后，点击右侧绿色【开始游戏】按钮进入游戏。",
        True,
        STATUS_INFO,
    )

    screen.blit(title, (24, 22))
    screen.blit(subtitle, (24, 58))
    screen.blit(intro_line1, (24, 82))
    screen.blit(intro_line2, (24, 104))
    screen.blit(intro_line3, (24, 126))

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

    preview_title = fonts["body"].render("迷宫预览", True, TEXT)
    size_title = fonts["body"].render("迷宫尺寸", True, TEXT)
    player_title = fonts["body"].render("玩家姓名", True, TEXT)
    action_title = fonts["body"].render("操作", True, TEXT)
    saved_title = fonts["body"].render("已保存的迷宫", True, TEXT)
    leaderboard_title = fonts["body"].render("排行榜", True, TEXT)
    preview_info = fonts["small"].render(
        f"{preview_maze.cols} 列 × {preview_maze.rows} 行",
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
        original_input_value if editing_player_name else "点击此处输入玩家姓名",
        fonts,
        ime_preview_text if editing_player_name else "",
    )

    dropdown_btn = layout.buttons["player_name_dropdown"]
    dropdown_hover = dropdown_btn.collidepoint(mouse_pos)
    dropdown_fill = BUTTON_HOVER if (dropdown_hover or player_dropdown_open) else PANEL
    pygame.draw.rect(screen, dropdown_fill, dropdown_btn, border_radius=10)
    pygame.draw.rect(screen, GRID, dropdown_btn, width=1, border_radius=10)
    arrow_glyph = "▲" if player_dropdown_open else "▼"
    arrow_surface = fonts["small"].render(arrow_glyph, True, BUTTON_TEXT)
    screen.blit(arrow_surface, arrow_surface.get_rect(center=dropdown_btn.center))
    if editing_player_name:
        player_hint_text = "输入即时保存。按 Esc 或点击其他位置完成。"
    else:
        player_hint_text = "完成迷宫后会以此姓名记录最佳成绩。"
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

    rows_text = fonts["body"].render(f"行数: {rows_setting}", True, TEXT)
    cols_text = fonts["body"].render(f"列数: {cols_setting}", True, TEXT)
    rows_rect = rows_text.get_rect(center=(layout.size_panel.centerx, layout.size_panel.y + 50 + 17))
    cols_rect = cols_text.get_rect(center=(layout.size_panel.centerx, layout.size_panel.y + 96 + 17))
    screen.blit(rows_text, rows_rect)
    screen.blit(cols_text, cols_rect)

    draw_button(screen, layout.buttons["rows_minus"], "-", layout.buttons["rows_minus"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["rows_plus"], "+", layout.buttons["rows_plus"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["cols_minus"], "-", layout.buttons["cols_minus"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["cols_plus"], "+", layout.buttons["cols_plus"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["generate"], "随机生成迷宫", layout.buttons["generate"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["play"], "开始游戏", layout.buttons["play"].collidepoint(mouse_pos), fonts, highlight=True)
    draw_button(screen, layout.buttons["save_preview"], "保存当前预览", layout.buttons["save_preview"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["delete_saved"], "删除选中的迷宫", layout.buttons["delete_saved"].collidepoint(mouse_pos), fonts)
    draw_button(screen, layout.buttons["close"], "关闭游戏", layout.buttons["close"].collidepoint(mouse_pos), fonts)

    if not saved_mazes:
        empty_text = fonts["small"].render("暂无保存的迷宫，可在预览中点击保存。", True, STATUS_INFO)
        screen.blit(empty_text, (layout.saved_panel.x + 18, layout.saved_panel.y + 58))
    else:
        for index, rect in layout.saved_item_rects:
            maze = saved_mazes[index]
            is_selected = index == selected_saved_index
            fill = BUTTON_HOVER if is_selected else PANEL
            pygame.draw.rect(screen, fill, rect, border_radius=10)
            label = trim_label(maze.name or f"maze_{maze.cols}x{maze.rows}")
            text_surface = fonts["small"].render(label, True, BUTTON_TEXT if is_selected else TEXT)
            meta_surface = fonts["small"].render(
                f"{maze.cols}x{maze.rows}",
                True,
                BUTTON_TEXT if is_selected else STATUS_INFO,
            )
            screen.blit(text_surface, (rect.x + 10, rect.y + 7))
            screen.blit(meta_surface, (rect.right - 70, rect.y + 7))

        if layout.saved_scrollbar is not None:
            pygame.draw.rect(screen, PANEL, layout.saved_scrollbar, border_radius=4)
            pygame.draw.rect(screen, GRID, layout.saved_scrollbar, width=1, border_radius=4)
            if layout.saved_thumb is not None:
                pygame.draw.rect(screen, BUTTON_HOVER, layout.saved_thumb, border_radius=4)

    if selected_maze is None:
        leaderboard_empty = fonts["small"].render("选择一个保存的迷宫以查看最佳成绩。", True, STATUS_INFO)
        rename_hint = fonts["small"].render("提示：按 F2 可重命名选中的迷宫。", True, STATUS_INFO)
        screen.blit(leaderboard_empty, (layout.leaderboard_panel.x + 18, layout.leaderboard_panel.y + 56))
        screen.blit(rename_hint, (layout.leaderboard_panel.x + 18, layout.leaderboard_panel.y + 88))
    else:
        if editing_maze_name:
            meta_text = f"Enter 确认   Esc 取消   尺寸 {selected_maze.cols}×{selected_maze.rows}"
        else:
            meta_text = f"按 F2 重命名   尺寸 {selected_maze.cols}×{selected_maze.rows}"
        selected_meta = fonts["small"].render(meta_text, True, STATUS_INFO)
        draw_input_box(
            screen,
            layout.buttons["maze_name"],
            maze_name_text if editing_maze_name else selected_maze.name,
            editing_maze_name,
            original_input_value if editing_maze_name else "迷宫名称",
            fonts,
            ime_preview_text if editing_maze_name else "",
        )
        screen.blit(selected_meta, (layout.leaderboard_panel.x + 18, layout.leaderboard_panel.y + 90))

        if not selected_maze.leaderboard:
            no_record = fonts["small"].render("此迷宫还没有任何成绩。", True, STATUS_INFO)
            record_tip = fonts["small"].render("玩一局即可上榜。", True, STATUS_INFO)
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
            "删除选中的记录",
            layout.buttons["delete_record"].collidepoint(mouse_pos),
            fonts,
        )

    footer = fonts["status"].render(status_message, True, STATUS_INFO)
    screen.blit(footer, (24, height - 28))

    if player_dropdown_open:
        items = player_dropdown_items or []
        panel_rect, item_rects = build_player_dropdown_rects(layout, len(items))
        if panel_rect is None:
            empty_rect = pygame.Rect(
                layout.buttons["player_name"].x,
                layout.buttons["player_name"].bottom + 4,
                layout.buttons["player_name_dropdown"].right - layout.buttons["player_name"].x,
                34,
            )
            pygame.draw.rect(screen, PANEL_ALT, empty_rect, border_radius=10)
            pygame.draw.rect(screen, GRID, empty_rect, width=1, border_radius=10)
            empty_text = fonts["small"].render("暂无历史玩家名", True, STATUS_INFO)
            screen.blit(empty_text, empty_text.get_rect(center=empty_rect.center))
        else:
            pygame.draw.rect(screen, PANEL_ALT, panel_rect, border_radius=10)
            pygame.draw.rect(screen, GRID, panel_rect, width=1, border_radius=10)
            for rect, name in zip(item_rects, items):
                hovered = rect.collidepoint(mouse_pos)
                is_current = name == player_name
                if hovered:
                    pygame.draw.rect(screen, BUTTON_HOVER, rect, border_radius=6)
                elif is_current:
                    pygame.draw.rect(screen, BUTTON, rect, border_radius=6)
                color = BUTTON_TEXT if (hovered or is_current) else TEXT
                label_surface = fonts["small"].render(trim_center_label(name, 28), True, color)
                screen.blit(label_surface, (rect.x + 8, rect.y + 5))

    return layout


def draw_game_screen(screen, fonts, width, height, buttons, labels, maze, viewport, goal_rect, trail, ball_pos, bx_filtered, by_filtered, bx0, by0, status_message, status_color, elapsed_time, timer_started, mouse_pos):
    screen.fill(BG)

    pygame.draw.rect(screen, PANEL, (0, 0, width, TOP_BAR_HEIGHT))
    pygame.draw.line(screen, GRID, (0, TOP_BAR_HEIGHT), (width, TOP_BAR_HEIGHT), 2)

    for name, rect in buttons.items():
        draw_button(screen, rect, labels[name], rect.collidepoint(mouse_pos), fonts)

    # app_title = fonts["status"].render("Magnetic Maze Control", True, TEXT)
    # app_title_rect = app_title.get_rect(center=(width // 2, TOP_BAR_HEIGHT // 2 + 1))
    # screen.blit(app_title, app_title_rect)

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
    size_text = fonts["status"].render(f"迷宫尺寸：{maze.cols} × {maze.rows}", True, STATUS_INFO)
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
    overlay.fill((30, 35, 45, 130))
    screen.blit(overlay, (0, 0))

    dialog, play_again, back_to_menu, close_game = build_victory_dialog_rects(width, height)
    pygame.draw.rect(screen, PANEL_ALT, dialog, border_radius=18)
    pygame.draw.rect(screen, GRID, dialog, width=2, border_radius=18)

    title = fonts["title"].render("到达终点！", True, ACCENT_HOVER)
    subtitle = fonts["body"].render(f"用时：{elapsed_time:0.2f} 秒", True, TEXT)
    tip = fonts["status"].render("可重玩本关、返回主菜单或关闭游戏。", True, STATUS_INFO)

    screen.blit(title, title.get_rect(center=(dialog.centerx, dialog.y + 60)))
    screen.blit(subtitle, subtitle.get_rect(center=(dialog.centerx, dialog.y + 118)))
    screen.blit(tip, tip.get_rect(center=(dialog.centerx, dialog.y + 158)))

    draw_button(screen, play_again, "再玩一次", play_again.collidepoint(mouse_pos), fonts)
    draw_button(screen, back_to_menu, "返回主菜单", back_to_menu.collidepoint(mouse_pos), fonts)
    draw_button(screen, close_game, "关闭游戏", close_game.collidepoint(mouse_pos), fonts)
    return dialog, play_again, back_to_menu, close_game
