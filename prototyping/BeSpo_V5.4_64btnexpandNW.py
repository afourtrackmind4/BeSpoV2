import time
from adafruit_ticks import ticks_ms, ticks_diff, ticks_add
import board
from digitalio import DigitalInOut, Pull
import keypad
import adafruit_aw9523
import usb_midi
from adafruit_seesaw import seesaw, rotaryio, digitalio
from adafruit_debouncer import Debouncer
from adafruit_ht16k33 import segments
import neopixel

# Add the following imports
import busio
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff



# define I2C
i2c = board.STEMMA_I2C()

num_steps = 16  # number of steps/switches
num_drums = 11  # primary 808 drums used here, but you can use however many you like
# Beat timing assumes 4/4 time sig,4 beatspermeasure, 1/4 note beat
bpm = 120.0  # default BPM
beat_time = 60.0 / bpm  # time length of a single beat
beat_millis = beat_time * 1000.0  # time length of single beat in milliseconds
steps_per_beat = 4  # subdivide beats down to to 16th notes
steps_millis = (
    beat_millis / steps_per_beat
)  # time length of a beat subdivision, e.g. 1/16th note

step_counter = 0  # goes from 0 to length of sequence - 1
sequence_length = 16  # how many notes stored in a sequence
curr_drum = 0
playing = False


# Setup button
start_button_in = DigitalInOut(board.A2)
start_button_in.pull = Pull.UP
start_button = Debouncer(start_button_in)

# Setup switches
switch_pins = (
    board.A3, board.RX, board.MOSI, board.MISO, board.SCK, board.A0
)
switches = keypad.Keys(switch_pins, value_when_pressed=False, pull=True)

# Define row and column pins for the 8x8 matrix using the input expander
# Initialize the AW9523 input expander for the 8x8 matrix
matrix_expander = adafruit_aw9523.AW9523(i2c, address=0x5B)  # using a different address

# Define new row and column pins for the 8x8 matrix using the expander
row_pins = [matrix_expander.get_pin(i) for i in range(8)]
col_pins = [matrix_expander.get_pin(i + 8) for i in range(8)]

# Initialize the KeyMatrix using the expander pins
keys = keypad.KeyMatrix(
    [matrix_expander.get_pin(i) for i in range(8)],
    [matrix_expander.get_pin(i + 8) for i in range(8)],
    columns_to_anodes=True
)

# Configure the row pins as inputs with pull-up resistors
for i in range(8):
    matrix_expander.pin_mode(i, adafruit_aw9523.AW9523.INPUT)

# Configure the column pins as outputs
for i in range(8, 16):
    matrix_expander.pin_mode(i, adafruit_aw9523.AW9523.OUTPUT)

# Setup LEDs
leds = adafruit_aw9523.AW9523(i2c, address=0x5B)  # both jumpers soldered on board
for led in range(num_steps):  # turn them off
    leds.set_constant_current(led, 0)
leds.LED_modes = 0xFFFF  # constant current mode
leds.directions = 0xFFFF  # output

# Values for LED brightness 0-255
offled = 0
dimled = 2
midled = 20
highled = 150

for led in range(num_steps):  # dramatic boot up light sequence
    leds.set_constant_current(led, dimled)
    time.sleep(0.05)
time.sleep(0.5)

# STEMMA QT Rotary encoder setup
rotary_seesaw = seesaw.Seesaw(i2c, addr=0x36)  # default address is 0x36
encoder = rotaryio.IncrementalEncoder(rotary_seesaw)
last_encoder_pos = 0
rotary_seesaw.pin_mode(24, rotary_seesaw.INPUT_PULLUP)  # setup the button pin
knobbutton_in = digitalio.DigitalIO(rotary_seesaw, 24)  # use seesaw digitalio
knobbutton = Debouncer(knobbutton_in)  # create debouncer object for button
encoder_pos = -encoder.position

# Initialize UART for MIDI output on D0 (TX)
uart = busio.UART(board.D0, baudrate=31250)

# Initialize MIDI over UART
midi = MIDI(midi_out=uart, out_channel=9)  # MIDI channel 10 is 9 in code (0-15 range)

# Initialize WS2811 LEDs on pin A1
num_pixels = 16
pixels = neopixel.NeoPixel(board.A1, num_pixels, auto_write=True)

def neopixel_boot_sequence():
    # Example boot sequence: light up each LED in sequence
    for i in range(num_pixels):
        pixels[i] = (0, 0, 255)  # Example: Blue color for boot sequence
        pixels.show()
        time.sleep(0.05)
    time.sleep(0.5)
    # Turn off all pixels after the sequence
    pixels.fill((0, 0, 0))
    pixels.show()

# Call the boot sequence
neopixel_boot_sequence()


drum_names = [
    "Bass", "Snar", "LTom", "MTom", "HTom",
    "Clav", "Clap", "Cowb", "Cymb", "OHat", "CHat",
]
drum_notes = [
    36, 38, 41, 43, 45, 37, 39, 56, 49, 46, 42,
]  # general midi drum notes matched to 808

# default starting sequence needs to match number of drums in num_drums
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

# play_drum function
def play_drum(note):
    midi.send(NoteOn(note, 120))  # Note on with velocity 120
    time.sleep(0.01)  # Short delay to simulate the note being played
    midi.send(NoteOff(note, 0))  # Note off


def light_steps(step, state):
    if state:
        leds.set_constant_current(step, midled)
    else:
        leds.set_constant_current### Part 5: LED Functions and Sequence Printing


def light_steps(step, state):
    if state:
        leds.set_constant_current(step, midled)
    else:
        leds.set_constant_current(step, offled)

def light_beat(step):
    # Turn off all pixels first
    # pixels.fill((0, 0, 0))
    # Light up the current step
    pixels[step] = (0, 255, 0)  # Example: Red color for the beat indicator
    pixels.show()

def neopixel_boot_sequence():
    # Example boot sequence: light up each LED in sequence
    for i in range(num_pixels):
        pixels[i] = (0, 0, 255)  # Example: Blue color for boot sequence
        pixels.show()
        time.sleep(0.05)
    time.sleep(0.01)
    # Turn off all pixels after the sequence
    pixels.fill((0, 0, 0))
    pixels.show()

def edit_mode_toggle():
    global edit_mode
    edit_mode = (edit_mode + 1) % num_modes
    display.fill(0)
    if edit_mode == 0:
        display.print(bpm)
    elif edit_mode == 1:
        display.print(drum_names[curr_drum])

def print_sequence():
    print("sequence = [ ")
    for k in range(num_drums):
        print(
            " [" + ",".join("1" if e else "0" for e in sequence[k]) + "], #",
            drum_names[k],
        )
    print("]")

def update_leds():
    for i in range(num_steps):
        if sequence[curr_drum][i]:
            pixels[i] = (8, 125, 60)  # Purple for active steps
        else:
            pixels[i] = (0, 0, 0)  # Off for inactive steps

# set the leds
for j in range(sequence_length):
    light_steps(j, sequence[curr_drum][j])
update_leds()


display = segments.Seg14x4(i2c, address=(0x71))
display.brightness = 0.3
display.fill(0)
display.show()
display.print(bpm)
display.show()

edit_mode = 0  # 0=bpm, 1=voices
num_modes = 2

print("The beatspot")

display.fill(0)
display.show()
display.marquee("THE", 0.05, loop=False)
time.sleep(0.5)
display.marquee("BEAT", 0.075, loop=False)
time.sleep(0.5)
display.marquee("SPOT", 0.05, loop=False)
time.sleep(1)
display.marquee("BPM", 0.05, loop=False)
time.sleep(0.75)
display.marquee(str(bpm), 0.1, loop=False)

while True:
    start_button.update()
    if start_button.fell:  # pushed encoder button plays/stops transport
        if playing is True:
            print_sequence()
        playing = not playing
        step_counter = 0
        last_step = int(ticks_add(ticks_ms(), -steps_millis))
        print("*** Play:", playing)

    if playing:
        now = ticks_ms()
        diff = ticks_diff(now, last_step)
        if diff >= steps_millis:
            late_time = ticks_diff(int(diff), int(steps_millis))
            last_step = ticks_add(now, -late_time // 2)

            light_beat(step_counter)  # Update beat indicator LED
            for i in range(num_drums):
                if sequence[i][step_counter]:  # if a 1 at step seq, play it
                    play_drum(drum_notes[i])
            light_steps(step_counter, sequence[curr_drum][step_counter]) # rtnLED-spval
            step_counter = (step_counter + 1) % sequence_length
            update_leds()
            encoder_pos = (
                -encoder.position
            )  # only check encoder while playing between steps
            knobbutton.update()
            if knobbutton.fell:
                edit_mode_toggle()
    else:  # check the encoder all the time when not playing
        encoder_pos = -encoder.position
        knobbutton.update()
        if knobbutton.fell:  # change edit mode, refresh display
            edit_mode_toggle()

    # Handle keypad events for the 8x8 matrix
    event = keys.events.get()
    if event:
        if event.pressed:
            row, col = divmod(event.key_number, 8)
            print(f"Button pressed at Row {row + 1}, Col {col + 1}")
            i = row * 8 + col
            sequence[curr_drum][i] = not sequence[curr_drum][i]  # toggle step
            light_steps(i, sequence[curr_drum][i])  # toggle light
            update_leds()

    if encoder_pos != last_encoder_pos:
        encoder_delta = encoder_pos - last_encoder_pos
        if edit_mode == 0:
            bpm = bpm + (encoder_delta/10)
            bpm = min(max(bpm, 60.0), 220.0)
            beat_time = 60.0 / bpm  # time length of a single beat
            beat_millis = beat_time * 1000.0
            steps_millis = beat_millis / steps_per_beat
            display.fill(0)
            display.print(f'{bpm:.1f}')
        if edit_mode == 1:
            curr_drum = (curr_drum + encoder_delta) % num_drums
            # quickly set the step leds
            for i in range(sequence_length):
                light_steps(i, sequence[curr_drum][i])
            display.print(drum_names[curr_drum])
        last_encoder_pos = encoder_pos

# Add the new key scanning logic here
for col in range(8, 16):
    matrix_expander.digital_write(col, False)  # Drive the current column low
    for row in range(8):
        if not matrix_expander.digital_read(row):  # Check if the row is low (button pressed)
            print(f"Button pressed at Row {row + 1}, Col {col - 8 + 1}")
    matrix_expander.digital_write(col, True)  # Set the column back to high
time.sleep(0.01)  # Small delay to debounce


# Test the KeyMatrix setup by scanning for key presses
while True:
    event = keys.events.get()
    if event:
        if event.pressed:
            print(f"Key pressed: {event.key_number}")
        elif event.released:
            print(f"Key released: {event.key_number}")
