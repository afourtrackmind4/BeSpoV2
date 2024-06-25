# global_config.py (V1.0)
import board
import neopixel
import busio
from digitalio import DigitalInOut, Direction, Pull
import keypad

# Constants and global variables
NUM_PIXELS = 64
NUM_ROWS = 12
NUM_COLS = 8
SEQUENCE_LENGTH = 16
NUM_VOICES = 11
NUM_PATTERNS = 4

# Pin definitions
ROW_PINS = [board.GP6, board.GP7, board.GP8, board.GP9, board.GP10, board.GP11, board.GP12, board.GP13, board.GP14, board.GP15, board.GP28, board.GP29]
COL_PINS = [board.GP16, board.GP17, board.GP18, board.GP19, board.GP20, board.GP21, board.GP22, board.GP23]

# Initial setup for global variables
current_voices = [0] * NUM_ROWS
current_patterns = [0] * NUM_ROWS
sequences = [[[0] * SEQUENCE_LENGTH for _ in range(NUM_ROWS)] for _ in range(NUM_PATTERNS)]

# led_control.py (V1.0)
import neopixel
from global_config import NUM_PIXELS, SEQUENCE_LENGTH, NUM_ROWS, current_voices, current_patterns, sequences, ROW_PINS, COL_PINS

# Initialize the Neopixel LEDs
pixels = neopixel.NeoPixel(board.GP2, NUM_PIXELS, auto_write=False)

# Define colors for each voice
voice_colors = [
    (255, 0, 0),    # Voice 0
    (0, 255, 0),    # Voice 1
    (0, 0, 255),    # Voice 2
    (255, 255, 0),  # Voice 3
    (255, 0, 255),  # Voice 4
    (0, 255, 255),  # Voice 5
    (255, 165, 0),  # Voice 6
    (75, 0, 130),   # Voice 7
    (128, 0, 128),  # Voice 8
    (255, 192, 203),# Voice 9
    (0, 128, 0),    # Voice 10
]

# Function to update LEDs based on the current sequence and pointers
def update_leds():
    for row in range(NUM_ROWS):
        for step in range(SEQUENCE_LENGTH):
            led_index = row * SEQUENCE_LENGTH + step
            voice = current_voices[row]
            pattern = current_patterns[row]
            state = sequences[pattern][row][step]
            color = voice_colors[voice] if state else (0, 0, 0)
            pixels[led_index] = color
    pixels.show()

# Boot sequence for Neopixels
def neopixel_boot_sequence():
    for i in range(NUM_PIXELS):
        pixels[i] = (0, 70, 150)  # Blue color for boot sequence
        pixels.show()
        time.sleep(0.004)
    time.sleep(0.01)
    pixels.fill((0, 0, 0))
    pixels.show()
# key_matrix.py (V1.0)
from global_config import ROW_PINS, COL_PINS, NUM_ROWS, SEQUENCE_LENGTH, current_voices, current_patterns, sequences
from led_control import update_leds
import keypad

# Initialize the KeyMatrix using the defined row and column pins
keys = keypad.KeyMatrix(ROW_PINS, COL_PINS, columns_to_anodes=True)

# Define keys for scrolling in the 8x12 matrix
scroll_voice_up_key = (8, 0)  # Example position, adjust as needed
scroll_voice_down_key = (8, 1)  # Example position, adjust as needed
scroll_pattern_up_key = (9, 0)  # Example position, adjust as needed
scroll_pattern_down_key = (9, 1)  # Example position, adjust as needed

# Scroll through voices for a specific row
def scroll_voice(row, direction):
    current_voices[row] = (current_voices[row] + direction) % len(voice_colors)
    update_leds()

# Scroll through patterns for a specific row
def scroll_pattern(row, direction):
    current_patterns[row] = (current_patterns[row] + direction) % len(sequences)
    update_leds()

# Handle button press events and set the flag for voice change
def handle_button_press(event):
    global voice_change_flag
    col, row = divmod(event.key_number, len(COL_PINS))
    if event.pressed:
        if (row, col) == scroll_voice_up_key:
            scroll_voice(0, 1)  # Scroll voice up for row 0, adjust as needed
        elif (row, col) == scroll_voice_down_key:
            scroll_voice(0, -1)  # Scroll voice down for row 0, adjust as needed
        elif (row, col) == scroll_pattern_up_key:
            scroll_pattern(0, 1)  # Scroll pattern up for row 0, adjust as needed
        elif (row, col) == scroll_pattern_down_key:
            scroll_pattern(0, -1)  # Scroll pattern down for row 0, adjust as needed
        else:
            # Handle normal sequence key presses
            if row < NUM_ROWS and col < SEQUENCE_LENGTH:
                step_index = col
                voice_index = current_voices[row]
                pattern_index = current_patterns[row]
                sequences[pattern_index][row][step_index] = not sequences[pattern_index][row][step_index]  # Toggle step state
                light_steps(row, step_index, sequences[pattern_index][row][step_index])  # Update LED
                voice_change_flag = True  # Set the flag for voice change
