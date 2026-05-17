import os
import time

os.environ.setdefault("SDL_IME_SHOW_UI", "1")

import pygame

from config import (
    BALL_RADIUS,
    DEFAULT_HEIGHT,
    DEFAULT_MAZE_COLS,
    DEFAULT_MAZE_ROWS,
    DEFAULT_WIDTH,
    FILTER_ALPHA,
    FPS,
    INITIAL_CALIBRATION_DURATION,
    INPUT_CLAMP,
    INPUT_EXPONENT,
    INPUT_SCALE,
    MAX_MAZE_COLS,
    MAX_MAZE_ROWS,
    MAX_SPEED,
    MIN_HEIGHT,
    MIN_MAZE_COLS,
    MIN_MAZE_ROWS,
    MIN_WIDTH,
    QUICK_CALIBRATION_DURATION,
    STATUS_INFO,
    STATUS_OK,
    STATUS_WARN,
    TRAIL_LIMIT,
    VELOCITY_BLEND,
    VELOCITY_DAMPING,
    DEAD_ZONE,
)
from maze_logic import build_wall_rects, clone_maze, create_random_maze
from sensor_input import calibrate_sensor, open_serial_connection, parse_line
from storage import add_leaderboard_record, delete_maze_at, load_saved_mazes, normalize_saved_mazes, rename_maze_at, save_maze_copy
from ui import (
    build_game_buttons,
    build_game_viewport,
    build_goal_rect,
    build_start_screen_layout,
    build_victory_dialog_rects,
    cell_center,
    draw_game_screen,
    draw_start_screen,
    draw_victory_dialog,
    init_fonts,
    remap_point,
)


class MazeGameApp:
    def __init__(self):
        pygame.init()
        self.width = DEFAULT_WIDTH
        self.height = DEFAULT_HEIGHT
        self.display_flags = pygame.RESIZABLE | pygame.DOUBLEBUF
        self.screen = pygame.display.set_mode((self.width, self.height), self.display_flags)
        if hasattr(pygame.display, "set_window_minimum_size"):
            pygame.display.set_window_minimum_size(MIN_WIDTH, MIN_HEIGHT)
        pygame.display.set_caption("Magnetic Maze Control")
        self.clock = pygame.time.Clock()
        self.fonts = init_fonts()

        self.running = True
        self.mode = "start"

        self.ser = None
        self.bx0 = 0.0
        self.by0 = 0.0
        self.bx_filtered = 0.0
        self.by_filtered = 0.0

        self.saved_mazes = normalize_saved_mazes(load_saved_mazes())
        self.selected_saved_index = 0 if self.saved_mazes else None

        self.rows_setting = DEFAULT_MAZE_ROWS
        self.cols_setting = DEFAULT_MAZE_COLS
        self.preview_maze = create_random_maze(self.rows_setting, self.cols_setting)
        self.start_status = "Preview ready. Adjust size or load a saved maze."
        self.player_name = "Player1"
        self.text_input_mode = None
        self.text_input_buffer = ""
        self.text_input_original_value = ""
        self.ime_preview_text = ""
        self.pending_resize = None

        self.current_maze = None
        self.viewport = None
        self.goal_rect = None
        self.walls = []
        self.buttons, self.button_labels = build_game_buttons(self.width)
        self.game_status = "Ready"
        self.game_status_color = STATUS_INFO
        self.ball_x = 0.0
        self.ball_y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.trail = []
        self.win = False
        self.timer_started = False
        self.timer_start_time = None
        self.elapsed_time = 0.0

    def begin_text_input(self, mode, initial_value):
        self.text_input_mode = mode
        self.text_input_original_value = initial_value
        self.text_input_buffer = ""
        self.ime_preview_text = ""
        pygame.key.start_text_input()
        self.update_text_input_rect()

    def end_text_input(self):
        self.text_input_mode = None
        self.text_input_buffer = ""
        self.text_input_original_value = ""
        self.ime_preview_text = ""
        pygame.key.stop_text_input()

    def update_text_input_rect(self):
        if self.text_input_mode is None:
            return

        layout = build_start_screen_layout(self.width, self.height, len(self.saved_mazes))
        if self.text_input_mode == "player_name":
            rect = layout.buttons["player_name"]
        else:
            rect = layout.buttons["maze_name"]
        pygame.key.set_text_input_rect(rect)

    def commit_text_input(self):
        value = self.text_input_buffer.strip()
        if not value:
            value = self.text_input_original_value.strip()

        if self.text_input_mode == "player_name":
            self.player_name = value or "Player1"
            self.start_status = f"Player name set to {self.player_name}."
        elif self.text_input_mode == "maze_name":
            if self.selected_saved_index is None or not value:
                self.start_status = "Maze rename cancelled."
            else:
                self.saved_mazes, updated_maze = rename_maze_at(self.saved_mazes, self.selected_saved_index, value)
                if updated_maze is not None:
                    if self.preview_maze.maze_id == updated_maze.maze_id:
                        self.preview_maze = clone_maze(updated_maze)
                    if self.current_maze is not None and self.current_maze.maze_id == updated_maze.maze_id:
                        self.current_maze = clone_maze(updated_maze)
                    self.start_status = f"Renamed maze to {updated_maze.name}."
        self.end_text_input()

    def ensure_serial_ready(self, calibration_duration):
        if self.ser is None:
            self.ser = open_serial_connection()
        self.bx0, self.by0 = calibrate_sensor(self.ser, duration=calibration_duration)

    def reset_motion_filters(self):
        self.bx_filtered = 0.0
        self.by_filtered = 0.0
        self.vx = 0.0
        self.vy = 0.0

    def reset_timer(self):
        self.timer_started = False
        self.timer_start_time = None
        self.elapsed_time = 0.0

    def shape_input(self, value):
        scaled_value = value * INPUT_SCALE
        magnitude = abs(scaled_value)
        if magnitude <= DEAD_ZONE:
            return 0.0

        effective = min(magnitude, INPUT_CLAMP) - DEAD_ZONE
        span = max(INPUT_CLAMP - DEAD_ZONE, 1e-6)
        normalized = effective / span
        curved = normalized ** INPUT_EXPONENT
        return MAX_SPEED * curved * (1 if scaled_value > 0 else -1)

    def collides(self, ball_x, ball_y):
        ball_rect = pygame.Rect(
            int(ball_x - BALL_RADIUS),
            int(ball_y - BALL_RADIUS),
            BALL_RADIUS * 2,
            BALL_RADIUS * 2,
        )
        return any(ball_rect.colliderect(wall) for wall in self.walls)

    def ball_touches_goal(self):
        ball_rect = pygame.Rect(
            int(self.ball_x - BALL_RADIUS),
            int(self.ball_y - BALL_RADIUS),
            BALL_RADIUS * 2,
            BALL_RADIUS * 2,
        )
        return ball_rect.colliderect(self.goal_rect)

    def move_ball(self):
        next_x = self.ball_x + self.vx
        if not self.collides(next_x, self.ball_y):
            self.ball_x = next_x
        else:
            self.vx = 0.0

        next_y = self.ball_y + self.vy
        if not self.collides(self.ball_x, next_y):
            self.ball_y = next_y
        else:
            self.vy = 0.0

    def rebuild_game_geometry(self, preserve_motion=False):
        old_viewport = self.viewport
        old_ball = (self.ball_x, self.ball_y)
        old_trail = list(self.trail)

        self.viewport = build_game_viewport(
            self.width,
            self.height,
            self.current_maze.rows,
            self.current_maze.cols,
        )
        self.goal_rect = build_goal_rect(self.current_maze.goal, self.viewport)
        self.walls = build_wall_rects(self.current_maze, self.viewport)
        self.buttons, self.button_labels = build_game_buttons(self.width)

        if preserve_motion and old_viewport is not None:
            self.ball_x, self.ball_y = remap_point(
                old_ball[0],
                old_ball[1],
                old_viewport,
                self.viewport,
            )
            self.trail = [
                remap_point(x, y, old_viewport, self.viewport)
                for x, y in old_trail
            ]
        else:
            self.ball_x, self.ball_y = cell_center(self.current_maze.start, self.viewport)
            self.trail = []

    def apply_current_maze(self, maze, calibrate_duration, status_message):
        self.current_maze = clone_maze(maze)
        self.rows_setting = self.current_maze.rows
        self.cols_setting = self.current_maze.cols
        self.preview_maze = clone_maze(maze)
        self.rebuild_game_geometry(preserve_motion=False)
        self.ensure_serial_ready(calibrate_duration)
        self.reset_motion_filters()
        self.reset_timer()
        self.win = False
        self.game_status = status_message
        self.game_status_color = STATUS_OK

    def start_game(self):
        self.apply_current_maze(
            self.preview_maze,
            INITIAL_CALIBRATION_DURATION,
            "Maze loaded and calibrated.",
        )
        self.mode = "game"

    def generate_preview(self):
        self.preview_maze = create_random_maze(self.rows_setting, self.cols_setting)
        self.start_status = f"Generated a new {self.cols_setting} x {self.rows_setting} preview maze."

    def save_preview_maze(self):
        self.saved_mazes, saved_maze = save_maze_copy(self.saved_mazes, self.preview_maze)
        self.preview_maze = clone_maze(saved_maze)
        self.selected_saved_index = next(
            (index for index, maze in enumerate(self.saved_mazes) if maze.maze_id == saved_maze.maze_id),
            self.selected_saved_index,
        )
        self.start_status = f"Saved preview as {saved_maze.name}."

    def load_selected_saved_maze(self):
        if self.selected_saved_index is None or not self.saved_mazes:
            self.start_status = "Select a saved maze first."
            return

        self.preview_maze = clone_maze(self.saved_mazes[self.selected_saved_index])
        self.rows_setting = self.preview_maze.rows
        self.cols_setting = self.preview_maze.cols
        self.start_status = f"Loaded {self.preview_maze.name} into preview."

    def delete_selected_saved_maze(self):
        if self.selected_saved_index is None or not self.saved_mazes:
            self.start_status = "No saved maze selected."
            return

        self.saved_mazes, deleted_name = delete_maze_at(self.saved_mazes, self.selected_saved_index)
        self.selected_saved_index = 0 if self.saved_mazes else None
        self.start_status = f"Deleted {deleted_name}."

    def save_current_game_maze(self):
        self.saved_mazes, saved_maze = save_maze_copy(self.saved_mazes, self.current_maze)
        self.current_maze = clone_maze(saved_maze)
        self.preview_maze = clone_maze(saved_maze)
        self.selected_saved_index = next(
            (index for index, maze in enumerate(self.saved_mazes) if maze.maze_id == saved_maze.maze_id),
            self.selected_saved_index,
        )
        self.game_status = f"Saved current maze as {saved_maze.name}."
        self.game_status_color = STATUS_OK

    def generate_new_game_maze(self):
        maze = create_random_maze(self.current_maze.rows, self.current_maze.cols)
        self.apply_current_maze(maze, QUICK_CALIBRATION_DURATION, "Random maze generated and calibrated.")

    def recalibrate_current_signal(self):
        self.ensure_serial_ready(QUICK_CALIBRATION_DURATION)
        self.reset_motion_filters()
        self.game_status = f"Recalibrated here: bx0={self.bx0:.1f}, by0={self.by0:.1f}"
        self.game_status_color = STATUS_OK

    def reset_ball_to_start(self):
        self.ball_x, self.ball_y = cell_center(self.current_maze.start, self.viewport)
        self.trail = []
        self.vx = 0.0
        self.vy = 0.0
        self.reset_timer()
        self.win = False
        self.game_status = "Ball reset to start."
        self.game_status_color = STATUS_INFO

    def return_to_start_menu(self):
        self.mode = "start"
        self.preview_maze = clone_maze(self.current_maze)
        self.rows_setting = self.current_maze.rows
        self.cols_setting = self.current_maze.cols
        if self.current_maze.maze_id:
            self.selected_saved_index = next(
                (index for index, maze in enumerate(self.saved_mazes) if maze.maze_id == self.current_maze.maze_id),
                self.selected_saved_index,
            )
        self.start_status = "Returned to the setup screen with the current maze loaded."

    def replay_current_maze(self):
        self.rebuild_game_geometry(preserve_motion=False)
        self.ensure_serial_ready(QUICK_CALIBRATION_DURATION)
        self.reset_motion_filters()
        self.reset_timer()
        self.win = False
        self.game_status = "Replay started."
        self.game_status_color = STATUS_OK

    def record_current_result(self):
        if self.current_maze is None or not self.current_maze.maze_id:
            self.game_status = f"Finished in {self.elapsed_time:0.2f}s. Save this maze to enable leaderboard records."
            self.game_status_color = STATUS_WARN
            return

        player_name = self.player_name.strip() or "Player1"
        self.saved_mazes, updated_maze = add_leaderboard_record(
            self.saved_mazes,
            self.current_maze.maze_id,
            player_name,
            self.elapsed_time,
        )
        if updated_maze is None:
            self.saved_mazes, saved_maze = save_maze_copy(self.saved_mazes, self.current_maze, self.current_maze.name)
            self.current_maze = clone_maze(saved_maze)
            self.preview_maze = clone_maze(saved_maze)
            self.saved_mazes, updated_maze = add_leaderboard_record(
                self.saved_mazes,
                self.current_maze.maze_id,
                player_name,
                self.elapsed_time,
            )
        if updated_maze is not None:
            self.current_maze = clone_maze(updated_maze)
            if self.preview_maze.maze_id == updated_maze.maze_id:
                self.preview_maze = clone_maze(updated_maze)
            self.selected_saved_index = next(
                (index for index, maze in enumerate(self.saved_mazes) if maze.maze_id == updated_maze.maze_id),
                self.selected_saved_index,
            )
            self.game_status = f"{player_name} finished in {self.elapsed_time:0.2f}s. Leaderboard updated."
            self.game_status_color = STATUS_OK

    def resize_window(self, new_width, new_height):
        current_surface = pygame.display.get_surface()
        if current_surface is not None:
            self.screen = current_surface
            surface_width, surface_height = self.screen.get_size()
            self.width = surface_width
            self.height = surface_height
        else:
            self.width = new_width
            self.height = new_height
        self.buttons, self.button_labels = build_game_buttons(self.width)
        if self.text_input_mode is not None:
            self.update_text_input_rect()

        if self.mode == "game" and self.current_maze is not None:
            self.rebuild_game_geometry(preserve_motion=True)

    def handle_start_click(self, mouse_pos):
        layout = build_start_screen_layout(self.width, self.height, len(self.saved_mazes))
        if self.selected_saved_index is not None and layout.buttons["maze_name"].collidepoint(mouse_pos):
            selected_maze = self.saved_mazes[self.selected_saved_index]
            self.begin_text_input("maze_name", selected_maze.name)
            self.start_status = "Editing maze name. Press Enter to save."
            return

        for index, rect in layout.saved_item_rects:
            if rect.collidepoint(mouse_pos):
                self.selected_saved_index = index
                self.start_status = f"Selected saved maze: {self.saved_mazes[index].name}"
                return

        buttons = layout.buttons
        if buttons["player_name"].collidepoint(mouse_pos):
            self.begin_text_input("player_name", self.player_name)
        elif buttons["rows_minus"].collidepoint(mouse_pos):
            self.rows_setting = max(self.rows_setting - 1, MIN_MAZE_ROWS)
            self.start_status = f"Rows set to {self.rows_setting}. Generate a new maze to apply it."
        elif buttons["rows_plus"].collidepoint(mouse_pos):
            self.rows_setting = min(self.rows_setting + 1, MAX_MAZE_ROWS)
            self.start_status = f"Rows set to {self.rows_setting}. Generate a new maze to apply it."
        elif buttons["cols_minus"].collidepoint(mouse_pos):
            self.cols_setting = max(self.cols_setting - 1, MIN_MAZE_COLS)
            self.start_status = f"Cols set to {self.cols_setting}. Generate a new maze to apply it."
        elif buttons["cols_plus"].collidepoint(mouse_pos):
            self.cols_setting = min(self.cols_setting + 1, MAX_MAZE_COLS)
            self.start_status = f"Cols set to {self.cols_setting}. Generate a new maze to apply it."
        elif buttons["generate"].collidepoint(mouse_pos):
            self.generate_preview()
        elif buttons["play"].collidepoint(mouse_pos):
            self.start_game()
        elif buttons["save_preview"].collidepoint(mouse_pos):
            self.save_preview_maze()
        elif buttons["load_saved"].collidepoint(mouse_pos):
            self.load_selected_saved_maze()
        elif buttons["delete_saved"].collidepoint(mouse_pos):
            self.delete_selected_saved_maze()
        elif buttons["close"].collidepoint(mouse_pos):
            self.running = False

    def handle_game_click(self, mouse_pos):
        if self.win:
            _, play_again, back_to_menu, close_game = build_victory_dialog_rects(self.width, self.height)
            if play_again.collidepoint(mouse_pos):
                self.replay_current_maze()
            elif back_to_menu.collidepoint(mouse_pos):
                self.return_to_start_menu()
            elif close_game.collidepoint(mouse_pos):
                self.running = False
            return

        for name, rect in self.buttons.items():
            if not rect.collidepoint(mouse_pos):
                continue

            if name == "menu":
                self.return_to_start_menu()
            elif name == "save_maze":
                self.save_current_game_maze()
            elif name == "new_maze":
                self.generate_new_game_maze()
            elif name == "recalibrate":
                self.recalibrate_current_signal()
            elif name == "reset_ball":
                self.reset_ball_to_start()
            elif name == "close":
                self.running = False
            return

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.pending_resize = (event.w, event.h)
            elif event.type == pygame.TEXTINPUT:
                if self.text_input_mode is not None and event.text:
                    self.text_input_buffer += event.text
                    self.ime_preview_text = ""
            elif event.type == pygame.TEXTEDITING:
                if self.text_input_mode is not None:
                    self.ime_preview_text = event.text
            elif event.type == pygame.KEYDOWN:
                if self.text_input_mode is not None:
                    if event.key == pygame.K_RETURN:
                        self.commit_text_input()
                    elif event.key == pygame.K_ESCAPE:
                        self.end_text_input()
                        self.start_status = "Text edit cancelled."
                    elif event.key == pygame.K_BACKSPACE:
                        self.text_input_buffer = self.text_input_buffer[:-1]
                        self.ime_preview_text = ""
                    continue

                if self.mode == "start":
                    if event.key == pygame.K_F2 and self.selected_saved_index is not None:
                        selected_maze = self.saved_mazes[self.selected_saved_index]
                        self.begin_text_input("maze_name", selected_maze.name)
                        self.start_status = "Editing maze name. Press Enter to save."
                    elif event.key == pygame.K_RETURN:
                        self.start_game()
                    elif event.key == pygame.K_g:
                        self.generate_preview()
                    elif event.key == pygame.K_s:
                        self.save_preview_maze()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                else:
                    if self.win:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_RETURN:
                            self.replay_current_maze()
                        elif event.key == pygame.K_m:
                            self.return_to_start_menu()
                        continue

                    if event.key == pygame.K_F2 and self.current_maze is not None and self.current_maze.maze_id:
                        current_index = next(
                            (index for index, maze in enumerate(self.saved_mazes) if maze.maze_id == self.current_maze.maze_id),
                            None,
                        )
                        if current_index is not None:
                            self.selected_saved_index = current_index
                            self.mode = "start"
                            self.preview_maze = clone_maze(self.current_maze)
                            self.begin_text_input("maze_name", self.current_maze.name)
                            self.start_status = "Editing current saved maze name. Press Enter to save."
                    elif event.key == pygame.K_r:
                        self.generate_new_game_maze()
                    elif event.key == pygame.K_c:
                        self.recalibrate_current_signal()
                    elif event.key == pygame.K_SPACE:
                        self.reset_ball_to_start()
                    elif event.key == pygame.K_s:
                        self.save_current_game_maze()
                    elif event.key == pygame.K_m:
                        self.return_to_start_menu()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.mode == "start":
                    self.handle_start_click(event.pos)
                else:
                    self.handle_game_click(event.pos)

        if self.pending_resize is not None:
            resize_w, resize_h = self.pending_resize
            self.pending_resize = None
            self.resize_window(resize_w, resize_h)

    def update_sensor_stream(self):
        if self.ser is None:
            return

        while self.ser.in_waiting:
            result = parse_line(self.ser.readline())
            if result is None:
                continue

            bx, by = result
            bx -= self.bx0
            by -= self.by0

            self.bx_filtered = (1 - FILTER_ALPHA) * self.bx_filtered + FILTER_ALPHA * bx
            self.by_filtered = (1 - FILTER_ALPHA) * self.by_filtered + FILTER_ALPHA * by

    def update_game(self):
        if self.mode != "game" or self.current_maze is None:
            return

        self.update_sensor_stream()

        if self.win:
            return

        target_vx = self.shape_input(self.bx_filtered)
        target_vy = -self.shape_input(self.by_filtered)

        if not self.timer_started and (abs(target_vx) > 1e-6 or abs(target_vy) > 1e-6):
            self.timer_started = True
            self.timer_start_time = time.time()
            self.game_status = "Timer started."
            self.game_status_color = STATUS_WARN

        self.vx = self.vx * VELOCITY_DAMPING + target_vx * VELOCITY_BLEND
        self.vy = self.vy * VELOCITY_DAMPING + target_vy * VELOCITY_BLEND

        if abs(target_vx) < 1e-6:
            self.vx *= 0.86
        if abs(target_vy) < 1e-6:
            self.vy *= 0.86

        self.move_ball()

        self.ball_x = max(BALL_RADIUS, min(self.width - BALL_RADIUS, self.ball_x))
        self.ball_y = max(BALL_RADIUS, min(self.height - BALL_RADIUS, self.ball_y))

        self.trail.append((self.ball_x, self.ball_y))
        if len(self.trail) > TRAIL_LIMIT:
            self.trail.pop(0)

        if self.timer_started and self.timer_start_time is not None:
            self.elapsed_time = time.time() - self.timer_start_time

        if self.ball_touches_goal():
            self.win = True
            self.vx = 0.0
            self.vy = 0.0
            self.record_current_result()

    def draw(self):
        mouse_pos = pygame.mouse.get_pos()

        if self.mode == "start":
            draw_start_screen(
                self.screen,
                self.fonts,
                self.width,
                self.height,
                self.preview_maze,
                self.rows_setting,
                self.cols_setting,
                self.saved_mazes,
                self.selected_saved_index,
                self.start_status,
                mouse_pos,
                self.text_input_buffer if self.text_input_mode == "player_name" else self.player_name,
                self.text_input_mode == "player_name",
                self.text_input_mode == "maze_name",
                self.text_input_buffer if self.text_input_mode == "maze_name" else "",
                self.ime_preview_text,
                self.text_input_original_value,
            )
        else:
            self.walls = draw_game_screen(
                self.screen,
                self.fonts,
                self.width,
                self.height,
                self.buttons,
                self.button_labels,
                self.current_maze,
                self.viewport,
                self.goal_rect,
                self.trail,
                (self.ball_x, self.ball_y),
                self.bx_filtered,
                self.by_filtered,
                self.bx0,
                self.by0,
                self.game_status,
                self.game_status_color,
                self.elapsed_time,
                self.timer_started,
                mouse_pos,
            )
            if self.win:
                draw_victory_dialog(
                    self.screen,
                    self.fonts,
                    self.width,
                    self.height,
                    self.elapsed_time,
                    mouse_pos,
                )

        pygame.display.flip()

    def close(self):
        if self.ser is not None:
            self.ser.close()
        pygame.quit()

    def run(self):
        try:
            while self.running:
                self.clock.tick(FPS)
                self.handle_events()
                self.update_game()
                self.draw()
        finally:
            self.close()


if __name__ == "__main__":
    MazeGameApp().run()
