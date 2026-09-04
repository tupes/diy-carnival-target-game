# SPDX-FileCopyrightText: 2026 Mark Tupala
# SPDX-License-Identifier: MIT

"""ESP32 target controller for the DIY carnival target game."""

import espnow
import machine
import network
import random
import time
from machine import Pin, PWM, SoftSPI

# SERVO CONSTANTS
SERVO_DOWN_DUTY = 40
SERVO_UP_DUTY = 115
SERVO_FREQUENCY = 50
SERVO_WAIT_DURATION = 0.5  # seconds

# NETWORK CONSTANTS
BROADCAST_MAC = b"\xff\xff\xff\xff\xff\xff"
RECEIVE_TIMEOUT_MS = 100
START_COMMAND = b"START"
GAME_OVER_COMMAND = b"GAME OVER"

# CLOWN CONSTANTS
NUM_CLOWNS = 5

# LIGHT CONSTANTS
SPI_CLOCK_PIN = 13
SPI_DATA_PIN = 4
SPI_UNUSED_MISO_PIN = 12
SPI_BAUDRATE = 100_000
LIGHT_SPACING = 1
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
OFF = (0, 0, 0)

HARDWARE_MAP = [
    {"switch": 18, "servo": 14, "light": 0 * LIGHT_SPACING},
    {"switch": 23, "servo": 27, "light": 1 * LIGHT_SPACING},
    {"switch": 19, "servo": 26, "light": 2 * LIGHT_SPACING},
    {"switch": 22, "servo": 25, "light": 3 * LIGHT_SPACING},
    {"switch": 21, "servo": 33, "light": 4 * LIGHT_SPACING},
    {"switch": 37, "servo": 32, "light": 5 * LIGHT_SPACING},
]

if not 0 < NUM_CLOWNS <= len(HARDWARE_MAP):
    raise ValueError("NUM_CLOWNS must select at least one configured target")

NUM_TOTAL_LEDS = max(hardware["light"] for hardware in HARDWARE_MAP[:NUM_CLOWNS]) + 1
led_buffer = bytearray(NUM_TOTAL_LEDS * 3)

EASY, MEDIUM, HARD = "easy", "medium", "hard"
DIFFICULTY_VALUES = {
    EASY: {"points": 1, "color": GREEN},
    MEDIUM: {"points": 2, "color": YELLOW},
    HARD: {"points": 3, "color": RED},
}

# GAME CONSTANTS
CLOWN_RESET_DURATION = 2000  # ms
CLOWN_REROLL_DURATION = 5000  # ms
GAME_LOOP_DURATION = 0.05  # seconds

# GAME STATES
WAITING = "waiting"
PLAYING = "playing"


class Clown:
    def __init__(self, clown_id):
        self.id = clown_id
        self.switch = None
        self.servo = None

        try:
            hardware = HARDWARE_MAP[self.id]
            self.switch = Pin(hardware["switch"], Pin.IN, Pin.PULL_UP)
            self.servo = PWM(Pin(hardware["servo"]), freq=SERVO_FREQUENCY)
            self.light_id = hardware["light"]

            self.is_down = False
            self.needs_broadcast = False
            self.time_hit = 0

            random_age = random.randint(0, CLOWN_REROLL_DURATION // 2)
            self.last_roll_time = time.ticks_add(time.ticks_ms(), -random_age)

            self.apply_new_difficulty()
            self.stand_up()
            self.turn_light_on()

            self.switch.irq(trigger=Pin.IRQ_FALLING, handler=self.hit)
        except Exception:
            self._release_failed_initialization()
            raise

    def _release_failed_initialization(self):
        """Release hardware owned by a target that could not finish setup."""
        if self.switch is not None:
            try:
                self.switch.irq(handler=None)
            except Exception:
                pass

        if self.servo is not None:
            try:
                self.servo.deinit()
            except Exception:
                pass

    def apply_new_difficulty(self):
        """Calculates new stats and updates the point/color values."""
        self.difficulty = roll_difficulty(self.id)
        self.points = DIFFICULTY_VALUES[self.difficulty]["points"]
        self.color = DIFFICULTY_VALUES[self.difficulty]["color"]

    def set_arm_down(self):
        self.servo.duty(SERVO_DOWN_DUTY)

    def set_arm_up(self):
        self.servo.duty(SERVO_UP_DUTY)

    def stand_up(self):
        print(f"Standing up Clown {self.id}")
        self.set_arm_up()
        time.sleep(SERVO_WAIT_DURATION)
        self.set_arm_down()  # Hide the arm away from the impact zone.

    def turn_light_on(self):
        set_single_light(self.light_id, self.color)

    def turn_light_off(self):
        set_single_light(self.light_id, OFF)

    def hit(self, pin):
        # Keep the IRQ callback allocation-free and defer I/O to the main loop.
        if pin.value() == 1 or self.is_down:
            return

        self.time_hit = time.ticks_ms()
        self.needs_broadcast = True
        self.is_down = True

    def reset(self):
        self.apply_new_difficulty()
        self.stand_up()
        self.turn_light_on()

        self.time_hit = 0
        self.last_roll_time = time.ticks_ms()
        self.needs_broadcast = False
        self.is_down = False

    def destroy(self):
        print(f"Destroying Clown {self.id}")

        self.needs_broadcast = False
        self.is_down = True
        cleanup_error = None

        # Attempt every cleanup step even if one hardware operation fails.
        try:
            self.switch.irq(handler=None)
        except Exception as error:
            cleanup_error = error

        try:
            self.turn_light_off()
        except Exception as error:
            if cleanup_error is None:
                cleanup_error = error

        try:
            self.stand_up()
        except Exception as error:
            if cleanup_error is None:
                cleanup_error = error

        if cleanup_error is not None:
            raise cleanup_error


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
    return wlan, connection


def close_network_connection(wlan, connection):
    """Best-effort radio cleanup after an exception or manual interruption."""
    try:
        connection.active(False)
    except Exception as error:
        print("Unable to deactivate ESP-NOW during shutdown:", error)

    try:
        wlan.disconnect()
        wlan.active(False)
    except Exception as error:
        print("Unable to deactivate Wi-Fi during shutdown:", error)


def push_led_data():
    """Sends the current state of the led_buffer to the physical strip."""
    state = machine.disable_irq()
    try:
        spi.write(led_buffer)
    finally:
        machine.enable_irq(state)

    time.sleep_ms(10)


def set_single_light(light_index, color):
    """Updates a specific LED in the buffer and pushes the change."""
    if not 0 <= light_index < NUM_TOTAL_LEDS:
        raise ValueError("light index is outside the LED buffer")

    start_idx = light_index * 3
    led_buffer[start_idx] = color[0]
    led_buffer[start_idx + 1] = color[1]
    led_buffer[start_idx + 2] = color[2]
    push_led_data()


def initialize_lights():
    for i in range(len(led_buffer)):
        led_buffer[i] = 0

    push_led_data()


spi = SoftSPI(
    baudrate=SPI_BAUDRATE,
    polarity=0,
    phase=0,
    sck=Pin(SPI_CLOCK_PIN),
    mosi=Pin(SPI_DATA_PIN),
    miso=Pin(SPI_UNUSED_MISO_PIN),
)
initialize_lights()


def roll_difficulty(clown_id):
    """Return a weighted difficulty based on target position."""
    roll = random.randint(1, 100)
    if clown_id < 2:  # Clowns 1 and 2
        if roll <= 75:
            return EASY
        return MEDIUM

    if clown_id < 4:  # Clowns 3 and 4
        if roll <= 25:
            return EASY
        if roll <= 75:
            return MEDIUM
        return HARD

    if clown_id < 6:  # Clowns 5 and 6
        if roll <= 25:
            return MEDIUM
        return HARD

    raise ValueError("clown id is outside the configured difficulty map")


def destroy_clowns(active_clowns):
    """Best-effort shutdown for every initialized target station."""
    for clown in active_clowns:
        try:
            clown.destroy()
        except Exception as error:
            print("Error while shutting down Clown", clown.id, error)


def create_clowns():
    """Construct a complete round, cleaning up if initialization is partial."""
    new_clowns = []
    try:
        for clown_id in range(NUM_CLOWNS):
            new_clowns.append(Clown(clown_id))
            time.sleep_ms(300)
    except Exception:
        destroy_clowns(new_clowns)
        raise

    return new_clowns


def run_controller(connection):
    """Run the target-controller state machine until reset or failure."""
    clowns = []
    state = WAITING

    print("Device initialized and awaiting START command")

    try:
        while True:
            _host, command = connection.recv(timeout_ms=RECEIVE_TIMEOUT_MS)

            if command is not None:
                print("Received command:", command)

            if state == WAITING:
                if command == START_COMMAND:
                    print("Starting new game")
                    clowns = create_clowns()
                    state = PLAYING
                elif command is not None:
                    print("Ignoring command while waiting:", command)

            elif state == PLAYING:
                if command == GAME_OVER_COMMAND:
                    print("Ending game")
                    destroy_clowns(clowns)
                    clowns = []
                    state = WAITING
                    continue
                if command is not None:
                    print("Ignoring command while playing:", command)

                current_time = time.ticks_ms()
                for clown in clowns:
                    if clown.is_down:
                        if clown.needs_broadcast:
                            hit_message = "%d-%d" % (clown.id, clown.points)
                            connection.send(BROADCAST_MAC, hit_message.encode("utf-8"))
                            clown.needs_broadcast = False
                        if (
                            time.ticks_diff(current_time, clown.time_hit)
                            >= CLOWN_RESET_DURATION
                        ):
                            clown.reset()
                    elif (
                        time.ticks_diff(current_time, clown.last_roll_time)
                        >= CLOWN_REROLL_DURATION
                    ):
                        clown.apply_new_difficulty()
                        clown.turn_light_on()
                        clown.last_roll_time = current_time

            time.sleep(GAME_LOOP_DURATION)
    finally:
        destroy_clowns(clowns)
        try:
            initialize_lights()
        except Exception as error:
            print("Unable to clear target lights during shutdown:", error)


def main():
    wlan, connection = create_network_connection()
    try:
        run_controller(connection)
    finally:
        close_network_connection(wlan, connection)


main()
