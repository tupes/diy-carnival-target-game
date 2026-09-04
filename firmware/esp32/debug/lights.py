# SPDX-FileCopyrightText: 2026 Mark Tupala
# SPDX-License-Identifier: MIT

"""Cycle one clocked RGB pixel through the colors used by the game."""

import time
from machine import Pin, SoftSPI

SPI_CLOCK_PIN = 13
SPI_DATA_PIN = 4
SPI_UNUSED_MISO_PIN = 12
SPI_BAUDRATE = 100_000
COLOR_DWELL_MS = 1_000

OFF = (0, 0, 0)
TEST_SEQUENCE = (
    ("green", (0, 255, 0)),
    ("blue", (0, 0, 255)),
    ("red", (255, 0, 0)),
    ("yellow", (255, 255, 0)),
)

spi = SoftSPI(
    baudrate=SPI_BAUDRATE,
    polarity=0,
    phase=0,
    sck=Pin(SPI_CLOCK_PIN),
    mosi=Pin(SPI_DATA_PIN),
    miso=Pin(SPI_UNUSED_MISO_PIN),
)
pixel = bytearray(3)


def write_color(color):
    """Write one RGB tuple to the first pixel."""
    pixel[0] = color[0]
    pixel[1] = color[1]
    pixel[2] = color[2]
    spi.write(pixel)


try:
    write_color(OFF)
    for name, color in TEST_SEQUENCE:
        print("Testing", name)
        write_color(color)
        time.sleep_ms(COLOR_DWELL_MS)
finally:
    write_color(OFF)
