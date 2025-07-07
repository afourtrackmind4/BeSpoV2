# BeSpoV2

Experimental drum sequencer.  Earlier revisions placed all input and
output on the Raspberry Pi Pico.  The current approach offloads the user
interface to an Arduino Nano which communicates with the Pico via I2C.

```
Pico  -> step grid NeoPixels, MIDI, sequencing
Nano  -> encoders, buttons, 7‑segment display, UI NeoPixels

The Pico still scans the 8x8 step button matrix while the Nano handles all rotary encoders and other buttons. UI updates occur over I2C using the simple protocol implemented in `pico/nanoui.py`.
```

All source is contained in this repository.  The `pico` directory holds
the CircuitPython code for the Pico and `nano` contains the Arduino
sketch driving the UI.

See `docs/pinout.md` for wiring information.

## Running on the Pico

Upload the contents of the `pico` directory to the CircuitPython
filesystem.  `main.py` implements the sequencer logic and communicates
with the Nano UI helper using the `nanoui` module.

Set ``DEBUG = True`` at the top of `main.py` for verbose console output.

The `nano` directory contains `nano_ui.ino`, an Arduino sketch that must
be loaded onto the Nano.  It scans the encoders and buttons and updates
the UI NeoPixels and 7-segment display in response to commands from the
Pico.

Wiring details are in `docs/pinout.md`.
