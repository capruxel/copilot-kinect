# ESP32 LED Strip Firmware

## Hardware

- ESP32 32E (WROOM)
- 5 x WS2812B LED strips, 30 LEDs each
- GPIO pins: 13, 12, 14, 27, 33

## Setup

1. Install MicroPython on ESP32 (see https://micropython.org/download/ESP32_GENERIC/)
2. Install mpremote:
   ```bash
   pip install mpremote
   ```
3. Copy files to the board:
   ```bash
   mpremote cp boot.py :boot.py
   mpremote cp strip.py :strip.py
   mpremote cp main.py :main.py
   mpremote soft-reset
   ```
   Or in one shot:
   ```bash
   mpremote cp boot.py :boot.py + cp strip.py :strip.py + cp main.py :main.py + soft-reset
   ```
   If the device is not auto-detected, specify the serial port:
   ```bash
   mpremote connect /dev/cu.usbserial-10 cp boot.py :boot.py + cp strip.py :strip.py + cp main.py :main.py + soft-reset
   ```
4. Edit `boot.py` — replace `YOUR_WIFI_SSID` and `YOUR_WIFI_PASSWORD`
5. Edit `main.py` — replace `HOST` with the Kinect machine IP

## Protocol

NDJSON over TCP (port 8765). ESP32 connects as client, sends `{"t":"hello"}` on connect.

Host → ESP32:
- `{"t":"state","regions":[{"region":0,"color":"g","median":85.0,"count":3},...]}`

ESP32 → Host:
- `{"t":"hello"}`
- `{"t":"pong"}` (every 10s)

Colors: `"g"` (green), `"r"` (red), `"b"` (blue), `"off"` (no lights).

## Fallback

If no data received for 10 seconds, all strips switch to rainbow pattern.
