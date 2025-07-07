/*
 * nano_ui.ino - Arduino Nano UI controller for BeSpoV2
 *
 * The Nano reads all user inputs (rotary encoders, buttons) and drives the
 * NeoPixel based 7-segment display and indicator LEDs.  Communication with the
 * Raspberry Pi Pico sequencer is handled via I2C where the Nano is a slave at
 * address 0x33.
 *
 * Protocol overview
 * -----------------
 * Pico writes commands (first byte = command):
 *   0x01 d0 d1 d2 d3    -> set digits on 7-seg display
 *   0x02 idx r g b      -> set UI NeoPixel at index
 *   0x03 brightness     -> set overall NeoPixel brightness
 *
 * When the Pico reads from the Nano it receives 8 bytes:
 *   [0]  encoder delta since last read (signed)
 *   [1]  button state bitmask
 *   [2..7] reserved for future use
 */

#include <Wire.h>
#include <Adafruit_NeoPixel.h>

#define I2C_ADDR 0x33
#define UI_PIN   2        // NeoPixel DIN
#define NUM_PIXELS 16     // Adjust to the actual number of UI pixels

Adafruit_NeoPixel pixels(NUM_PIXELS, UI_PIN, NEO_GRB + NEO_KHZ800);

volatile int8_t encDelta = 0;
volatile uint8_t buttonMask = 0;

// Simple example using a single encoder and one button.
const int ENC_A = 3;
const int ENC_B = 4;
const int BTN   = 5;

int lastEnc = 0;

void handleReceive(int count) {
  if (count < 1) return;
  uint8_t cmd = Wire.read();
  if (cmd == 0x01 && count >= 5) {
    for (int i = 0; i < 4; i++) {
      if (!Wire.available()) break;
      uint8_t val = Wire.read();
      // very primitive 7-seg emulation: pixel per digit
      if (i < NUM_PIXELS) pixels.setPixelColor(i, val ? 0xFFFFFF : 0);
    }
    pixels.show();
  } else if (cmd == 0x02 && count >= 5) {
    uint8_t idx = Wire.read();
    uint8_t r = Wire.read();
    uint8_t g = Wire.read();
    uint8_t b = Wire.read();
    if (idx < NUM_PIXELS) {
      pixels.setPixelColor(idx, pixels.Color(r, g, b));
      pixels.show();
    }
  } else if (cmd == 0x03 && count >= 2) {
    uint8_t br = Wire.read();
    pixels.setBrightness(br);
    pixels.show();
  } else {
    // discard the rest
    while (Wire.available()) Wire.read();
  }
}

void handleRequest() {
  uint8_t out[8] = { (uint8_t)encDelta, buttonMask, 0,0,0,0,0,0 };
  Wire.write(out, sizeof(out));
  encDelta = 0; // reset after report
}

void setup() {
  Wire.begin(I2C_ADDR);
  Wire.onReceive(handleReceive);
  Wire.onRequest(handleRequest);

  pixels.begin();
  pixels.fill(0);
  pixels.show();

  pinMode(ENC_A, INPUT_PULLUP);
  pinMode(ENC_B, INPUT_PULLUP);
  pinMode(BTN, INPUT_PULLUP);
  lastEnc = digitalRead(ENC_A);
}

void loop() {
  // very naive encoder handling for demonstration
  int a = digitalRead(ENC_A);
  if (a != lastEnc) {
    if (digitalRead(ENC_B) != a) encDelta++; else encDelta--;
    lastEnc = a;
  }

  if (!digitalRead(BTN)) buttonMask |= 0x01; else buttonMask &= ~0x01;
}
