import board
import adafruit_aw9523
import digitalio
import time
from adafruit_ticks import ticks_ms, ticks_diff, ticks_add
from digitalio import DigitalInOut, Direction, Pull
import keypad
from adafruit_seesaw import seesaw, rotaryio, digitalio
from adafruit_debouncer import Debouncer
from adafruit_ht16k33 import segments
import neopixel
import busio
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

# Global Variables
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

# Initialize I2C
i2c = board.STEMMA_I2C()

# Initialize AW9523
aw = adafruit_aw9523.AW9523(i2c, address=0x5B)# Configure AW9523 pins for input with external pull-ups
from digitalio import Direction

# Configure the first 5 pins as inputs with Debouncer
button_pins = [aw.get_pin(i) for i in range(5)]
buttons = []
for pin in button_pins:
    pin.direction = Direction.INPUT  # Set direction to input
    # Ensure you have external pull-up resistors
    buttons.append(Debouncer(pin))

# Define variables for button states
button_states = [False] * len(button_pins)


# Setup play button
start_button_in = DigitalInOut(board.D11)
start_button_in.pull = Pull.UP
start_button = Debouncer(start_button_in)

# Define row and column pins for the 8x8 matrix
row_pins = [board.D2, board.D3, board.D4, board.D5, board.D6, board.D7, board.D8, board.D9]
col_pins = [board.D10, board.MOSI, board.MISO, board.SCK, board.A0, board.A1, board.A2, board.A3]

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

# Initialize UART for MIDI output on D0 (TX)
uart = busio.UART(board.D0, baudrate=31250)

# Initialize MIDI over UART
midi = MIDI(midi_out=uart, out_channel=9)  # MIDI channel 10 is 9 in code (0-15 range)

# Initialize WS2811 LEDs on pin RX
num_pixels = 64
pixels = neopixel.NeoPixel(board.RX, num_pixels, auto_write=True)

# Update LEDs based on the current sequence (Rev 2)
def update_leds():
    for voice_index in range(num_drums):
        for step_index in range(sequence_length):
            light_steps(voice_index, step_index, sequence[voice_index][step_index])
    pixels.show()  # Ensure the LEDs are updated visually


# V1.1 Define colors for each voice
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

# Boot sequence for Neopixels
def neopixel_boot_sequence():
    for i in range(num_pixels):
        pixels[i] = (0, 70, 150)  # Blue color for boot sequence
        pixels.show()
        time.sleep(0.008)
    time.sleep(0.1)
    pixels.fill((0, 0, 0))
    pixels.show()


# Call the boot sequence
neopixel_boot_sequence()

# Define multiple patterns (Rev 1)
num_patterns = 4
sequences = [[[0] * sequence_length for _ in range(num_drums)] for _ in range(num_patterns)]

# Initialize to load the first pattern by default (Rev 1)
current_pattern = 0

def load_pattern(pattern_index):
    global sequence
    sequence = sequences[pattern_index]
    update_leds()  # Update LEDs to reflect the loaded pattern

# Toggle pattern selection (Rev 1)
def toggle_pattern():
    global current_pattern
    current_pattern = (current_pattern + 1) % num_patterns
    load_pattern(current_pattern)
    display.fill(0)
    display.print(f"Patt:{current_pattern+1}")


# Drum setup
drum_names = ["Bass", "Snar", "LTom", "MTom", "HTom", "Clav", "Clap", "Cowb", "Cymb", "OHat", "CHat"]
drum_notes = [36, 38, 41, 43, 45, 37, 39, 56, 49, 46, 42]  # general midi drum notes matched to 808

sequence = [
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

# Play drum function
def play_drum(note):
    midi.send(NoteOn(note, 120))  # Note on with velocity 120
    time.sleep(0.01)  # Short delay to simulate the note being played
    midi.send(NoteOff(note, 0))  # Note off

# V1.1 Define colors for each voice
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


# Light steps (v1.1)
def light_steps(voice_index, step_index, state):
    led_index = voice_index * 16 + step_index  # Map the voice and step to the LED index
    print(f"Debug: voice_index={voice_index}, step_index={step_index}, led_index={led_index}")  # Debugging
    color = voice_colors.get(voice_index, (8, 125, 60))  # Default to Purple if voice not found
    if 0 <= led_index < 64:  # Ensure LED index is within the valid range
        if state:
            pixels[led_index] = color  # Set color based on voice
        else:
            pixels[led_index] = (0, 0, 0)  # Off for inactive steps
        pixels.show()
    else:
        print(f"Error: led_index out of range: {led_index}")  # Debug out-of-range indices

# set the leds
for j in range(sequence_length):
    light_steps(curr_drum, j, sequence[curr_drum][j])
update_leds()

# Light the current beat
def light_beat(step):
    if 0 <= step < num_pixels:
        pixels[step] = (70, 20, 0)  # Red color for the beat indicator
        pixels.show()

# Toggle edit mode
def edit_mode_toggle():
    global edit_mode
    edit_mode = (edit_mode + 1) % num_modes
    print(f"Toggled edit mode to: {edit_mode}")  # Debugging
    display.fill(0)
    if edit_mode == 0:
        display.print(bpm)
    elif edit_mode == 1:
        display.print(drum_names[curr_drum])
    elif edit_mode == 2:
        display.print(f"Shfl:{shuffle_amount:.2f}")

def print_sequence():
    print("sequence = [ ")
    for k in range(num_drums):
        print(
            " [" + ",".join("1" if e else "0" for e in sequence[k]) + "], #",
            drum_names[k],
        )
    print("]")




# Print sequence for debugging
def print_sequence():
    print("sequence = [ ")
    for k in range(num_drums):
        print(" [" + ",".join("1" if e else "0" for e in sequence[k]) + "], #", drum_names[k])
    print("]")

# Initialize display
display = segments.Seg14x4(i2c, address=(0x71))
display.brightness = 1.0
display.fill(0)
display.show()
display.print(bpm)
display.show()

edit_mode = 0  # 0=bpm, 1=voices, 2=shuffle, 4=Patterns
num_modes = 4

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

# Handle button press events and set the flag for voice change
def handle_button_press(event):
    global voice_change_flag
    col, row = divmod(event.key_number, len(col_pins))
    if event.pressed:
        # Map the rows to voices, adjusting for your desired mapping
        if row % 4 == 0:
            voice_index = 0
        elif row % 4 == 1:
            voice_index = 1
        elif row % 4 == 2:
            voice_index = 2
        elif row % 4 == 3:
            voice_index = 3

        step_index = (row // 4) * 8 + col  # Each column corresponds to a step within the voice
        if 0 <= voice_index < num_drums:
            sequence[voice_index][step_index] = not sequence[voice_index][step_index]  # Toggle step state
            light_steps(voice_index, step_index, sequence[voice_index][step_index])  # Update LED
            voice_change_flag = True  # Set the flag for voice change
            print(f"Pressed: Row {row}, Col {col} | Voice Index: {voice_index} | Step Index: {step_index} | State: {sequence[voice_index][step_index]}")
    else:
        print(f"Released: Row {row}, Col {col}")

def read_buttons():
    for i, button in enumerate(buttons):
        button.update()
        if button.fell:  # Button press detected
            print(f"Button {i} pressed")
        elif button.rose:  # Button release detected
            print(f"Button {i} released")

# Main Loop with Shuffle
shuffle_amount = 0.5  # Adjust this value to control the shuffle amount (0.0 to 0.5)
while True:
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
            for i in range(num_drums):
                if sequence[i][step_counter]:  # if a 1 at step seq, play it
                    play_drum(drum_notes[i % len(drum_notes)])
            light_steps(curr_drum, step_counter, sequence[curr_drum][step_counter])
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

    # Handle keypad events for the 8x8 matrix
    event = keys.events.get()
    if event:
        handle_button_press(event)

    # Handle the voice change outside the timing-critical section
    if encoder_pos != last_encoder_pos:
        encoder_delta = encoder_pos - last_encoder_pos
        if edit_mode == 1:
            curr_drum = (curr_drum + encoder_delta) % num_drums
            update_leds()
            display.fill(0)
            display.print(drum_names[curr_drum % len(drum_names)])
            print(f"Changing voice from {curr_drum} to {(curr_drum + encoder_delta) % num_drums}")
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
        # Read button states from AW9523 (low priority)
    read_buttons()

    # Example: Handle button presses
    for i, pin in enumerate(button_pins):
        if not pin.value:  # Button pressed (assuming active low)
            print(f"Button {i} pressed")
    read_buttons()
    time.sleep(0.1)  # Small delay for debouncing
