# led_control.py (V1.3)
import neopixel
import time
from global_config import NUM_PIXELS, SEQUENCE_LENGTH, NUM_ROWS, current_voices, current_patterns, sequences, LED_PIN

# Initialize the Neopixel LEDs
pixels = neopixel.NeoPixel(LED_PIN, NUM_PIXELS, auto_write=False)

# Define colors for each voice
voice_colors = {
    0: (255, 0, 0),    # Bass drum - Red
    1: (0, 255, 0),    # Snare - Green
    2: (0, 0, 255),    # Low Tom - Blue
    3: (255, 255, 0),  # Mid Tom - Yellow
    4: (255, 0, 255),  # High Tom - Magenta
    5: (0, 255, 255),  # Rimshot - Cyan
    6: (255, 165, 0),  # Hand Clap - Orange
    7: (75, 0, 130),   # Cowbell - Indigo
    8: (128, 0, 128),  # Cymbal - Purple
    9: (255, 192, 203),# Open Hi-Hat - Pink
    10: (0, 128, 0),   # Closed Hi-Hat - Dark Green
}

# Function to update LEDs based on the current sequence and pointers
def update_leds():
    for row in range(8):  # Only iterate over the first 8 rows for step LEDs
        for step in range(SEQUENCE_LENGTH if SEQUENCE_LENGTH < 16 else 16):
            led_index = row * SEQUENCE_LENGTH + step  # Calculate LED index
            voice = current_voices[row]
            pattern = current_patterns[row]
            state = sequences[pattern][row][step]
            color = voice_colors[voice] if state else (0, 0, 0)
            print(f"Updating LED at row {row}, step {step}, voice {voice}, pattern {pattern}, led_index {led_index}")
            if led_index >= NUM_PIXELS:
                print(f"Error: led_index {led_index} out of range")
                continue
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

# Call the boot sequence at the start
neopixel_boot_sequence()

# Light steps
def light_steps(voice_index, step_index, state):
    led_index = voice_index * SEQUENCE_LENGTH + step_index  # Map the voice and step to the LED index
    color = voice_colors.get(voice_index, (8, 125, 60))  # Default to Purple if voice not found
    if 0 <= led_index < NUM_PIXELS:  # Ensure LED index is within the valid range
        if state:
            pixels[led_index] = color  # Set color based on voice
        else:
            pixels[led_index] = (0, 0, 0)  # Off for inactive steps
        pixels.show()

# Light the current beat
def light_beat(step):
    for row in range(NUM_ROWS):
        led_index = row * SEQUENCE_LENGTH + step
        if 0 <= led_index < NUM_PIXELS:
            pixels[led_index] = (70, 20, 0)  # Red color for the beat indicator
    pixels.show()



"""# led_control.py (V1.3)
import neopixel
import time
from global_config import NUM_PIXELS, SEQUENCE_LENGTH, NUM_ROWS, current_voices, current_patterns, sequences, LED_PIN

# Initialize the Neopixel LEDs
pixels = neopixel.NeoPixel(LED_PIN, NUM_PIXELS, auto_write=False)

# Define colors for each voice
voice_colors = {
    0: (255, 0, 0),    # Bass drum - Red
    1: (0, 255, 0),    # Snare - Green
    2: (0, 0, 255),    # Low Tom - Blue
    3: (255, 255, 0),  # Mid Tom - Yellow
    4: (255, 0, 255),  # High Tom - Magenta
    5: (0, 255, 255),  # Rimshot - Cyan
    6: (255, 165, 0),  # Hand Clap - Orange
    7: (75, 0, 130),   # Cowbell - Indigo
    8: (128, 0, 128),  # Cymbal - Purple
    9: (255, 192, 203),# Open Hi-Hat - Pink
    10: (0, 128, 0),   # Closed Hi-Hat - Dark Green
}

# Function to update LEDs based on the current sequence and pointers
def update_leds():
    for row in range(8):  # Only iterate over the first 8 rows for step LEDs
        for step in range(SEQUENCE_LENGTH if SEQUENCE_LENGTH < 16 else 16):
            led_index = row * SEQUENCE_LENGTH + step  # Calculate LED index
            voice = current_voices[row]
            pattern = current_patterns[row]
            state = sequences[pattern][row][step]
            color = voice_colors[voice] if state else (0, 0, 0)
            print(f"Updating LED at row {row}, step {step}, voice {voice}, pattern {pattern}, led_index {led_index}")
            if led_index >= NUM_PIXELS:
                print(f"Error: led_index {led_index} out of range")
                continue
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

# Call the boot sequence at the start
neopixel_boot_sequence()

# Light steps
def light_steps(voice_index, step_index, state):
    led_index = voice_index * SEQUENCE_LENGTH + step_index  # Map the voice and step to the LED index
    color = voice_colors.get(voice_index, (8, 125, 60))  # Default to Purple if voice not found
    if 0 <= led_index < NUM_PIXELS:  # Ensure LED index is within the valid range
        if state:
            pixels[led_index] = color  # Set color based on voice
        else:
            pixels[led_index] = (0, 0, 0)  # Off for inactive steps
        pixels.show()

# Light the current beat
def light_beat(step):
    for row in range(NUM_ROWS):
        led_index = row * SEQUENCE_LENGTH + step
        if 0 <= led_index < NUM_PIXELS:
            pixels[led_index] = (70, 20, 0)  # Red color for the beat indicator
    pixels.show()
"""
