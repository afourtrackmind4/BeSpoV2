"""NanoUI I2C communication helper for the BeSpoV2 Pico sequencer.

This module encapsulates the I2C protocol used to communicate with the
Arduino Nano that handles all user interface elements (encoders,
buttons, 7‑segment display and indicator NeoPixels).

The protocol is intentionally simple so it can be reliably executed
inside the Pico's timing sensitive sequencer loop.

Incoming data (Nano -> Pico)
----------------------------
The Nano sends a 8 byte block whenever the Pico performs an I2C read.
Currently only the first two bytes are used::

    Byte 0 : signed encoder delta since last read
    Byte 1 : button state bitmask (1 = pressed)
    Bytes 2‑7 : reserved for future expansion

Outgoing commands (Pico -> Nano)
--------------------------------
Each write begins with a command byte followed by optional data.
Implemented commands are::

    0x01 <d0> <d1> <d2> <d3>
        Update the four digits of the 7‑segment display.

    0x02 <index> <r> <g> <b>
        Set UI NeoPixel ``index`` to the given RGB value.

    0x03 <brightness>
        Set overall NeoPixel brightness (0‑255).

The command set is intentionally small but can be extended in the
future without breaking existing functionality.
"""

from adafruit_bus_device.i2c_device import I2CDevice


class NanoUI:
    """High level helper for the UI Arduino."""

    def __init__(self, i2c, address=0x33):
        self.device = I2CDevice(i2c, address)
        self._in_buf = bytearray(8)

    def read_inputs(self):
        """Return ``(encoder_delta, buttons)``.

        ``encoder_delta`` is a signed integer in the range -128..127.
        ``buttons`` is a bitmask representing the current button states.
        """
        with self.device:
            self.device.readinto(self._in_buf)
        enc = int.from_bytes(self._in_buf[0:1], "big", signed=True)
        buttons = self._in_buf[1]
        return enc, buttons

    def set_display(self, digits):
        """Update the 7‑segment display.

        ``digits`` should be an iterable of four integers representing
        the raw segment value for each digit (0‑15 typically).
        """
        if len(digits) != 4:
            raise ValueError("expected four digits")
        out = bytearray(5)
        out[0] = 0x01
        for i, d in enumerate(digits):
            out[i + 1] = int(d) & 0xFF
        with self.device:
            self.device.write(out)

    def set_led(self, index, r, g, b):
        """Set a UI NeoPixel color."""
        out = bytearray((0x02, index & 0xFF, r & 0xFF, g & 0xFF, b & 0xFF))
        with self.device:
            self.device.write(out)

    def set_brightness(self, value):
        """Set UI NeoPixel brightness (0‑255)."""
        out = bytearray((0x03, value & 0xFF))
        with self.device:
            self.device.write(out)
