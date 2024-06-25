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
# Beat timing assumes 4/4 time signature,4 beats per measure, 1/4 note gets the beat
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


# Define row and column pins for the 4x4 matrix
row_pins = [board.D2, board.D3, board.D4, board.D5]
col_pins = [board.D6, board.D7, board.D8, board.D9]

# Initialize the KeyMatrix using the defined row and column pins
keys = keypad.KeyMatrix(row_pins, col_pins, columns_to_anodes=True)


# Setup LEDs
leds = adafruit_aw9523.AW9523(i2c, address=0x5B)  # both jumperes soldered on board
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

# initialize UART for MIDI output on D0 (TX)
uart = busio.UART(board.D0, baudrate=31250)

# Initialize MIDI over UART
midi = MIDI(midi_out=uart, out_channel=9)  # MIDI channel 10 is 9 in code (0-15 range)

# Initialize WS2811 LEDs on pin A1
num_pixels = 16
pixels = neopixel.NeoPixel(board.A1, num_pixels, auto_write=True)


drum_names = [
    "Bass", "Snar", "LTom", "MTom", "HTom", "Clav", "Clap", "Cowb", "Cymb", "OHat", "CHat",
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
        leds.set_constant_current(step, offled)


def light_beat(step):
    leds.set_constant_current(step, highled)
    update_leds()


def edit_mode_toggle():
    # pylint: disable=global-statement
    global edit_mode
    # pylint: disable=used-before-assignment
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

            light_beat(step_counter)  # brighten current step
            for i in range(num_drums):
                if sequence[i][
                    step_counter
                ]:  # if there's a 1 at the step for the seq, play it
                    play_drum(drum_notes[i])
            light_steps(
                step_counter, sequence[curr_drum][step_counter]
            )  # return led to step value
            step_counter = (step_counter + 1) % sequence_length
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

 # Handle keypad events for the 4x4 matrix
    event = keys.events.get()
    if event:
        if event.pressed:
            row, col = divmod(event.key_number, 4)
            print(f"Button pressed at Row {row + 1}, Col {col + 1}")
            i = row * 4 + col
            sequence[curr_drum][i] = not sequence[curr_drum][i]  # toggle step
            light_steps(i, sequence[curr_drum][i])  # toggle light
            update_leds()

    if encoder_pos != last_encoder_pos:
        encoder_delta = encoder_pos - last_encoder_pos
        if edit_mode == 0:
            bpm = bpm + (encoder_delta/10)# or (encoder_delta * 5)
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
            update_leds()
        last_encoder_pos = encoder_pos
