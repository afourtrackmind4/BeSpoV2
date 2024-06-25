# midi_control.py (V1.0)
from global_config import MIDI_OUT_PIN
import busio
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff
import time

# Initialize UART for MIDI output
uart = busio.UART(MIDI_OUT_PIN, baudrate=31250)

# Initialize MIDI over UART
midi = MIDI(midi_out=uart, out_channel=9)  # MIDI channel 10 is 9 in code (0-15 range)

# Play drum function
def play_drum(note):
    midi.send(NoteOn(note, 120))  # Note on with velocity 120
    time.sleep(0.01)  # Short delay to simulate the note being played
    midi.send(NoteOff(note, 0))  # Note off



"""# midi_control.py (V1.0)
from global_config import MIDI_OUT_PIN
import busio
from adafruit_midi import MIDI
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

# Initialize UART for MIDI output
uart = busio.UART(MIDI_OUT_PIN, baudrate=31250)

# Initialize MIDI over UART
midi = MIDI(midi_out=uart, out_channel=9)  # MIDI channel 10 is 9 in code (0-15 range)

# Play drum function
def play_drum(note):
    midi.send(NoteOn(note, 120))  # Note on with velocity 120
    time.sleep(0.01)  # Short delay to simulate the note being played
    midi.send(NoteOff(note, 0))  # Note off
"""
