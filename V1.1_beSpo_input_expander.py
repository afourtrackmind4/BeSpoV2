import board
import time
from adafruit_ticks import ticks_ms, ticks_diff, ticks_add
from digitalio import DigitalInOut, Pull
import keypad
from adafruit_seesaw import seesaw, rotaryio, digitalio
from adafruit_debouncer import Debouncer
from adafruit_ht16k33 import segments
import neopixel
import busio
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

print("Section 1: Initialization and Setup")

# Global Variables
num_pixels = 64
num_rows = 4
steps_per_row = num_pixels // num_rows  # This should be 16
pixels = neopixel.NeoPixel(board.GP2, num_pixels, auto_write=True)

num_steps = 16
num_drums = 11
bpm = 120.0
beat_time = 60.0 / bpm
beat_millis = beat_time * 1000.0
steps_per_beat = 4
steps_millis = beat_millis / steps_per_beat
step_counter = 0
sequence_length = 16
curr_drum = 0
playing = False
voice_change_flag = False  # Ensure this is included
num_patterns = 4
current_pattern = 0  # Initialize current_pattern here
edit_mode = 0  # Initialize edit mode
num_modes = 4  # Number of edit modes
current_voices = [0] * num_rows
current_patterns = [0] * num_rows

# Initialize I2C
i2c = board.STEMMA_I2C()

# Setup play button
start_button_in = DigitalInOut(board.GP3)
start_button_in.pull = Pull.UP
start_button = Debouncer(start_button_in)

# Initialize UART for MIDI output on D0 (TX)
uart = busio.UART(board.GP0, baudrate=31250)

# Initialize MIDI over UART
midi = MIDI(midi_out=uart, out_channel=9)  # MIDI channel 10 is 9 in code (0-15 range)

# Initialize display
display = segments.Seg14x4(i2c, address=(0x71))
display.brightness = 1.0
display.fill(0)
display.show()
display.print(bpm)
display.show()

# Display startup message
print("The beatspot")
display.fill(0)
display.show()
display.marquee("THE", 0.03, loop=False)
time.sleep(0.2)
display.marquee("BEAT", 0.05, loop=False)
time.sleep(0.2)
display.marquee("SPOT", 0.04, loop=False)
time.sleep(0.05)
display.marquee("BPM", 0.02, loop=False)
time.sleep(0.2)
display.marquee(str(bpm), 0.1, loop=False)

# Boot sequence for Neopixels
def neopixel_boot_sequence():
    for i in range(num_pixels):
        pixels[i] = (0, 70, 150)  # Blue color for boot sequence
        pixels.show()
        time.sleep(0.004)
    time.sleep(0.01)
    pixels.fill((0, 0, 0))
    pixels.show()

# Call the boot sequence
neopixel_boot_sequence()

print("Initialization complete")
print("Section 2: Matrix Configuration and Key Handling")

# Define row and column pins for the 12x8 matrix
col_pins = [board.GP6, board.GP7, board.GP8, board.GP9, board.GP10, board.GP11, board.GP12, board.GP13]
row_pins = [board.GP14, board.GP15, board.GP16, board.GP17, board.GP18, board.GP19, board.GP20, board.GP21, board.GP22, board.GP26, board.GP27, board.GP28]

# Initialize the KeyMatrix using the defined row and column pins
keys = keypad.KeyMatrix(row_pins, col_pins, columns_to_anodes=True)

# STEMMA QT Rotary encoder setup
rotary_seesaw = seesaw.Seesaw(i2c, addr=0x36)
encoder = rotaryio.IncrementalEncoder(rotary_seesaw)
last_encoder_pos = 0
rotary_seesaw.pin_mode(24, rotary_seesaw.INPUT_PULLUP)  # setup the button pin
knobbutton_in = digitalio.DigitalIO(rotary_seesaw, 24)
knobbutton = Debouncer(knobbutton_in)
encoder_pos = encoder.position

print("Matrix configuration complete")

print("Section 3: Pattern and Voice Management")

# Drum setup
drum_names = ["Bass", "Snar", "LTom", "MTom", "HTom", "Clav", "Clap", "Cowb", "Cymb", "OHat", "CHat"]
drum_notes = [36, 38, 41, 43, 45, 37, 39, 56, 49, 46, 42]  # general midi drum notes matched to 808

# Define default pattern for testing and debugging
default_pattern = [
    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],  # bass drum
    [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],  # snare
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # low tom
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # mid tom
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # high tom
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # rimshot/claves
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # handclap/maracas
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # cowbell
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # cymbal
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # hihat open
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],  # hihat closed
]

# Initialize the sequences with the default pattern
sequences = [default_pattern.copy() for _ in range(num_patterns)]

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

# Load pattern
def load_pattern(pattern_index):
    global sequence
    sequence = sequences[pattern_index]
    update_leds() # Update LEDs to reflect the loaded pattern

# Toggle pattern selection
def toggle_pattern():
    global current_pattern
    current_pattern = (current_pattern + 1) % num_patterns
    load_pattern(current_pattern)
    display.fill(0)
    display.print(f"Patt:{current_pattern+1}")

# Scroll through voices for a specific row
def scroll_voice(row, direction):
    current_voices[row] = (current_voices[row] + direction) % len(voice_colors)
    update_leds()

# Scroll through patterns for a specific row
def scroll_pattern(row, direction):
    current_patterns[row] = (current_patterns[row] + direction) % num_patterns
    update_leds()

print("Pattern and voice management complete")

print("Section 4: Main Loop and LED Updates")

# Play drum function
def play_drum(note):
    midi.send(NoteOn(note, 120))  # Note on with velocity 120
    time.sleep(0.01)  # Short delay to simulate the note being played
    midi.send(NoteOff(note, 0))  # Note off

# Light steps
def light_steps(voice_index, step_index, state):
    led_index = voice_index * steps_per_row + step_index  # Map the voice and step to the LED index
    if led_index < num_pixels:  # Ensure LED index is within the 64 LEDs
        color = voice_colors.get(voice_index, (8, 125, 60))  # Default to Purple if voice not found
        if state:
            pixels[led_index] = color  # Set color based on voice
        else:
            pixels[led_index] = (0, 0, 0)  # Off for inactive steps
        pixels.show()

# Update LEDs based on the current sequence and pointers
def update_leds():
    for row in range(num_rows):
        for step in range(steps_per_row):
            led_index = row * steps_per_row + step
            if led_index < num_pixels:  # Ensure we're within the 64 LEDs
                voice = current_voices[row]
                pattern = current_patterns[row]
                state = sequences[pattern][row][step]
                color = voice_colors[voice] if state else (0, 0, 0)
                pixels[led_index] = color
    pixels.show()

# Light the current beat
def light_beat(step):
    for row in range(num_rows):  # Ensure it iterates through rows
        led_index = row * steps_per_row + step
        if led_index < num_pixels:
            pixels[led_index] = (70, 20, 0)  # Red color for the beat indicator
    pixels.show()

# Toggle edit mode
def edit_mode_toggle():
    global edit_mode
    edit_mode = (edit_mode + 1) % num_modes
    display.fill(0)
    if edit_mode == 0:
        display.print(bpm)
    elif edit_mode == 1:
        display.print(drum_names[curr_drum])
    elif edit_mode == 2:
        display.print(f"Shfl:{shuffle_amount:.2f}")

# Print sequence for debugging
def print_sequence():
    print("sequence = [ ")
    for k in range(num_drums):
        print(" [" + ",".join("1" if e else "0" for e in sequence[k]) + "], #", drum_names[k])
    print("]")

# Define keys for scrolling in the extended matrix
scroll_voice_up_key = (8, 0)  # Example position, adjust as needed
scroll_voice_down_key = (8, 1)  # Example position, adjust as needed
scroll_pattern_up_key = (9, 0)  # Example position, adjust as needed
scroll_pattern_down_key = (9, 1)  # Example position, adjust as needed

# Handle button press events and set the flag for voice change
def handle_button_press(event):
    global voice_change_flag
    col, row = divmod(event.key_number, len(col_pins))
    print(f"Button pressed: {event.key_number}, Row: {row}, Col: {col}")
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
            if row < num_rows and col < steps_per_row:
                step_index = col
                voice_index = current_voices[row]
                pattern_index = current_patterns[row]
                if step_index < len(sequences[pattern_index][row]):  # Ensure step_index is within the bounds of the sequence
                    sequences[pattern_index][row][step_index] = not sequences[pattern_index][row][step_index]  # Toggle step state
                    light_steps(row, step_index, sequences[pattern_index][row][step_index])  # Update LED
                    voice_change_flag = True  # Set the flag for voice change

update_leds()
print("Setup Complete")

# Main Loop with Shuffle
shuffle_amount = 0.0  # Adjust this value to control the shuffle amount (0.0 to 0.5)
sequence = sequences[current_pattern]

while True:
    sequence = sequences[current_pattern]
    # Update the start button state
    start_button.update()
    if start_button.fell:  # If the play button is pressed
        if playing:
            print_sequence()
        playing = not playing
        step_counter = 0
        last_step = int(ticks_add(ticks_ms(), -steps_millis))
        print("*** Play:", playing)
        update_leds()

    if playing:
        now = ticks_ms()
        diff = ticks_diff(now, last_step)
        if diff >= steps_millis:
            late_time = ticks_diff(int(diff), int(steps_millis))
            last_step = ticks_add(now, -late_time // 2)

            # Apply shuffle to every other step
            if step_counter % 2 == 0:
                time.sleep(shuffle_amount * steps_millis / 1000.0)

            light_beat(step_counter)  # Update beat indicator LED

            # Debugging prints to check indices and arrays
            print(f"step_counter: {step_counter}")
            print(f"sequence length: {len(sequence)}")  # Check length of sequence
            for i in range(min(num_rows, len(sequence))):  # Ensure we stay within bounds
                print(f"Checking sequence[{i}]: {sequence[i]}")
                if step_counter < len(sequence[i]):  # Ensure step_counter is within the length of sequence[i]
                    if sequence[i][step_counter]:  # Check if step_counter is within bounds
                        if i < len(drum_notes):
                            play_drum(drum_notes[i % len(drum_notes)])
                        else:
                            print(f"Index {i} out of range for drum_notes (length {len(drum_notes)})")
                        light_steps(i, step_counter, sequence[i][step_counter])
                    else:
                        print(f"step_counter {step_counter} out of range for sequence[{i}] (length {len(sequence[i])})")

            print(f"curr_drum: {curr_drum}")  # Print curr_drum value
            if curr_drum < len(sequence):
                if step_counter < len(sequence[curr_drum]):
                    light_steps(curr_drum, step_counter, sequence[curr_drum][step_counter])
                else:
                    print(f"step_counter {step_counter} out of range for sequence[{curr_drum}] (length {len(sequence[curr_drum])})")
            else:
                print(f"curr_drum {curr_drum} out of range (length {len(sequence)})")

            step_counter = (step_counter + 1) % sequence_length
            encoder_pos = encoder.position  # only check encoder while playing between steps
            knobbutton.update()  # Update knobbutton state
            if knobbutton.fell:
                edit_mode_toggle()
    else:
        # Check the encoder all the time when not playing
        encoder_pos = encoder.position
        knobbutton.update()  # Update knobbutton state
        if knobbutton.fell:  # Change edit mode, refresh display
            edit_mode_toggle()

    # Handle keypad events for the 10x10 matrix
    event = keys.events.get()
    if event:
        handle_button_press(event)

    # Handle the voice change outside the timing-critical section
    if encoder_pos != last_encoder_pos:
        encoder_delta = encoder_pos - last_encoder_pos
        if edit_mode == 1:  # Assuming edit_mode 1 is for voice
            row_to_edit = (curr_drum // num_rows) % num_rows  # Adjust based on current drum
            scroll_voice(row_to_edit, encoder_delta)
            display.fill(0)
            display.print(drum_names[current_voices[row_to_edit] % len(drum_names)])
            last_encoder_pos = encoder_pos
        elif edit_mode == 3:  # Assuming edit_mode 3 is for pattern
            row_to_edit = (curr_drum // num_rows) % num_rows  # Adjust based on current drum
            scroll_pattern(row_to_edit, encoder_delta)
            display.fill(0)
            display.print(f"Patt:{current_patterns[row_to_edit] + 1}")
            last_encoder_pos = encoder_pos

    # Adjust BPM if the encoder was moved and edit mode is 0 (BPM mode)
    if encoder_pos != last_encoder_pos:
        encoder_delta = encoder_pos - last_encoder_pos
        if edit_mode == 0:
            bpm = bpm + (encoder_delta / 10)  # Adjust BPM by the encoder delta
            bpm = min(max(bpm, 60.0), 220.0)  # Clamp BPM between 60 and 220
            beat_time = 60.0 / bpm  # time length of a single beat
            beat_millis = beat_time * 1000.0
            steps_millis = beat_millis / steps_per_beat
            display.fill(0)
            display.print(f"{bpm:.1f}")
        elif edit_mode == 2:
            shuffle_amount = shuffle_amount + (encoder_delta / 100)
            shuffle_amount = min(max(shuffle_amount, 0.0), 0.5)  # Clamp shuffle amount between 0.0 and 0.5
            display.fill(0)
            display.print(f"Shfl:{shuffle_amount:.2f}")
        elif edit_mode == 3:
            toggle_pattern()
        last_encoder_pos = encoder_pos

print("Main loop and LED updates complete")
