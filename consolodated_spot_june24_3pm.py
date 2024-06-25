import board
import neopixel
import busio
from digitalio import DigitalInOut, Direction, Pull
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

# LED Setup
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

# MIDI Setup
uart = busio.UART(MIDI_OUT_PIN, baudrate=31250)
midi = MIDI(midi_out=uart, out_channel=9)  # MIDI channel 10 is 9 in code (0-15 range)

# Display Setup
i2c = board.STEMMA_I2C()
display = segments.Seg14x4(i2c, address=(0x71))
display.brightness = 1.0
display.fill(0)
display.show()
display.print(bpm)
display.show()

# Rotary Encoder Setup
rotary_seesaw = seesaw.Seesaw(i2c, addr=0x36)
encoder = rotaryio.IncrementalEncoder(rotary_seesaw)
last_encoder_pos = 0
#  rotary_seesaw.pin_mode(24, digitalio.Pull.UP)  # setup the button pin
knobbutton_in = seesaw_digitalio.DigitalIO(rotary_seesaw, 24)
knobbutton = Debouncer(knobbutton_in)
encoder_pos = encoder.position

# Play Button Setup
start_button_in = DigitalInOut(board.GP3)
start_button_in.pull = Pull.UP
start_button = Debouncer(start_button_in)

# Manual GPIO configuration for key matrix
# Set columns as outputs

"""
column_pins = [digitalio.DigitalInOut(pin) for pin in COL_PINS]
for col_pin in column_pins:
    col_pin.direction = digitalio.Direction.OUTPUT
    col_pin.value = False  # Set initial state to low

# Set rows as inputs with pull-ups
row_pins = [digitalio.DigitalInOut(pin) for pin in ROW_PINS]
for row_pin in row_pins:
    row_pin.direction = digitalio.Direction.INPUT
    row_pin.pull = digitalio.Pull.UP
"""
python
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

# Function to play a drum note
def play_drum(note):
    midi.send(NoteOn(note, 120))  # Note on with velocity 120
    time.sleep(0.01)  # Short delay to simulate the note being played
    midi.send(NoteOff(note, 0))  # Note off

# Function to update LEDs based on the current sequence and pointers
def update_leds():
    for row in range(NUM_ROWS):
        for step in range(SEQUENCE_LENGTH):
            led_index = row * SEQUENCE_LENGTH + step  # Calculate LED index
            voice = current_voices[row]
            pattern = current_patterns[row]
            state = sequences[pattern][row][step]
            color = voice_colors[voice] if state else (0, 0, 0)
            pixels[led_index] = color
    pixels.show()

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
