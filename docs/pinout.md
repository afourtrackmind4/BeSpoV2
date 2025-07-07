# BeSpoV2 Pico/Nano Wiring

This document summarises the connections between the Raspberry Pi Pico
running CircuitPython and the Arduino Nano responsible for the user
interface.

## I2C

```
Pico GP4  <->  Nano A4 (SDA)
Pico GP5  <->  Nano A5 (SCL)
```

Both lines should have 3.3k pull‑ups to 3.3 V.  Use a level shifter if
the Nano is running at 5 V.

## NeoPixels

```
Step grid LEDs  : Pico GP1
UI NeoPixels    : Nano D2
```

## Other IO

Encoders, buttons and additional LEDs are connected directly to the
Nano.  The exact mapping can be customised in `nano_ui.ino`.

---

This wiring keeps all real‑time user interaction off the Pico so the
sequencer can maintain accurate musical timing.

## Step grid buttons

The 8x8 button matrix used for sequencing is wired directly to the Pico.
Column pins are GP6-GP13 and row pins are GP14-GP21 as configured in
`pico/main.py`.
