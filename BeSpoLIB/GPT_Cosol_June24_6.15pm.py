import board
import busio
from digitalio import DigitalInOut, Pull
import keypad
from adafruit_seesaw import seesaw, rotaryio, digitalio as seesaw_digitalio
from adafruit_debouncer import Debouncer
from adafruit_ht16k33 import segments
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
import neopixel
import time
from adafruit_ticks import ticks_ms, ticks_diff, ticks_add

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
voice_change_flag = False

# Initialize I2C
i2c = board.STEMMA_I2C()

# Setup play button
start_button_in = DigitalInOut(board.GP3)
start_button_in.pull = Pull.UP
start_button = Debouncer(start_button_in)

# Define row and column pins for the 12x8 matrix
col_pins = [board.GP6, board.GP7, board.GP8, board.GP9, board.GP10, board.GP11, board.GP12, board.GP13]
row_pins = [board.GP14, board.GP15, board.GP16, board.GP17, board.GP18, board.GP19, board.GP20, board.GP21, board.GP22, board.GP26, board.GP27, board.GP28]

# Initialize the KeyMatrix using the defined row and column pins
keys = keypad.KeyMatrix(row_pins, col_pins, columns_to_anodes=True)

# Rotary Encoder Setup
rotary_seesaw = seesaw.Seesaw(i2c, addr=0x36)
encoder = rotaryio.IncrementalEncoder(rotary_seesaw)
last_encoder_pos = 0
rotary_seesaw.pin_mode(24, seesaw_digitalio.INPUT_PULLUP)  # setup the button pin
knobbutton_in = seesaw_digitalio.DigitalIO(rotary_seesaw, 24)
knobbutton = Debouncer(knobbutton_in)
encoder_pos = encoder.position

# Initialize UART for MIDI output on GP0 (TX)
uart = busio.UART(board.GP0, baudrate=31250)

# Initialize MIDI over UART
midi = MIDI(midi_out=uart, out_channel=9)  # MIDI channel 10 is 9 in code (0-15 range)

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

# Initialize sequence and current voice/pattern pointers
num_patterns = 4
sequences = [[[0] * sequence_length for _ in range(num_rows)] for _ in range(num_patterns)]
current_voices = [0] * num_rows
current_patterns = [0] * num_rows
