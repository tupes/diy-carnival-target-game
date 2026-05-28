import network
import espnow
import time
import random
import machine
from machine import Pin, PWM, SoftSPI
import uasyncio as asyncio

# SERVO CONSTANTS
SERVO_DOWN_ANGLE = 40
SERVO_UP_ANGLE = 115
SERVO_FREQUENCY = 50
SERVO_WAIT_DURATION = 0.5 # seconds

# NETWORK CONSTANTS
BROADCAST_MAC = b'\xff\xff\xff\xff\xff\xff'
AWAIT_MESSAGE_DURATION = 100 # ms
 
# CLOWN CONSTANTS
NUM_CLOWNS = 4

# LIGHT CONSTANTS
LIGHT_SPACING = 1
GREEN = [0, 255, 0]
YELLOW = [255, 255, 0]
RED = [255, 0, 0]
OFF = [0, 0, 0]
NUM_TOTAL_LEDS = NUM_CLOWNS
led_buffer = bytearray((NUM_TOTAL_LEDS) * 3)

HARDWARE_MAP = [
    { 'switch': 18, 'servo': 14, 'light': 0 * LIGHT_SPACING },
    { 'switch': 23, 'servo': 27, 'light': 1 * LIGHT_SPACING },
    { 'switch': 19, 'servo': 26, 'light': 2 * LIGHT_SPACING },
    { 'switch': 22, 'servo': 25, 'light': 3 * LIGHT_SPACING },
    { 'switch': 21, 'servo': 33, 'light': 4 * LIGHT_SPACING },
    { 'switch': 37, 'servo': 32, 'light': 5 * LIGHT_SPACING },
]

EASY, MEDIUM, HARD = 'easy', 'medium', 'hard'
CLOWN_DIFFICULTY = [EASY, EASY, MEDIUM, MEDIUM, HARD, HARD]
DIFFICULTY_VALUES = {
    EASY: { 'points': 1, 'color': GREEN },
    MEDIUM: { 'points': 2, 'color': YELLOW },
    HARD: { 'points': 3, 'color': RED },
}

# GAME CONSTANTS
CLOWN_RESET_DURATION = 2000 # ms
CLOWN_REROLL_DURATION = 5000 # ms
GAME_LOOP_DURATION = 0.05 # seconds

# GAME STATES
WAITING = 'waiting'
PLAYING = 'playing'

class Clown:
    def __init__(self, clown_id):
        self.id = clown_id
        
        hardware = HARDWARE_MAP[self.id]
        self.switch = Pin(hardware['switch'], Pin.IN, Pin.PULL_UP)
        self.servo = PWM(Pin(hardware['servo']), freq=SERVO_FREQUENCY)
        self.light_id = hardware['light']
        
        self.is_down = False
        self.needs_broadcast = False
        self.time_hit = 0
        
        #self.turn_light_off()
        
        #self.servo.duty(SERVO_DOWN_ANGLE)
        
        random_age = random.randint(0, int(CLOWN_REROLL_DURATION / 2))
        self.last_roll_time = time.ticks_ms() - random_age
        
        self.apply_new_difficulty()
        self.stand_up()
        #asyncio.create_task(self.stand_up())
        self.turn_light_on()
    
        self.switch.irq(trigger=Pin.IRQ_FALLING, handler=self.hit)

    def apply_new_difficulty(self):
        """Calculates new stats and updates the point/color values."""
        self.difficulty = roll_difficulty(self.id)
        self.points = DIFFICULTY_VALUES[self.difficulty]['points']
        self.color = DIFFICULTY_VALUES[self.difficulty]['color']

    def set_arm_down(self):
        self.servo.duty(SERVO_DOWN_ANGLE) 

    def set_arm_up(self):
        self.servo.duty(SERVO_UP_ANGLE)
    
    def stand_up(self):
        print(f"Standing up Clown {self.id}")
        self.set_arm_up()
        time.sleep(SERVO_WAIT_DURATION)           # Wait for mechanical movement
        #await asyncio.sleep_ms(SERVO_WAIT_DURATION)
        self.set_arm_down()      # Hide arm away from impact zone

    def turn_light_on(self):
        #print(f"Turning light on for Clown {self.id} with color {self.color}")
        set_single_light(self.light_id, self.color)

    def turn_light_off(self):
        #print(f"Turning light off for Clown {self.id}")
        set_single_light(self.light_id, OFF)

    def hit(self, pin):
        # If we check the pin right now and it's already back to 1 (HIGH),
        # it was a ghost signal. Ignore it immediately!
        if pin.value() == 1:
            #print(f"In Clown {self.id} hit handler but the it's already back to HIGH")
            return
        
        if not self.is_down:
            print(f"Clown {self.id} hit!")
            
            self.is_down = True
            self.time_hit = time.ticks_ms()
            self.needs_broadcast = True
            #self.turn_light_off()
        else:
            print(f"Clown {self.id} hit but is already down!")
    
    def reset(self):
        #print(f"Resetting Clown {self.id}")
        
        self.apply_new_difficulty()
        
        #asyncio.create_task(self.stand_up())
        self.stand_up()
        self.turn_light_on()
        
        self.is_down = False
        self.time_hit = 0
        self.last_roll_time = time.ticks_ms()

    def destroy(self):
        print(f"Destroying Clown {self.id}")
        
        # Unbind the hardware interrupt to allow garbage collection
        self.switch.irq(handler=None)
        
        self.turn_light_off()
        #asyncio.create_task(self.stand_up())
        self.stand_up()


def create_network_connection():
    # Turn on the WiFi antenna, but disconnect from any routers
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.disconnect()

    # Turn on the ESP-NOW protocol
    connection = espnow.ESPNow()
    connection.active(True)
    
    connection.add_peer(BROADCAST_MAC)
    print("Network connection ready! Listening for commands...")
    return connection


def push_led_data():
    """Sends the current state of the led_buffer to the physical strip."""
    #print(f"Writing to LED buffer: {led_buffer}")
    state = machine.disable_irq() 
    
    # 2. Blast the SPI data uninterrupted
    spi.write(led_buffer) 
    
    # 3. Turn the interrupts back on so ESP-NOW can work again
    machine.enable_irq(state) 
    
    time.sleep(0.01)

def set_single_light(light_index, color):
    """Updates a specific LED in the buffer and pushes the change."""
    # Calculate exactly where in the bytearray this LED's 3 colors start
    #print(f"Length of bytearray: {len(led_buffer)}")
    start_idx = (light_index * 3)
    
    # Update the Red, Green, and Blue bytes
    led_buffer[start_idx] = color[0]
    led_buffer[start_idx + 1] = color[1]
    led_buffer[start_idx + 2] = color[2]
    
    # Push the updated array to the lights
    push_led_data()

def initialize_lights():
    for i in range(len(led_buffer)):
        led_buffer[i] = 0
    
    push_led_data()

spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=Pin(13), mosi=Pin(4), miso=Pin(12))
initialize_lights()

def roll_difficulty(clown_id):
    roll = random.randint(1, 100) # Roll a 100-sided die
    #print(f"Rolled a {roll} for Clown {clown_id}")
    if clown_id in [0, 1]:  # Clowns 1 and 2
        if roll <= 75:
            return EASY
        else:
            return MEDIUM
            
    elif clown_id in [2, 3]: # Clowns 3 and 4
        if roll <= 25:
            return EASY
        elif roll <= 75:     # 25% to 75% covers the 50% spread
            return MEDIUM
        else:
            return HARD
            
    elif clown_id in [4, 5]: # Clowns 5 and 6
        if roll <= 25:
            return MEDIUM
        else:
            return HARD

connection = create_network_connection()
clowns = []
state = WAITING

print('Device initialized and awaiting START command')

while True:
    host, message = connection.recv(timeout_ms=AWAIT_MESSAGE_DURATION) # Check for messages
    
    if message:
        # Decode the message from bytes to a standard string
        command = message.decode('utf-8') 
        print(f"Received command: {command}")
    else:
        command = None
    
    if state == WAITING:            
        if command == 'START':
            print("Starting new game")
            for clown_id in range(NUM_CLOWNS):
                clowns.append(Clown(clown_id))
                time.sleep_ms(300)
            
            state = PLAYING
        elif command:
            print(f"Received invalid command {command} while in WAITING state")
                    
    elif state == PLAYING:            
        if command == 'GAME OVER':
            print("Ending game")
            for clown in clowns:
                clown.destroy()
            clowns = []
            
            state = WAITING
            continue
        elif command:
            print(f"Received invalid command {command} while in PLAYING state")
        
        current_time = time.ticks_ms()
        
        for clown in clowns:
            if clown.is_down:
                if clown.needs_broadcast:
                    connection.send(BROADCAST_MAC, str(clown.id).encode('utf-8') + '-' + str(clown.points).encode('utf-8'))
                    clown.needs_broadcast = False
                if time.ticks_diff(current_time, clown.time_hit) >= CLOWN_RESET_DURATION:
                    clown.reset()
                    #time.sleep_ms(300)
            else:
                if time.ticks_diff(current_time, clown.last_roll_time) >= CLOWN_REROLL_DURATION:
                    #print(f"Rerolling Clown {clown.id}")
                    clown.apply_new_difficulty()   
                    clown.turn_light_on()        
                    clown.last_roll_time = current_time
        
    time.sleep(GAME_LOOP_DURATION)
