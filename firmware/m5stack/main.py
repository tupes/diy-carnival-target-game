# SPDX-FileCopyrightText: 2026 Mark Tupala
# SPDX-License-Identifier: MIT

"""M5Stack touchscreen, score, timer, and audio controller."""

import _thread
import time
from m5stack import *
from uiflow import *
from libs.m5_espnow import M5ESPNOW

# GAME CONSTANTS
GAME_DURATION = 30  # seconds
GAME_OVER_DURATION = 5  # seconds
GAME_LOOP_DURATION = 0.05  # seconds
NUM_CLOWNS = 5
VALID_POINT_VALUES = (1, 2, 3)

# ESP-NOW CONSTANTS
ESPNOW_CHANNEL = 0
ESPNOW_STRING_DATA_TYPE = 1

# AUDIO CONSTANTS
SCORE_SOUND_PATH = "/flash/res/ding.wav"
SCORE_SOUND_VOLUME = 6
audio_lock = _thread.allocate_lock()

# GLOBAL STATE
high_score = 0


def parse_hit_message(message):
    """Parse and validate a ``<target_id>-<points>`` hit message."""
    if not isinstance(message, str):
        return None

    fields = message.split("-")
    if len(fields) != 2:
        return None

    try:
        clown_id = int(fields[0])
        points = int(fields[1])
    except ValueError:
        return None

    if not 0 <= clown_id < NUM_CLOWNS or points not in VALID_POINT_VALUES:
        return None

    return clown_id, points


class Game:
    def __init__(self, connection):
        self.connection = connection
        self.score = 0
        self.time_left = GAME_DURATION
        self.start_time = time.ticks_ms()
        self.active = True

        draw_game_screen(self)

    def update(self):
        """Update the countdown from an absolute start tick to avoid drift."""
        current_time = time.ticks_ms()
        elapsed_seconds = max(0, time.ticks_diff(current_time, self.start_time) // 1000)
        time_left = max(0, GAME_DURATION - elapsed_seconds)
        if time_left != self.time_left:
            self.time_left = time_left
            draw_time(time_left)

    def finish(self):
        """Prevent late ESP-NOW callbacks from mutating a completed round."""
        self.active = False

    def receive_message(self, _callback_source):
        try:
            received = self.connection.espnow_recv_str()
            if not self.active:
                return

            if not received or len(received) < 2:
                print("Ignoring empty ESP-NOW hit message")
                return

            hit = parse_hit_message(received[1])
            if hit is None:
                print("Ignoring invalid hit message:", received[1])
                return

            _clown_id, points = hit
            self.score += points
            draw_score(self.score)
            play_score_sound()
        except Exception as e:
            print("Error processing hit:", e)


def create_connection():
    connection = M5ESPNOW()
    connection.espnow_init(ESPNOW_CHANNEL, ESPNOW_STRING_DATA_TYPE)
    return connection


# --- UI Rendering Functions ---
def draw_start_screen(current_high_score):
    lcd.clear(lcd.BLACK)
    lcd.font(lcd.FONT_DejaVu40)

    # Split the neutral public-project title to keep the large font readable.
    lcd.print("CARNIVAL", 60, 20, lcd.CYAN)
    lcd.print("TARGETS", 80, 60, lcd.CYAN)

    # Draw High Score
    lcd.font(lcd.FONT_DejaVu24)
    lcd.print("HIGH SCORE: " + str(current_high_score), 70, 110, lcd.YELLOW)

    # Draw interactive touch boundary (visual only, entire screen is active)
    lcd.roundrect(60, 150, 200, 50, 10, lcd.GREEN, lcd.GREEN)
    lcd.font(lcd.FONT_DejaVu24)
    lcd.print("TAP TO START", 75, 163, lcd.BLACK)


def draw_game_screen(game):
    lcd.clear(lcd.BLACK)
    lcd.font(lcd.FONT_DejaVu24)
    lcd.print("TIME:", 10, 20, lcd.WHITE)
    lcd.print("SCORE:", 10, 100, lcd.WHITE)
    draw_time(game.time_left)
    draw_score(game.score)


def draw_time(time_left):
    lcd.fillRect(100, 15, 100, 40, lcd.BLACK)  # Clear previous rendering
    lcd.font(lcd.FONT_DejaVu40)
    color = lcd.WHITE if time_left > 10 else lcd.RED
    lcd.print(str(time_left), 100, 15, color)


def draw_score(score):
    lcd.fillRect(120, 95, 100, 40, lcd.BLACK)  # Clear previous rendering
    lcd.font(lcd.FONT_DejaVu40)
    lcd.print(str(score), 120, 95, lcd.YELLOW)


def start_button_pushed():
    if touch.status():
        pos = touch.read()
        x, y = pos[0], pos[1]
        print("Received a touch at position %d, %d" % (x, y))
        # The entire start screen is intentionally touch-active.
        print("Start button pressed")
        return True

    return False


def draw_game_over(score, current_high_score, is_new_high_score):
    lcd.clear(lcd.BLACK)
    lcd.font(lcd.FONT_DejaVu40)
    lcd.print("GAME OVER!", 50, 40, lcd.RED)

    lcd.font(lcd.FONT_DejaVu24)
    lcd.print("FINAL SCORE: " + str(score), 50, 100, lcd.WHITE)

    if is_new_high_score:
        lcd.print("NEW HIGH SCORE!", 45, 150, lcd.GREEN)
    else:
        lcd.print("HIGH SCORE: " + str(current_high_score), 50, 150, lcd.YELLOW)


def play_score_sound():
    """Start at most one score-sound thread at a time."""
    if not audio_lock.acquire(False):
        return

    def background_audio():
        try:
            speaker.playWAV(SCORE_SOUND_PATH, volume=SCORE_SOUND_VOLUME)
        except Exception as e:
            print("Audio error:", e)
        finally:
            audio_lock.release()

    try:
        _thread.start_new_thread(background_audio, ())
    except Exception as e:
        audio_lock.release()
        print("Unable to start audio thread:", e)


lcd.clear()
draw_start_screen(high_score)
print("Start screen initialized.")
connection = create_connection()
game = None

while True:
    if game is None and start_button_pushed():
        print("Starting new game")
        game = Game(connection)
        connection.espnow_recv_cb(game.receive_message)

        print("Broadcasting START message")
        connection.espnow_broadcast_data("START")
        time.sleep(0.5)  # Debounce touch input

    if game is not None:
        game.update()

        if game.time_left <= 0:
            game.finish()
            final_score = game.score
            is_new_high_score = final_score > high_score
            if is_new_high_score:
                high_score = final_score

            draw_game_over(final_score, high_score, is_new_high_score)
            print("Broadcasting GAME OVER message")
            connection.espnow_broadcast_data("GAME OVER")
            game = None

            time.sleep(GAME_OVER_DURATION)
            draw_start_screen(high_score)

    time.sleep(GAME_LOOP_DURATION)
