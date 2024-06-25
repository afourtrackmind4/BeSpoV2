# pattern_management.py (V1.0)
from global_config import NUM_PATTERNS, SEQUENCE_LENGTH, NUM_VOICES, sequences
from led_control import update_leds

# Initialize to load the first pattern by default
current_pattern = 0

def load_pattern(pattern_index):
    global sequence
    sequence = sequences[pattern_index]
    update_leds()  # Update LEDs to reflect the loaded pattern

# Toggle pattern selection
def toggle_pattern():
    global current_pattern
    current_pattern = (current_pattern + 1) % NUM_PATTERNS
    load_pattern(current_pattern)
    display.fill(0)
    display.print(f"Patt:{current_pattern+1}")
