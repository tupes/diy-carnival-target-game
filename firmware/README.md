# Firmware notes

The game runs as two cooperating MicroPython programs. They target different device APIs and are deployed separately; neither file is intended to run under desktop CPython.

| Controller | Source | Responsibilities |
| --- | --- | --- |
| ESP32 | [`esp32/main.py`](esp32/main.py) | Target state, active-low switches, servo PWM, RGB output, difficulty selection, and hit transmission |
| Touchscreen M5Stack | [`m5stack/main.py`](m5stack/main.py) | Touch input, round timing, scoring, high score, LCD rendering, and hit audio |

## ESP-NOW protocol

All current messages are broadcasts:

| Direction | Payload | Meaning |
| --- | --- | --- |
| M5Stack → ESP32 | `START` | Create and enable the target stations for a new round |
| M5Stack → ESP32 | `GAME OVER` | Disable hit interrupts, clear the lights, and reset the mechanisms |
| ESP32 → M5Stack | `<target_id>-<points>` | Add 1–3 points for the specified zero-based target |

The protocol is intentionally small, but it is best-effort: it has no acknowledgement, session ID, or duplicate suppression. A production revision should add coordinated retry/acknowledgement semantics to both controllers and verify them on hardware; retrying hit messages alone would risk double-scoring.

The M5Stack wrapper is initialized with channel argument `0` and string data type `1`. The exact legacy UIFlow build used for the delivered game was not recorded, so radio-channel changes should be tested on both devices together.

## ESP32 pin map

The firmware currently enables the first five stations.

| Station | Status | Switch GPIO | Servo GPIO | LED index |
| ---: | --- | ---: | ---: | ---: |
| 1 | Active | 18 | 14 | 0 |
| 2 | Active | 23 | 27 | 1 |
| 3 | Active | 19 | 26 | 2 |
| 4 | Active | 22 | 25 | 3 |
| 5 | Active | 21 | 33 | 4 |
| 6 | Reserved layout | 37 | 32 | 5 |

The clocked RGB connection uses GPIO 13 for clock and GPIO 4 for data. The `SoftSPI` constructor also receives GPIO 12 as MISO, although the game does not consume return data from the lights.

The sixth switch mapping is historical. On a classic ESP32, GPIO 37 does not provide the internal pull-up used by the active stations; enabling it requires an external pull-up or a verified remap.

## Deployment requirements

### ESP32

- Install an ESP32 MicroPython build that includes `espnow`.
- Copy [`esp32/main.py`](esp32/main.py) to the board as `/main.py`.
- Use [`esp32/debug/lights.py`](esp32/debug/lights.py) as a temporary diagnostic script when isolating the clock/data/color path.

### M5Stack

- Use a touch-capable M5Stack firmware with the legacy UIFlow 1-style `m5stack`, `uiflow`, and `libs.m5_espnow` APIs.
- Deploy [`m5stack/main.py`](m5stack/main.py) through the matching UIFlow/MicroPython workflow.
- Copy a compatible score sound to `/flash/res/ding.wav`, or leave audio unavailable; the sound file is not included in this repository.

## Hardware-validation boundaries

- `SERVO_UP_DUTY` and `SERVO_DOWN_DUTY` are calibrated legacy PWM duty values, not angles. Do not translate them to `duty_u16` or `duty_ns` without rechecking the mechanism travel.
- Servo movement deliberately blocks for 0.5 seconds. Replacing it with a non-blocking actuator state machine would improve radio responsiveness but changes mechanical timing.
- Round teardown leaves servo PWM active so the delivered mechanism retains its calibrated resting behavior. Test target stability and power draw on the physical assembly before adding `PWM.deinit()`.
- `START` and `GAME OVER` are each sent once. Reliability improvements require a coordinated protocol change across both devices.
- The exact MicroPython, M5Stack hardware, and UIFlow versions used for delivery were not archived, so all flash/runtime changes require a two-controller bench test.
