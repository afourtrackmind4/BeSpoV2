import board
import neopixel
import busio
from digitalio import DigitalInOut, Pull
import keypad
import digitalio
import time
from adafruit_ht16k33 import segments
from adafruit_seesaw import seesaw, rotaryio, digitalio as seesaw_digitalio
from adafruit_debouncer import Debouncer
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

# Constants and global variables
NUM_PIXELS = 64 + 4 + 4 + 1 + 1 + 16
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
sequences = [[[0] * SEQUENCE_LENGTH for _ in range(NUM_ROWS)] for _ in range(NUM_PATTERNS)]
print(f"sequences dimensions: {len(sequences)}x{len(sequences[0])}x{len(sequences[0][0])}")  # Debug print



# Additional global variables
bpm = 120.0
beat_time = 60.0 / bpm
beat_millis = beat_time * 1000.0
steps_per_beat = 4
steps_millis = beat_millis / steps_per_beat
step_counter = 0
playing = False
voice_change_flag = False

# LED Setup
pixels = neopixel.NeoPixel(LED_PIN, NUM_PIXELS, auto_write=False)

# Function for LED boot sequence
def neopixel_boot_sequence():
    colors = [
        (255, 0, 0),    # Red
        (255, 165, 0),  # Orange
        (255, 255, 0),  # Yellow
        (0, 255, 0),    # Green
        (0, 255, 255),  # Cyan
        (0, 0, 255),    # Blue
        (128, 0, 128),  # Purple
        (255, 192, 203) # Pink
    ]
    color_index = 0
    for i in range(NUM_PIXELS):
        pixels[i] = colors[color_index]
        pixels.show()
        time.sleep(0.02)
        color_index = (color_index + 1) % len(colors)

    # Chase off sequence
    for i in range(NUM_PIXELS):
        pixels[i] = (0, 0, 0)
        pixels.show()
        time.sleep(0.02)

# Call the boot sequence at the start
neopixel_boot_sequence()


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


# MIDI Setup
uart = busio.UART(MIDI_OUT_PIN, baudrate=31250)
midi = MIDI(midi_out=uart, out_channel=9)

# Display Setup
i2c = board.STEMMA_I2C()
display = segments.Seg14x4(i2c, address=(0x71))
display.brightness = 1.0
display.fill(0)
display.show()
display.print(bpm)
display.show()

# Display startup message
def display_startup_message():
    display.fill(0)
    display.marquee("THE", 0.03, loop=False)
    time.sleep(0.2)
    display.marquee("BEAT", 0.05, loop=False)
    time.sleep(0.2)
    display.marquee("SPOT", 0.04, loop=False)
    time.sleep(0.05)
    display.marquee("BPM", 0.02, loop=False)
    time.sleep(0.2)
    display.marquee(str(bpm), 0.1, loop=False)

# Call the startup message function
display_startup_message()

print("Starting LED setup")
# Rotary Encoder Setup
rotary_seesaw = seesaw.Seesaw(i2c, addr=0x36)
encoder = rotaryio.IncrementalEncoder(rotary_seesaw)
last_encoder_pos = 0
knobbutton_in = seesaw_digitalio.DigitalIO(rotary_seesaw, 24)
knobbutton = Debouncer(knobbutton_in)
encoder_pos = encoder.position

print("Starting play button setup")

# Play Button Setup
start_button_in = DigitalInOut(board.GP3)
start_button_in.pull = Pull.UP
start_button = Debouncer(start_button_in)

print("Starting key matrix setup")
# Initialize the KeyMatrix using the defined row and column pins
keys = keypad.KeyMatrix(ROW_PINS, COL_PINS, columns_to_anodes=True)

# Button Assignments (clearly labeled for easy rearrangement)
scroll_voice_up_key = (8, 0)
scroll_voice_down_key = (8, 1)
scroll_pattern_up_key = (9, 0)
scroll_pattern_down_key = (9, 1)
shuffle_up_key = (10, 0)
shuffle_down_key = (10, 1)
play_button_key = (11, 0)
global_brightness_up_key = (11, 1)
global_brightness_down_key = (11, 2)
print("buttons assinged")

# Function to play a drum note
def play_drum(note):
    midi.send(NoteOn(note, 120))  # Note on with velocity 120
    time.sleep(0.01)  # Short delay to simulate the note being played
    midi.send(NoteOff(note, 0))  # Note off
print("drum functions loaded")

# Function to update LEDs based on the current sequence and pointers

"""
def update_leds():
    print("Updating LEDs...")
    print(f"NUM_ROWS: {NUM_ROWS}, SEQUENCE_LENGTH: {SEQUENCE_LENGTH}")
    print(f"current_voices length: {len(current_voices)}, current_patterns length: {len(current_patterns)}")
    print(f"sequences dimensions: {len(sequences)}x{len(sequences[0])}x{len(sequences[0][0])}")

    for row in range(NUM_ROWS):
        for step in range(SEQUENCE_LENGTH):
            led_index = row * SEQUENCE_LENGTH + step
            if led_index < NUM_PIXELS:
                print(f"Updating LED at row: {row}, step: {step}, led_index: {led_index}")
                voice = current_voices[row]
                pattern = current_patterns[row]
                print(f"Current voice: {voice}, Current pattern: {pattern}")
                color = voice_colors[voice] if sequences[pattern][row][step] else (0, 0, 0)
                pixels[led_index] = color
            else:
                print(f"Skipping LED update at row: {row}, step: {step}, led_index: {led_index} (out of bounds)")
    pixels.show()
"""

def update_leds():
    print("Updating all LEDs...")
    for row in range(NUM_ROWS):
        for step in range(SEQUENCE_LENGTH):
            update_specific_led(row, step)


def update_specific_led(row, step):
    led_index = row * SEQUENCE_LENGTH + step
    if led_index < NUM_PIXELS:
        voice = current_voices[row]
        pattern = current_patterns[row]
        color = voice_colors[voice] if sequences[pattern][row][step] else (0, 0, 0)
        pixels[led_index] = color
        pixels.show()
    else:
        print(f"Skipping LED update at row: {row}, step: {step}, led_index: {led_index} (out of bounds)")

def update_all_leds_in_row(row):
    for step in range(SEQUENCE_LENGTH):
        update_specific_led(row, step)



"""
def update_leds():
    print("Updating LEDs...")  # Debug print
    print(f"NUM_ROWS: {NUM_ROWS}, SEQUENCE_LENGTH: {SEQUENCE_LENGTH}")  # Debug print
    print(f"current_voices length: {len(current_voices)}, current_patterns length: {len(current_patterns)}")  # Debug print
    print(f"sequences dimensions: {len(sequences)}x{len(sequences[0])}x{len(sequences[0][0])}")  # Debug print

    for row in range(NUM_ROWS):
        for step in range(SEQUENCE_LENGTH):
            led_index = row * SEQUENCE_LENGTH + step  # Calculate LED index
            print(f"Updating LED at row: {row}, step: {step}, led_index: {led_index}")  # Debug print
            voice = current_voices[row]
            pattern = current_patterns[row]
            print(f"Current voice: {voice}, Current pattern: {pattern}")  # Debug print

            if voice < len(voice_colors):  # Ensure voice index is within bounds
                state = sequences[pattern][row][step]
                color = voice_colors[voice] if state else (0, 0, 0)
                pixels[led_index] = color
            else:
                print(f"Voice index out of range: {voice}")  # Debug print for out-of-range voice index

    pixels.show()
    print("LEDs updated")  # Debug print
"""

# Scroll through voices for a specific row

def scroll_voice(row, direction):
    current_voices[row] = (current_voices[row] + direction) % len(voice_colors)
    update_leds()
print("voice scroll loaded")

# Scroll through patterns for a specific row
def scroll_pattern(row, direction):
    current_patterns[row] = (current_patterns[row] + direction) % len(sequences)
    update_leds()
print("pTTERN SELECT LOADED")

# Handle button press events and set the flag for voice change
def handle_button_press(row, step):
    if row < 8:  # Step sequencer grid
        sequences[current_patterns[row]][row][step] = not sequences[current_patterns[row]][row][step]
        update_specific_led(row, step)
    elif row == 8:  # Voice mute/unmute
        voice_index = step // 2
        current_voices[voice_index] = (current_voices[voice_index] + 1) % len(voice_colors)
        update_all_leds_in_row(voice_index * 2)
        update_all_leds_in_row(voice_index * 2 + 1)
    # Add other button functionalities here as per your requirement


"""
def handle_button_press(event):
    global voice_change_flag
    col, row = divmod(event.key_number, len(COL_PINS))
    print(f"Key pressed at column: {col}, row: {row}, key number: {event.key_number}")  # Debug print

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

                # Toggle step state
                sequences[pattern_index][row][step_index] = not sequences[pattern_index][row][step_index]

                # Update the relevant LED
                led_index = row * SEQUENCE_LENGTH + step_index
                if led_index < NUM_PIXELS:  # Ensure led_index is within bounds
                    state = sequences[pattern_index][row][step_index]
                    color = voice_colors[voice_index] if state else (0, 0, 0)
                    pixels[led_index] = color
                    pixels.show()
                    print(f"LED updated at index: {led_index}, color: {color}")  # Debug print

                voice_change_flag = True  # Set the flag for voice change

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
        elif (row, col) == shuffle_up_key:
            # Increase shuffle amount
            shuffle_amount = min(shuffle_amount + 0.05, 0.5)
            print(f"Shuffle amount: {shuffle_amount}")
        elif (row, col) == shuffle_down_key:
            # Decrease shuffle amount
            shuffle_amount = max(shuffle_amount - 0.05, 0.0)
            print(f"Shuffle amount: {shuffle_amount}")
        elif (row, col) == play_button_key:
            global playing
            playing = not playing
            if playing:
                step_counter = 0
                last_step = int(time.monotonic() * 1000)
                print("Playing")
            else:
                print("Stopped")
        elif (row, col) == global_brightness_up_key:
            # Increase global brightness
            pixels.brightness = min(pixels.brightness + 0.1, 1.0)
            print(f"Global brightness: {pixels.brightness}")
        elif (row, col) == global_brightness_down_key:
            # Decrease global brightness
            pixels.brightness = max(pixels.brightness - 0.1, 0.1)
            print(f"Global brightness: {pixels.brightness}")
        else:
            # Handle normal sequence key presses
            if row < NUM_ROWS and col < SEQUENCE_LENGTH:
                step_index = col
                voice_index = current_voices[row]
                pattern_index = current_patterns[row]
                sequences[pattern_index][row][step_index] = not sequences[pattern_index][row][step_index]  # Toggle step state
                light_steps(row, step_index, sequences[pattern_index][row][step_index])  # Update LED
                voice_change_flag = True  # Set the flag for voice change
print("UI grid configured")
"""

# Main loop to process key events
def process_keys():
    event = keys.events.get()
    if event:
        handle_button_press(event)

# Light the current beat
def light_beat(step):
    for row in range(NUM_ROWS):
        led_index = row * SEQUENCE_LENGTH + step
        if 0 <= led_index < NUM_PIXELS:
            pixels[led_index] = (70, 20, 0)  # Red color for the beat indicator
    pixels.show()

# Main Loop with Shuffle
shuffle_amount = 0.0  # Adjust this value to control the shuffle amount (0.0 to 0.5)
last_step = int(time.monotonic() * 1000)

while True:
    # Update the start button state
    start_button.update()
    if start_button.fell:  # If the play button is pressed
        playing = not playing
        step_counter = 0
        last_step = int(time.monotonic() * 1000)
        print("*** Play:", playing)
        update_leds()

    if playing:
        now = int(time.monotonic() * 1000)
        diff = now - last_step
        if diff >= steps_millis:
            late_time = diff - steps_millis
            last_step = now - late_time // 2

            # Apply shuffle to every other step
            if step_counter % 2 == 0:
                time.sleep(shuffle_amount * steps_millis / 1000.0)

            light_beat(step_counter)  # Update beat indicator LED
            for i in range(NUM_VOICES):
                if sequences[current_patterns[i]][i][step_counter]:  # if a 1 at step seq, play it
                    play_drum(voice_colors[i])
            step_counter = (step_counter + 1) % SEQUENCE_LENGTH
            encoder_pos = encoder.position  # only check encoder while playing between steps
            knobbutton.update()  # Update knobbutton state
            if knobbutton.fell:
                # Handle encoder button press
                pass

    # Handle keypad events for the 12x8 matrix
    process_keys()

    # Handle the voice change outside the timing-critical section
    if encoder_pos != last_encoder_pos:
        encoder_delta = encoder_pos - last_encoder_pos
        last_encoder_pos = encoder_pos

    # Adjust BPM if the encoder was moved
    if encoder_pos != last_encoder_pos:
        encoder_delta = encoder_pos - last_encoder_pos
        bpm = bpm + (encoder_delta / 10)  # Adjust BPM by the encoder delta
        bpm = min(max(bpm, 60.0), 220.0)  # Clamp BPM between 60 and 220
        beat_time = 60.0 / bpm  # time length of a single beat
        beat_millis = beat_time * 1000.0
        steps_millis = beat_millis / steps_per_beat
        display.fill(0)
        display.print(f"{bpm:.1f}")
        last_encoder_pos = encoder_pos

    time.sleep(0.01)  # Short delay to prevent excessive CPU usage
