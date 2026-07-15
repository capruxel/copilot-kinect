# ESP32 RGB LED Firmware

## Hardware

- ESP32 32E (WROOM)
- 3 x common-cathode, 4-pin RGB LEDs for the front, middle, and back regions
- Recommended: 9 x 220-330 ohm current-limiting resistors, one per color channel
- Temporary option: 3 x 220-330 ohm resistors, one between each LED's common cathode and GND

| Region | Red | Green | Blue |
| ------ | --- | ----- | ---- |
| Front  | GPIO 25 | GPIO 26 | GPIO 27 |
| Middle | GPIO 32 | GPIO 33 | GPIO 14 |
| Back   | GPIO 18 | GPIO 19 | GPIO 21 |

Connect each RGB pin to its GPIO through a current-limiting resistor. Connect
each LED's common-cathode pin to ESP32 GND.

With only three resistors, keep the R/G/B pins separate and place one resistor
between each LED's common cathode and GND. This temporary wiring is suitable
for single-color states; the firmware therefore uses only blue for fallback.

Detailed wiring guide: [`docs/esp32_common_cathode_rgb_led_wiring.md`](../docs/esp32_common_cathode_rgb_led_wiring.md)

## Setup

1. Install MicroPython on ESP32 (see https://micropython.org/download/ESP32_GENERIC/)
2. Install mpremote:
   ```bash
   pip install mpremote
   ```
3. Edit `boot.py` and replace `YOUR_WIFI_SSID` and `YOUR_WIFI_PASSWORD`.
4. Edit `main.py` and replace `HOST` with the Kinect machine IP.
5. Copy the files to the board:
   ```bash
   mpremote cp boot.py :boot.py + cp strip.py :strip.py + cp main.py :main.py + soft-reset
   ```
   If the device is not auto-detected, specify the serial port:
   ```bash
   mpremote connect /dev/cu.usbserial-10 cp boot.py :boot.py + cp strip.py :strip.py + cp main.py :main.py + soft-reset
   ```

## Protocol

NDJSON over TCP (port 8765). ESP32 connects as the client and sends
`{"t":"hello"}` on connection.

Host to ESP32:

```json
{"t":"state","regions":[{"region":0,"color":"g","median":85.0,"count":3}]}
```

- Region `0`: front
- Region `1`: middle
- Region `2`: back
- Colors: `"g"` (green), `"r"` (red), `"b"` (blue), `"off"`

ESP32 to host:

- `{"t":"hello"}`
- `{"t":"pong"}` every 10 seconds

## Fallback

If no data is received for 10 seconds, all three LEDs display a synchronized
blue breathing effect until data resumes. The same effect runs between TCP
reconnection attempts.
