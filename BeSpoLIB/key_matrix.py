from global_config import ROW_PINS, COL_PINS, NUM_ROWS, SEQUENCE_LENGTH, current_voices, current_patterns, sequences
from led_control import update_leds, light_steps
import keypad
import digitalio

# Manual GPIO configuration for key matrix
# Set columns as outputs
for pin in COL_PINS:
    col_pin = digitalio.DigitalInOut(pin)
    col_pin.direction = digitalio.Direction.OUTPUT
    col_pin.value = False  # Set initial state to low

# Set rows as inputs with pull-ups
for pin in ROW_PINS:
    row_pin = digitalio.DigitalInOut(pin)
    row_pin.direction = digitalio.Direction.INPUT
    row_pin.pull = digitalio.Pull.UP


# Initialize the KeyMatrix using the defined row and column pins
keys = keypad.KeyMatrix(row_pins, col_pins, columns_to_anodes=True)


# Define keys for scrolling and additional controls in the 12x8 matrix
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
    print(f"Key pressed at column: {col}, row: {row}, key number: {event.key_number}")
    if event.pressed:
        if (row, col) == scroll_voice_up_key:
            scroll_voice(row, 1)  # Scroll voice up for row, adjust as needed
        elif (row, col) == scroll_voice_down_key:
            scroll_voice(row, -1)  # Scroll voice down for row, adjust as needed
        elif (row, col) == scroll_pattern_up_key:
            scroll_pattern(row, 1)  # Scroll pattern up for row, adjust as needed
        elif (row, col) == scroll_pattern_down_key:
            scroll_pattern(row, -1)  # Scroll pattern down for row, adjust as needed
        else:
            # Handle normal sequence key presses
            if row < NUM_ROWS and col < SEQUENCE_LENGTH:
                step_index = col
                voice_index = current_voices[row]
                pattern_index = current_patterns[row]
                sequences[pattern_index][row][step_index] = not sequences[pattern_index][row][step_index]  # Toggle step state
                light_steps(row, step_index, sequences[pattern_index][row][step_index])  # Update LED
                voice_change_flag = True  # Set the flag for voice change

# Main loop to process key events
def process_keys():
    event = keys.events.get()
    if event:
        handle_button_press(event)




"""# key_matrix.py (V1.1)
from global_config import ROW_PINS, COL_PINS, NUM_ROWS, SEQUENCE_LENGTH, current_voices, current_patterns, sequences
from led_control import update_leds, light_steps
import keypad

# Initialize the KeyMatrix using the defined row and column pins
keys = keypad.KeyMatrix(ROW_PINS, COL_PINS, columns_to_anodes=False)

# Define keys for scrolling and additional controls in the 12x8 matrix
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
    print(f"Key pressed at column: {col}, row: {row}, key number: {event.key_number}")
    if event.pressed:
        if (row, col) == scroll_voice_up_key:
            scroll_voice(row, 1)  # Scroll voice up for row, adjust as needed
        elif (row, col) == scroll_voice_down_key:
            scroll_voice(row, -1)  # Scroll voice down for row, adjust as needed
        elif (row, col) == scroll_pattern_up_key:
            scroll_pattern(row, 1)  # Scroll pattern up for row, adjust as needed
        elif (row, col) == scroll_pattern_down_key:
            scroll_pattern(row, -1)  # Scroll pattern down for row, adjust as needed
        else:
            # Handle normal sequence key presses
            if row < NUM_ROWS and col < SEQUENCE_LENGTH:
                step_index = col
                voice_index = current_voices[row]
                pattern_index = current_patterns[row]
                sequences[pattern_index][row][step_index] = not sequences[pattern_index][row][step_index]  # Toggle step state
                light_steps(row, step_index, sequences[pattern_index][row][step_index])  # Update LED
                voice_change_flag = True  # Set the flag for voice change

# Main loop to process key events
def process_keys():
    event = keys.events.get()
    if event:
        handle_button_press(event)
"""

"""
def handle_button_press(event):
    global voice_change_flag
    col, row = divmod(event.key_number, len(COL_PINS))
    print(f"Key pressed at column: {col}, row: {row}")
    if event.pressed:
        if (row, col) == scroll_voice_up_key:
            scroll_voice(row, 1)  # Scroll voice up for row, adjust as needed
        elif (row, col) == scroll_voice_down_key:
            scroll_voice(row, -1)  # Scroll voice down for row, adjust as needed
        elif (row, col) == scroll_pattern_up_key:
            scroll_pattern(row, 1)  # Scroll pattern up for row, adjust as needed
        elif (row, col) == scroll_pattern_down_key:
            scroll_pattern(row, -1)  # Scroll pattern down for row, adjust as needed
        else:
            # Handle normal sequence key presses
            if row < NUM_ROWS and col < SEQUENCE_LENGTH:
                step_index = col
                voice_index = current_voices[row]
                pattern_index = current_patterns[row]
                sequences[pattern_index][row][step_index] = not sequences[pattern_index][row][step_index]  # Toggle step state
                light_steps(row, step_index, sequences[pattern_index][row][step_index])  # Update LED
                voice_change_flag = True  # Set the flag for voice change

# Main loop to process key events
def process_keys():
    event = keys.events.get()
    if event:
        handle_button_press(event)
"""



"""
from global_config import ROW_PINS, COL_PINS, NUM_ROWS, SEQUENCE_LENGTH, current_voices, current_patterns, sequences
from led_control import update_leds, light_steps
import keypad

# Initialize the KeyMatrix using the defined row and column pins
keys = keypad.KeyMatrix(ROW_PINS, COL_PINS, columns_to_anodes=False)

# Define keys for scrolling and additional controls in the 12x8 matrix
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
    print(f"Key pressed at column: {col}, row: {row}")
    if event.pressed:
        if (row, col) == scroll_voice_up_key:
            scroll_voice(row, 1)  # Scroll voice up for row, adjust as needed
        elif (row, col) == scroll_voice_down_key:
            scroll_voice(row, -1)  # Scroll voice down for row, adjust as needed
        elif (row, col) == scroll_pattern_up_key:
            scroll_pattern(row, 1)  # Scroll pattern up for row, adjust as needed
        elif (row, col) == scroll_pattern_down_key:
            scroll_pattern(row, -1)  # Scroll pattern down for row, adjust as needed
        else:
            # Handle normal sequence key presses
            if row < NUM_ROWS and col < SEQUENCE_LENGTH:
                step_index = col
                voice_index = current_voices[row]
                pattern_index = current_patterns[row]
                sequences[pattern_index][row][step_index] = not sequences[pattern_index][row][step_index]  # Toggle step state
                light_steps(row, step_index, sequences[pattern_index][row][step_index])  # Update LED
                voice_change_flag = True  # Set the flag for voice change

# Main loop to process key events
def process_keys():
    event = keys.events.get()
    if event:
        handle_button_press(event)
"""
