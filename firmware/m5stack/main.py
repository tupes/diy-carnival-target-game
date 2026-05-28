import time

from m5stack import *
from uiflow import *
from libs.m5_espnow import M5ESPNOW
import _thread

# GAME CONSTANTS
GAME_DURATION = 30 # seconds
GAME_OVER_DURATION = 5 # seconds
GAME_LOOP_DURATION = 0.05 # seconds

# GLOBAL STATE
high_score = 0

# GAME STATES
WAITING = 'waiting'
PLAYING = 'playing'
GAME_OVER = 'game over'

class Game:
    def __init__(self, connection):
        self.connection = connection
        self.score = 0
        self.time_left = GAME_DURATION
        self.last_tick = time.ticks_ms()
        
        draw_game_screen(self)
    
    def update(self):
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_tick) >= 1000:
            self.time_left -= 1
            self.last_tick = current_time
            draw_time(self.time_left)
    
    def receive_message(self, payload):
        print('Received message from backend')
        try:
            message = self.connection.espnow_recv_str()
            print("Received:", message)
            clown_id, value = message[1].split('-')
            self.score += int(value)
            draw_score(self.score)
            
            play_score_sound()
        except Exception as e:
            print("Error processing hit:", e)

def create_connection():
    connection = M5ESPNOW()
    connection.espnow_init(0, 1)
    return connection

# --- UI Rendering Functions ---
def draw_start_screen(current_high_score):
    lcd.clear(lcd.BLACK)
    lcd.font(lcd.FONT_DejaVu40)
    
    # Split the title to prevent wrapping while keeping the large font
    lcd.print("DOWN THE", 60, 20, lcd.CYAN)
    lcd.print("CLOWN!", 80, 60, lcd.CYAN)
    
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
    lcd.fillRect(100, 15, 100, 40, lcd.BLACK) # Clear previous rendering
    lcd.font(lcd.FONT_DejaVu40)
    color = lcd.WHITE if time_left > 10 else lcd.RED
    lcd.print(str(time_left), 100, 15, color)

def draw_score(score):
    lcd.fillRect(120, 95, 100, 40, lcd.BLACK) # Clear previous rendering
    lcd.font(lcd.FONT_DejaVu40)
    lcd.print(str(score), 120, 95, lcd.YELLOW)

def start_button_pushed():
    if touch.status():
        pos = touch.read()
        x, y = pos[0], pos[1]
        print("Received a touch at position %d, %d" % (x, y))
        # Removed coordinate constraints. Any tap registers as a start.
        print("Start button pressed")
        return True

    return False

def draw_game_over(score, current_high_score):
    lcd.clear(lcd.BLACK)
    lcd.font(lcd.FONT_DejaVu40)
    lcd.print("GAME OVER!", 50, 40, lcd.RED)
    
    lcd.font(lcd.FONT_DejaVu24)
    lcd.print("FINAL SCORE: " + str(score), 50, 100, lcd.WHITE)
    
    # Check if they beat the high score for a special message
    if score >= current_high_score and score > 0:
        lcd.print("NEW HIGH SCORE!", 45, 150, lcd.GREEN)
    else:
        lcd.print("HIGH SCORE: " + str(current_high_score), 50, 150, lcd.YELLOW)

def play_score_sound():
    def background_audio():
        try:
            speaker.playWAV('/flash/res/ding.wav', volume=6)
        except Exception as e:
            print("Audio error:", e)
            
    _thread.start_new_thread(background_audio, ())

lcd.clear()
draw_start_screen(high_score) # Pass initial high score
print("Start screen initialized.")
connection = create_connection()
game = None

while True:
    if not game and start_button_pushed():
        print('Starting new game')
        game = Game(connection)
        connection.espnow_recv_cb(game.receive_message)
        
        print('Broadcasting START message')
        connection.espnow_broadcast_data('START')
        time.sleep(0.5) # Debounce touch input
            
    if game:
        game.update()

        if game.time_left <= 0:
            # Update high score if the current game's score is higher
            if game.score > high_score:
                high_score = game.score
                
            draw_game_over(game.score, high_score)
            print('Broadcasting GAME OVER message')
            connection.espnow_broadcast_data('GAME OVER')
            game = None
            
            time.sleep(GAME_OVER_DURATION)
            draw_start_screen(high_score)
                
    time.sleep(GAME_LOOP_DURATION)