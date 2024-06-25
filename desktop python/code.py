import board
import neopixel
import keypad
import time

# Constants
NUM_ROWS = 12
NUM_COLS = 8
NUM_LEDS = 96

# Define row and column pins
ROW_PINS = [board.GP14, board.GP15, board.GP16, board.GP17, board.GP18, board.GP19, board.GP20, board.GP21, board.GP22, board.GP26, board.GP27, board.GP28]
COL_PINS = [board.GP6, board.GP7, board.GP8, board.GP9, board.GP10, board.GP11, board.GP12, board.GP13]

# Initialize the KeyMatrix
keys = None
try:
    keys = keypad.KeyMatrix(ROW_PINS, COL_PINS, columns_to_anodes=True)
except ValueError as e:
    print(f"Error initializing KeyMatrix: {e}")
    time.sleep(1)  # Pause before restarting the script

# Initialize the Neopixel LEDs
pixels = neopixel.NeoPixel(board.GP2, NUM_LEDS, auto_write=True)

# Create a list to keep track of LED states
led_states = [False] * NUM_LEDS

# Function to update the LEDs based on the current states
def update_leds():
    for i in range(NUM_LEDS):
        if led_states[i]:
            pixels[i] = (255, 255, 255)  # White color when LED is on
        else:
            pixels[i] = (0, 0, 0)  # Off when LED is off
    pixels.show()

# Main loop to handle button presses and toggle LEDs
while True:
    if keys:
        event = keys.events.get()
        if event:
            col, row = divmod(event.key_number, NUM_COLS)
            led_index = row * NUM_COLS + col  # Calculate the LED index
            if event.pressed:
                led_states[led_index] = not led_states[led_index]  # Toggle the LED state
                update_leds()  # Update the LEDs
            print(f"Button {'pressed' if event.pressed else 'released'}: Row {row}, Col {col}, LED {led_index}")
    time.sleep(0.01)  # Small delay to debounce
