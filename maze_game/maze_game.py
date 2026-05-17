import random
import sys
import time
from collections import deque

import pygame
import serial
import serial.tools.list_ports


DEFAULT_WIDTH = 1560
DEFAULT_HEIGHT = 980
MIN_WIDTH = 1360
MIN_HEIGHT = 860

WIDTH = DEFAULT_WIDTH
HEIGHT = DEFAULT_HEIGHT
FPS = 60

BALL_RADIUS = 15
TRAIL_LIMIT = 80
TOP_BAR_HEIGHT = 48
DATA_PANEL_HEIGHT = 110

FILTER_ALPHA = 0.12
INPUT_SCALE = 0.03
DEAD_ZONE = 1.8
INPUT_CLAMP = 20.0
INPUT_EXPONENT = 1.65
MAX_SPEED = 4.0
VELOCITY_BLEND = 0.16
VELOCITY_DAMPING = 0.84

MAZE_COLS = 10
MAZE_ROWS = 6
CELL_SIZE = 96
WALL_THICKNESS = 18
MAZE_MARGIN_X = (WIDTH - MAZE_COLS * CELL_SIZE) // 2
MAZE_MARGIN_Y = TOP_BAR_HEIGHT + DATA_PANEL_HEIGHT + 24

BG = (8, 12, 20)
GRID = (20, 30, 45)
WALL = (0, 180, 255)
BALL = (255, 220, 100)
GOAL = (0, 255, 120)
TEXT = (220, 220, 220)
TRAIL = (255, 220, 100)
PANEL = (15, 22, 34)
PANEL_ALT = (20, 29, 44)
BUTTON = (24, 38, 59)
BUTTON_HOVER = (37, 99, 235)
BUTTON_TEXT = (245, 247, 250)
STATUS_OK = (125, 255, 160)
STATUS_INFO = (120, 205, 255)
STATUS_WARN = (255, 214, 102)


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Magnetic Maze Control")
clock = pygame.time.Clock()

font = pygame.font.Font(r"C:\Windows\Fonts\msyh.ttc", 32)
small_font = pygame.font.Font(r"C:\Windows\Fonts\consola.ttf", 24)
button_font = pygame.font.Font(r"C:\Windows\Fonts\msyh.ttc", 22)
status_font = pygame.font.Font(r"C:\Windows\Fonts\msyh.ttc", 20)


def select_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        desc = port.description.lower()
        if "arduino" in desc or "ch340" in desc or "usb serial" in desc:
            print(f"Auto connect: {port.device}")
            return port.device
    print("Arduino not found.")
    sys.exit()


def parse_line(line):
    try:
        decoded = line.decode("utf-8", errors="ignore").strip()
        if "ms:" not in decoded:
            return None
        parts = decoded.split()
        if len(parts) < 3:
            return None
        bx = float(parts[1])
        by = float(parts[2])
        return bx, by
    except Exception:
        return None


def calibrate_sensor(ser, duration=2.0):
    print("\nCalibrating, please keep the magnetic input still...")
    ser.reset_input_buffer()
    bx0 = 0.0
    by0 = 0.0
    count = 0
    start = time.time()

    while time.time() - start < duration:
        if not ser.in_waiting:
            continue
        result = parse_line(ser.readline())
        if result is None:
            continue
        bx, by = result
        bx0 += bx
        by0 += by
        count += 1

    if count == 0:
        print("Calibration skipped because no valid serial data was received.")
        return 0.0, 0.0

    bx0 /= count
    by0 /= count
    print(f"Calibration done: bx0={bx0:.2f}, by0={by0:.2f}")
    return bx0, by0


def build_button_rects():
    menu_top = 6
    menu_height = TOP_BAR_HEIGHT - 12
    button_width = 176
    gap = 12
    return {
        "new_maze": pygame.Rect(18, menu_top, button_width, menu_height),
        "recalibrate": pygame.Rect(18 + button_width + gap, menu_top, button_width, menu_height),
        "reset_ball": pygame.Rect(18 + (button_width + gap) * 2, menu_top, button_width, menu_height),
        "close": pygame.Rect(WIDTH - button_width - 18, menu_top, button_width, menu_height),
    }


def update_layout(window_width, window_height):
    global WIDTH, HEIGHT, MAZE_MARGIN_X, MAZE_MARGIN_Y

    WIDTH = max(window_width, MIN_WIDTH)
    HEIGHT = max(window_height, MIN_HEIGHT)

    MAZE_MARGIN_X = max((WIDTH - MAZE_COLS * CELL_SIZE) // 2, 24)

    content_top = TOP_BAR_HEIGHT + DATA_PANEL_HEIGHT + 24
    extra_vertical_space = HEIGHT - content_top - MAZE_ROWS * CELL_SIZE - 24
    MAZE_MARGIN_Y = content_top + max(extra_vertical_space // 2, 0)


def draw_button(rect, label, hovered):
    color = BUTTON_HOVER if hovered else BUTTON
    pygame.draw.rect(screen, color, rect, border_radius=10)
    text_surface = button_font.render(label, True, BUTTON_TEXT)
    text_rect = text_surface.get_rect(center=rect.center)
    screen.blit(text_surface, text_rect)


def recalibrate_to_current_signal(ser, duration=1.2):
    bx0, by0 = calibrate_sensor(ser, duration=duration)
    return bx0, by0, 0.0, 0.0, 0.0, 0.0


def cell_center(cell):
    row, col = cell
    x = MAZE_MARGIN_X + col * CELL_SIZE + CELL_SIZE // 2
    y = MAZE_MARGIN_Y + row * CELL_SIZE + CELL_SIZE // 2
    return x, y


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
        edge = tuple(sorted(((row, col), next_cell)))
        passages.add(edge)

    return passages


def is_maze_solvable(rows, cols, passages, start, goal):
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
            edge = tuple(sorted((current, neighbor)))
            if edge not in passages or neighbor in visited:
                continue
            visited.add(neighbor)
            queue.append(neighbor)

    return False


def build_wall_rects(rows, cols, passages):
    walls = []
    half = WALL_THICKNESS // 2
    left = MAZE_MARGIN_X
    top = MAZE_MARGIN_Y
    maze_width = cols * CELL_SIZE
    maze_height = rows * CELL_SIZE

    walls.append(pygame.Rect(left - half, top - half, maze_width + WALL_THICKNESS, WALL_THICKNESS))
    walls.append(pygame.Rect(left - half, top + maze_height - half, maze_width + WALL_THICKNESS, WALL_THICKNESS))
    walls.append(pygame.Rect(left - half, top - half, WALL_THICKNESS, maze_height + WALL_THICKNESS))
    walls.append(pygame.Rect(left + maze_width - half, top - half, WALL_THICKNESS, maze_height + WALL_THICKNESS))

    for row in range(rows):
        for col in range(cols - 1):
            a = (row, col)
            b = (row, col + 1)
            edge = tuple(sorted((a, b)))
            if edge in passages:
                continue
            x = left + (col + 1) * CELL_SIZE - half
            y = top + row * CELL_SIZE + half
            h = CELL_SIZE - WALL_THICKNESS
            walls.append(pygame.Rect(x, y, WALL_THICKNESS, h))

    for row in range(rows - 1):
        for col in range(cols):
            a = (row, col)
            b = (row + 1, col)
            edge = tuple(sorted((a, b)))
            if edge in passages:
                continue
            x = left + col * CELL_SIZE + half
            y = top + (row + 1) * CELL_SIZE - half
            w = CELL_SIZE - WALL_THICKNESS
            walls.append(pygame.Rect(x, y, w, WALL_THICKNESS))

    return walls


def create_maze():
    start = (0, 0)
    goal = (MAZE_ROWS - 1, MAZE_COLS - 1)

    for _ in range(50):
        passages = generate_passages(MAZE_ROWS, MAZE_COLS)
        if is_maze_solvable(MAZE_ROWS, MAZE_COLS, passages, start, goal):
            walls = build_wall_rects(MAZE_ROWS, MAZE_COLS, passages)
            return start, goal, walls

    raise RuntimeError("Failed to create a solvable maze.")


def shape_input(value):
    scaled_value = value * INPUT_SCALE
    magnitude = abs(scaled_value)
    if magnitude <= DEAD_ZONE:
        return 0.0

    effective = min(magnitude, INPUT_CLAMP) - DEAD_ZONE
    span = max(INPUT_CLAMP - DEAD_ZONE, 1e-6)
    normalized = effective / span
    curved = normalized ** INPUT_EXPONENT
    return MAX_SPEED * curved * (1 if scaled_value > 0 else -1)


def collides(ball_x, ball_y, walls):
    ball_rect = pygame.Rect(
        int(ball_x - BALL_RADIUS),
        int(ball_y - BALL_RADIUS),
        BALL_RADIUS * 2,
        BALL_RADIUS * 2,
    )
    return any(ball_rect.colliderect(wall) for wall in walls)


def move_ball(ball_x, ball_y, vx, vy, walls):
    next_x = ball_x + vx
    if not collides(next_x, ball_y, walls):
        ball_x = next_x
    else:
        vx = 0.0

    next_y = ball_y + vy
    if not collides(ball_x, next_y, walls):
        ball_y = next_y
    else:
        vy = 0.0

    return ball_x, ball_y, vx, vy


def reset_run(start_cell):
    x, y = cell_center(start_cell)
    return x, y, 0.0, 0.0, 0.0, 0.0, [], False


def generate_new_maze():
    start_cell, goal_cell, walls = create_maze()
    goal_rect = build_goal_rect(goal_cell)
    return start_cell, goal_cell, walls, goal_rect


def draw_data_panel(bx_filtered, by_filtered, bx0, by0, status_message, status_color, elapsed_time, timer_started, win):
    panel_rect = pygame.Rect(18, TOP_BAR_HEIGHT + 10, WIDTH - 36, DATA_PANEL_HEIGHT - 18)
    pygame.draw.rect(screen, PANEL_ALT, panel_rect, border_radius=14)
    pygame.draw.rect(screen, GRID, panel_rect, width=2, border_radius=14)

    title = status_font.render("Monitoring", True, TEXT)
    info1 = small_font.render(f"Bx = {bx_filtered:.0f}", True, TEXT)
    info2 = small_font.render(f"By = {by_filtered:.0f}", True, TEXT)
    info3 = small_font.render(
        f"scaled = ({bx_filtered * INPUT_SCALE:.2f}, {by_filtered * INPUT_SCALE:.2f})",
        True,
        TEXT,
    )
    info4 = small_font.render(
        f"baseline = ({bx0:.0f}, {by0:.0f})   dead zone = {DEAD_ZONE:.1f}   scale = {INPUT_SCALE:.3f}",
        True,
        TEXT,
    )
    if win:
        timer_text = f"timer = {format_elapsed(elapsed_time)}"
    elif timer_started:
        timer_text = f"timer = {format_elapsed(elapsed_time)}"
    else:
        timer_text = "timer = waiting for movement"
    info5 = small_font.render(timer_text, True, TEXT)
    status_surface = status_font.render(status_message, True, status_color)

    screen.blit(title, (panel_rect.x + 16, panel_rect.y + 10))
    screen.blit(status_surface, (panel_rect.x + 170, panel_rect.y + 12))
    screen.blit(info1, (panel_rect.x + 16, panel_rect.y + 42))
    screen.blit(info2, (panel_rect.x + 220, panel_rect.y + 42))
    screen.blit(info3, (panel_rect.x + 424, panel_rect.y + 42))
    screen.blit(info4, (panel_rect.x + 16, panel_rect.y + 72))
    screen.blit(info5, (panel_rect.x + 760, panel_rect.y + 72))


def build_goal_rect(goal_cell):
    goal_x, goal_y = cell_center(goal_cell)
    goal_rect = pygame.Rect(0, 0, 56, 56)
    goal_rect.center = (goal_x, goal_y)
    return goal_rect


def reset_timer_state():
    return False, None, 0.0


def format_elapsed(seconds):
    return f"{seconds:0.2f}s"


def shift_scene(dx, dy, walls, goal_rect, trail, ball_x, ball_y):
    shifted_walls = [wall.move(dx, dy) for wall in walls]
    shifted_goal = goal_rect.move(dx, dy)
    shifted_trail = [(x + dx, y + dy) for x, y in trail]
    return shifted_walls, shifted_goal, shifted_trail, ball_x + dx, ball_y + dy


def get_victory_dialog_rects():
    dialog = pygame.Rect(0, 0, 500, 270)
    dialog.center = (WIDTH // 2, HEIGHT // 2)
    play_again = pygame.Rect(dialog.x + 56, dialog.bottom - 64, 170, 44)
    close_game = pygame.Rect(dialog.right - 226, dialog.bottom - 64, 170, 44)
    return dialog, play_again, close_game


def draw_victory_dialog(elapsed_time, mouse_pos):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((5, 10, 18, 190))
    screen.blit(overlay, (0, 0))

    dialog, play_again, close_game = get_victory_dialog_rects()
    pygame.draw.rect(screen, PANEL_ALT, dialog, border_radius=18)
    pygame.draw.rect(screen, GRID, dialog, width=2, border_radius=18)

    title = font.render("Goal Reached!", True, (255, 255, 120))
    subtitle = status_font.render(f"Time: {format_elapsed(elapsed_time)}", True, TEXT)
    tip = status_font.render("Choose whether to play another round.", True, STATUS_INFO)

    title_rect = title.get_rect(center=(dialog.centerx, dialog.y + 60))
    subtitle_rect = subtitle.get_rect(center=(dialog.centerx, dialog.y + 114))
    tip_rect = tip.get_rect(center=(dialog.centerx, dialog.y + 154))

    screen.blit(title, title_rect)
    screen.blit(subtitle, subtitle_rect)
    screen.blit(tip, tip_rect)

    draw_button(play_again, "Play Again", play_again.collidepoint(mouse_pos))
    draw_button(close_game, "Close", close_game.collidepoint(mouse_pos))


port = select_port()
ser = serial.Serial(port, 115200, timeout=1)
print(f"\nSerial connected: {port}")
bx0, by0 = calibrate_sensor(ser)

update_layout(WIDTH, HEIGHT)
buttons = build_button_rects()
status_message = "Ready"
status_color = STATUS_INFO

start_cell, goal_cell, walls, goal_rect = generate_new_maze()
ball_x, ball_y, vx, vy, bx_filtered, by_filtered, trail, win = reset_run(start_cell)
timer_started, timer_start_time, elapsed_time = reset_timer_state()

running = True

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            old_margin_x = MAZE_MARGIN_X
            old_margin_y = MAZE_MARGIN_Y
            screen = pygame.display.set_mode(
                (max(event.w, MIN_WIDTH), max(event.h, MIN_HEIGHT)),
                pygame.RESIZABLE,
            )
            update_layout(event.w, event.h)
            buttons = build_button_rects()
            dx = MAZE_MARGIN_X - old_margin_x
            dy = MAZE_MARGIN_Y - old_margin_y
            walls, goal_rect, trail, ball_x, ball_y = shift_scene(
                dx,
                dy,
                walls,
                goal_rect,
                trail,
                ball_x,
                ball_y,
            )
        elif event.type == pygame.KEYDOWN:
            if win:
                if event.key == pygame.K_ESCAPE:
                    running = False
                continue
            if event.key == pygame.K_r:
                start_cell, goal_cell, walls, goal_rect = generate_new_maze()
                ball_x, ball_y, vx, vy, bx_filtered, by_filtered, trail, win = reset_run(start_cell)
                bx0, by0, bx_filtered, by_filtered, vx, vy = recalibrate_to_current_signal(ser, duration=1.2)
                timer_started, timer_start_time, elapsed_time = reset_timer_state()
                status_message = "New maze generated and recalibrated"
                status_color = STATUS_OK
            elif event.key == pygame.K_c:
                bx0, by0, bx_filtered, by_filtered, vx, vy = recalibrate_to_current_signal(ser, duration=1.2)
                status_message = f"Recalibrated here: bx0={bx0:.1f}, by0={by0:.1f}"
                status_color = STATUS_OK
            elif event.key == pygame.K_SPACE:
                ball_x, ball_y, vx, vy, bx_filtered, by_filtered, trail, win = reset_run(start_cell)
                timer_started, timer_start_time, elapsed_time = reset_timer_state()
                status_message = "Ball reset to start"
                status_color = STATUS_INFO
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if win:
                dialog, play_again, close_game = get_victory_dialog_rects()
                if play_again.collidepoint(mouse_pos):
                    start_cell, goal_cell, walls, goal_rect = generate_new_maze()
                    ball_x, ball_y, vx, vy, bx_filtered, by_filtered, trail, win = reset_run(start_cell)
                    bx0, by0, bx_filtered, by_filtered, vx, vy = recalibrate_to_current_signal(ser, duration=1.2)
                    timer_started, timer_start_time, elapsed_time = reset_timer_state()
                    status_message = "New round started"
                    status_color = STATUS_OK
                elif close_game.collidepoint(mouse_pos):
                    running = False
                continue
            if buttons["new_maze"].collidepoint(mouse_pos):
                start_cell, goal_cell, walls, goal_rect = generate_new_maze()
                ball_x, ball_y, vx, vy, bx_filtered, by_filtered, trail, win = reset_run(start_cell)
                bx0, by0, bx_filtered, by_filtered, vx, vy = recalibrate_to_current_signal(ser, duration=1.2)
                timer_started, timer_start_time, elapsed_time = reset_timer_state()
                status_message = "New maze generated and recalibrated"
                status_color = STATUS_OK
            elif buttons["recalibrate"].collidepoint(mouse_pos):
                bx0, by0, bx_filtered, by_filtered, vx, vy = recalibrate_to_current_signal(ser, duration=1.2)
                status_message = f"Recalibrated here: bx0={bx0:.1f}, by0={by0:.1f}"
                status_color = STATUS_OK
            elif buttons["reset_ball"].collidepoint(mouse_pos):
                ball_x, ball_y, vx, vy, bx_filtered, by_filtered, trail, win = reset_run(start_cell)
                timer_started, timer_start_time, elapsed_time = reset_timer_state()
                status_message = "Ball reset to start"
                status_color = STATUS_INFO
            elif buttons["close"].collidepoint(mouse_pos):
                running = False

    while ser.in_waiting:
        result = parse_line(ser.readline())
        if result is None:
            continue

        bx, by = result
        bx -= bx0
        by -= by0

        bx_filtered = (1 - FILTER_ALPHA) * bx_filtered + FILTER_ALPHA * bx
        by_filtered = (1 - FILTER_ALPHA) * by_filtered + FILTER_ALPHA * by

    target_vx = shape_input(bx_filtered)
    target_vy = -shape_input(by_filtered)

    if not win and not timer_started and (abs(target_vx) > 1e-6 or abs(target_vy) > 1e-6):
        timer_started = True
        timer_start_time = time.time()
        status_message = "Timer started"
        status_color = STATUS_WARN

    if not win:
        vx = vx * VELOCITY_DAMPING + target_vx * VELOCITY_BLEND
        vy = vy * VELOCITY_DAMPING + target_vy * VELOCITY_BLEND

        if abs(target_vx) < 1e-6:
            vx *= 0.86
        if abs(target_vy) < 1e-6:
            vy *= 0.86

        ball_x, ball_y, vx, vy = move_ball(ball_x, ball_y, vx, vy, walls)

        ball_x = max(BALL_RADIUS, min(WIDTH - BALL_RADIUS, ball_x))
        ball_y = max(BALL_RADIUS, min(HEIGHT - BALL_RADIUS, ball_y))

        trail.append((ball_x, ball_y))
        if len(trail) > TRAIL_LIMIT:
            trail.pop(0)

        if timer_started and timer_start_time is not None:
            elapsed_time = time.time() - timer_start_time

        if goal_rect.collidepoint(ball_x, ball_y):
            win = True
            vx = 0.0
            vy = 0.0
            if timer_started and timer_start_time is not None:
                elapsed_time = time.time() - timer_start_time
            status_message = f"Finished in {format_elapsed(elapsed_time)}"
            status_color = STATUS_OK

    mouse_pos = pygame.mouse.get_pos()

    screen.fill(BG)

    pygame.draw.rect(screen, PANEL, (0, 0, WIDTH, TOP_BAR_HEIGHT))
    pygame.draw.line(screen, GRID, (0, TOP_BAR_HEIGHT), (WIDTH, TOP_BAR_HEIGHT), 2)

    draw_button(buttons["new_maze"], "New Maze", buttons["new_maze"].collidepoint(mouse_pos))
    draw_button(buttons["recalibrate"], "Recalibrate", buttons["recalibrate"].collidepoint(mouse_pos))
    draw_button(buttons["reset_ball"], "Reset Ball", buttons["reset_ball"].collidepoint(mouse_pos))
    draw_button(buttons["close"], "Close", buttons["close"].collidepoint(mouse_pos))

    app_title = status_font.render("Magnetic Maze Control", True, TEXT)
    app_title_rect = app_title.get_rect(center=(WIDTH // 2, TOP_BAR_HEIGHT // 2 + 1))
    screen.blit(app_title, app_title_rect)

    draw_data_panel(
        bx_filtered,
        by_filtered,
        bx0,
        by0,
        status_message,
        status_color,
        elapsed_time,
        timer_started,
        win,
    )

    maze_top = MAZE_MARGIN_Y - 18
    maze_left = MAZE_MARGIN_X - 18
    maze_width = MAZE_COLS * CELL_SIZE + 36
    maze_height = MAZE_ROWS * CELL_SIZE + 36
    maze_panel = pygame.Rect(maze_left, maze_top, maze_width, maze_height)
    pygame.draw.rect(screen, PANEL_ALT, maze_panel, border_radius=16)
    pygame.draw.rect(screen, GRID, maze_panel, width=2, border_radius=16)

    for x in range(MAZE_MARGIN_X, MAZE_MARGIN_X + MAZE_COLS * CELL_SIZE + 1, 40):
        pygame.draw.line(screen, GRID, (x, MAZE_MARGIN_Y), (x, MAZE_MARGIN_Y + MAZE_ROWS * CELL_SIZE))
    for y in range(MAZE_MARGIN_Y, MAZE_MARGIN_Y + MAZE_ROWS * CELL_SIZE + 1, 40):
        pygame.draw.line(screen, GRID, (MAZE_MARGIN_X, y), (MAZE_MARGIN_X + MAZE_COLS * CELL_SIZE, y))

    for wall in walls:
        pygame.draw.rect(screen, WALL, wall, border_radius=6)

    pygame.draw.rect(screen, GOAL, goal_rect, border_radius=10)

    for i, point in enumerate(trail):
        alpha = i / max(len(trail), 1)
        radius = int(BALL_RADIUS * alpha)
        if radius > 0:
            pygame.draw.circle(screen, TRAIL, (int(point[0]), int(point[1])), radius, 1)

    pygame.draw.circle(screen, BALL, (int(ball_x), int(ball_y)), BALL_RADIUS)

    if win:
        draw_victory_dialog(elapsed_time, mouse_pos)

    pygame.display.flip()

ser.close()
pygame.quit()
