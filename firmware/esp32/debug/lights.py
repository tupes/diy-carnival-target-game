from machine import Pin, SoftSPI
spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=Pin(13), mosi=Pin(4), miso=Pin(12))
led_buffer = bytearray(3)

OFF = [0, 0, 0]
led_buffer[0] = OFF[0]
led_buffer[1] = OFF[1]
led_buffer[2] = OFF[2]
spi.write(led_buffer)

GREEN = [0, 255, 0]
led_buffer[0] = GREEN[0]
led_buffer[1] = GREEN[1]
led_buffer[2] = GREEN[2]
spi.write(led_buffer)

BLUE = [0, 0, 255]
led_buffer[0] = BLUE[0]
led_buffer[1] = BLUE[1]
led_buffer[2] = BLUE[2]
spi.write(led_buffer)

RED = [255, 0, 0]
led_buffer[0] = RED[0]
led_buffer[1] = RED[1]
led_buffer[2] = RED[2]
spi.write(led_buffer)

YELLOW = [255, 255, 0]
led_buffer[0] = YELLOW[0]
led_buffer[1] = YELLOW[1]
led_buffer[2] = YELLOW[2]
spi.write(led_buffer)