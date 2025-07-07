"""BeSpoV2 CircuitPython sequencer with Arduino Nano UI."""

import time
from adafruit_ticks import ticks_ms, ticks_diff, ticks_add
import board
import busio
import keypad
import neopixel
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

from nanoui import NanoUI

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEBUG = False  # set True for verbose logging

# Step grid button matrix (8 columns x 8 rows)
COL_PINS = [
    board.GP6, board.GP7, board.GP8, board.GP9,
    board.GP10, board.GP11, board.GP12, board.GP13,
]
ROW_PINS = [
    board.GP14, board.GP15, board.GP16, board.GP17,
    board.GP18, board.GP19, board.GP20, board.GP21,
]

NUM_STEPS = 16
NUM_DRUMS = 11

# NeoPixel step grid on the Pico
GRID_PIN = board.GP1
GRID_LEDS = 64

# I2C connection to the Nano UI helper
I2C_SDA = board.GP4
I2C_SCL = board.GP5
NANO_ADDR = 0x33

# MIDI output
MIDI_TX = board.GP0

# Drum note mapping (General MIDI)
DRUM_NOTES = [36, 38, 41, 43, 45, 37, 39, 56, 49, 46, 42]
DRUM_NAMES = [
    "Bass", "Snar", "LTom", "MTom", "HTom",
    "Clav", "Clap", "Cowb", "Cymb", "OHat", "CHat",
]

# Sequence data: drum x step matrix
sequence = [
    [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],  # bass
    [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],  # snare
] + [[0]*NUM_STEPS for _ in range(NUM_DRUMS-2)]

BPM = 120.0
STEPS_PER_BEAT = 4

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def debug(*args):
    if DEBUG:
        print(*args)


def calc_timing():
    beat_time = 60.0 / BPM
    beat_ms = beat_time * 1000.0
    return beat_ms / STEPS_PER_BEAT


steps_millis = calc_timing()


# ---------------------------------------------------------------------------
# Hardware setup
# ---------------------------------------------------------------------------

# I2C and Nano helper
i2c = busio.I2C(I2C_SCL, I2C_SDA)
ui = NanoUI(i2c, address=NANO_ADDR)

# Step grid LEDs
pixels = neopixel.NeoPixel(GRID_PIN, GRID_LEDS, auto_write=False)

# Button matrix
keys = keypad.KeyMatrix(ROW_PINS, COL_PINS, columns_to_anodes=True)

# MIDI interface
midi = MIDI(midi_out=busio.UART(MIDI_TX, baudrate=31250), out_channel=9)

# UI state
current_drum = 0
playing = False
step_counter = 0

# Button debounce
last_buttons = 0


# ---------------------------------------------------------------------------
# UI functions
# ---------------------------------------------------------------------------

def update_display():
    value = int(BPM)
    digits = [value // 1000 % 10, value // 100 % 10, value // 10 % 10, value % 10]
    ui.set_display(digits)


def light_step(index, active):
    pixels[index] = (8, 125, 60) if active else (0, 0, 0)


def refresh_grid():
    for idx in range(NUM_STEPS):
        light_step(idx, sequence[current_drum][idx])
    pixels.show()


update_display()
refresh_grid()

# Timestamp for step scheduling
last_step = ticks_ms()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
while True:
    enc_delta, buttons = ui.read_inputs()

    # button[0] toggles play
    if buttons & 0x01 and not last_buttons & 0x01:
        playing = not playing
        step_counter = 0
        last_step = ticks_ms()
        debug("Play", playing)
    last_buttons = buttons

    if enc_delta:
        if DEBUG:
            debug("Encoder", enc_delta)
        if playing:
            pass  # ignore while playing to keep timing consistent
        else:
            BPM = min(220.0, max(60.0, BPM + enc_delta))
            steps_millis = calc_timing()
            update_display()

    event = keys.events.get()
    if event and event.pressed:
        col, row = divmod(event.key_number, len(ROW_PINS))
        idx = row * len(COL_PINS) + col
        if row < NUM_DRUMS and col < NUM_STEPS:
            sequence[row][col] = not sequence[row][col]
            light_step(col, sequence[current_drum][col])
            pixels.show()
            debug("Toggle", row, col, sequence[row][col])

    now = ticks_ms()
    if playing and ticks_diff(now, last_step) >= steps_millis:
        last_step = ticks_add(last_step, int(steps_millis))
        for drum, drum_seq in enumerate(sequence):
            if drum_seq[step_counter]:
                midi.send(NoteOn(DRUM_NOTES[drum], 120))
        light_step(step_counter, True)
        pixels.show()
        time.sleep(0.01)
        for drum, drum_seq in enumerate(sequence):
            if drum_seq[step_counter]:
                midi.send(NoteOff(DRUM_NOTES[drum], 0))
        light_step(step_counter, sequence[current_drum][step_counter])
        pixels.show()
        step_counter = (step_counter + 1) % NUM_STEPS

