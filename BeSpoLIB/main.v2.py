# main.py (V1.0)
from global_config import *
from led_control import update_leds, light_beat
from key_matrix import process_keys
from midi_control import play_drum
from pattern_management import toggle_pattern, load_pattern
from adafruit_ht16k33 import segments
from adafruit_seesaw import seesaw, rotaryio, digitalio
from adafruit_debouncer import Debouncer
import busio
import time
from adafruit_ticks import ticks_ms, ticks_diff, ticks_add

edit_mode = 0  # Initial edit mode (0=bpm, 1=voices, 2=shuffle, 3=patterns)

# Setup I2C
i2c = board.STEMMA_I2C()

# Initialize display
display = segments.Seg14x4(i2c, address=(0x71))
display.brightness = 1.0
display.fill(0)
display.show()
display.print(bpm)
display.show()

# Initialize rotary encoder
rotary_seesaw = seesaw.Seesaw(i2c, addr=0x36)
encoder = rotaryio.IncrementalEncoder(rotary_seesaw)
last_encoder_pos = 0
rotary_seesaw.pin_mode(24, rotary_seesaw.INPUT_PULLUP)  # setup the button pin
knobbutton_in = digitalio.DigitalIO(rotary_seesaw, 24)
knobbutton = Debouncer(knobbutton_in)
encoder_pos = encoder.position

# Setup play button
start_button_in = DigitalInOut(board.GP3)
start_button_in.pull = Pull.UP
start_button = Debouncer(start_button_in)

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

# Main Loop with Shuffle
shuffle_amount = 0.0  # Adjust this value to control the shuffle amount (0.0 to 0.5)
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
            for i in range(NUM_VOICES):
                if sequence[i][step_counter]:  # if a 1 at step seq, play it
                    play_drum(drum_notes[i % len(drum_notes)])
            light_steps(curr_drum, step_counter, sequence[curr_drum][step_counter])
            step_counter = (step_counter + 1) % SEQUENCE_LENGTH
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

    # Handle keypad events for the 12x8 matrix
    process_keys()

    # Handle the voice change outside the timing-critical section
    if encoder_pos != last_encoder_pos:
        encoder_delta = encoder_pos - last_encoder_pos
        if edit_mode == 1:  # Assuming edit_mode 1 is for voice
            row_to_edit = (curr_drum // NUM_ROWS) % NUM_ROWS  # Adjust based on current drum
            scroll_voice(row_to_edit, encoder_delta)
            display.fill(0)
            display.print(drum_names[current_voices[row_to_edit] % len(drum_names)])
            last_encoder_pos = encoder_pos
        elif edit_mode == 3:  # Assuming edit_mode 3 is for pattern
            row_to_edit = (curr_drum // NUM_ROWS) % NUM_ROWS  # Adjust based on current drum
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
