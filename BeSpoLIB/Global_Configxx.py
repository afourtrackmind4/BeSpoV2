# global_config.py (V1.2)
import board
import neopixel
import busio
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

ROW_PINS = [board.GP14, board.GP15, board.GP16, board.GP17, board.GP18, board.GP19, board.GP20, board.GP21, board.GP22, board.GP26, board.GP27, board.GP28]
COL_PINS = [board.GP6, board.GP7, board.GP8, board.GP9, board.GP10, board.GP11, board.GP12, board.GP13]

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



"""

# global_config.py (V1.2)
import board
import neopixel
import busio
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


ROW_PINS = [board.GP14, board.GP15, board.GP16, board.GP17, board.GP18, board.GP19, board.GP20, board.GP21, board.GP22, board.GP26, board.GP27, board.GP28]
COL_PINS = [board.GP6, board.GP7, board.GP8, board.GP9, board.GP10, board.GP11, board.GP12, board.GP13]

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
"""

"""# global_config.py (V1.1)

import board

# General configurations
NUM_PIXELS = 64
SEQUENCE_LENGTH = 16
NUM_ROWS = 4
NUM_VOICES = 11

# LED pin configuration
LED_PIN = board.GP2

# Other configurations
bpm = 120.0
steps_millis = (60.0 / bpm) * 1000.0 / 4  # Example calculation for steps per beat
"""


"""# global_config.py (V1.1)
import board
import neopixel
import busio
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

ROW_PINS = [board.GP14, board.GP15, board.GP16, board.GP17, board.GP18, board.GP19, board.GP20, board.GP21, board.GP22, board.GP26, board.GP27, board.GP28]
COL_PINS = [board.GP6, board.GP7, board.GP8, board.GP9, board.GP10, board.GP11, board.GP12, board.GP13]

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
"""
