# global_config.py (V1.1)
import board
import neopixel
import busio
import digitalio
from digitalio import DigitalInOut, Direction, Pull
import keypad

# Constants and global variables
NUM_PIXELS = 64 + 4 + 4 + 1 + 1 + 16  # 64 step LEDs + 4 mute + 4 velocity + 1 play + 1 pitch bend + 16 pattern select
NUM_ROWS = 12
NUM_COLS = 8
SEQUENCE_LENGTH = 16
NUM_VOICES = 11
NUM_PATTERNS = 4

# Pin definitions
MIDI_OUT_PIN = board.GP0
LED_PIN = board.GP2
I2C_SDA = board.GP4
I2C_SCL = board.GP5

# Set columns as outputs
column_pins = [board.GP6, board.GP7, board.GP8, board.GP9, board.GP10, board.GP11, board.GP12, board.GP13]
for pin in column_pins:
    col_pin = digitalio.DigitalInOut(pin)
    col_pin.direction = digitalio.Direction.OUTPUT
    col_pin.value = False  # Set initial state to low

# Set rows as inputs with pull-ups
row_pins = [board.GP14, board.GP15, board.GP16, board.GP17, board.GP18,
board.GP19, board.GP20, board.GP21, board.GP22, board.GP26, board.GP27, board.GP28]
for pin in row_pins:
    row_pin = digitalio.DigitalInOut(pin)
    row_pin.direction = digitalio.Direction.INPUT
    row_pin.pull = digitalio.Pull.UP

# ROW_PINS = row_pins
"""[board.GP14, board.GP15, board.GP16, board.GP17, board.GP18,
board.GP19, board.GP20, board.GP21, board.GP22, board.GP26, board.GP27, board.GP28]"""
# COL_PINS = column_pins
"""[board.GP6, board.GP7, board.GP8, board.GP9, board.GP10, board.GP11, board.GP12, board.GP13]"""

# Initial setup for global variables
current_voices = [0] * NUM_ROWS
current_patterns = [0] * NUM_ROWS
sequences = [[[0] * SEQUENCE_LENGTH for _ in range(NUM_VOICES)] for _ in range(NUM_PATTERNS)]

# Additional global variables
bpm = 120.0
beat_time = 60.0 / bpm
beat_millis = beat_time * 1000.0
steps_per_beat = 4
steps_millis = beat_millis / steps_per_beat
step_counter = 0
playing = False
voice_change_flag = False
