import machine
import neopixel

PINS = [13, 12, 14, 27, 33]
LED_COUNT = 30
BRIGHTNESS = 80

strips = [neopixel.NeoPixel(machine.Pin(p), LED_COUNT) for p in PINS]


def color_hex(c):
    return {"g": (0, BRIGHTNESS, 0), "r": (BRIGHTNESS, 0, 0), "b": (0, 0, BRIGHTNESS), "off": (0, 0, 0)}.get(
        c, (0, 0, 0)
    )


def set_strip(idx, color_name):
    if idx < 0 or idx >= len(strips):
        return
    rgb = color_hex(color_name)
    for i in range(len(strips[idx])):
        strips[idx][i] = rgb
    strips[idx].write()


def rainbow(idx):
    if idx < 0 or idx >= len(strips):
        return
    strip = strips[idx]
    n = len(strip)
    for i in range(n):
        r = int(BRIGHTNESS * max(0, min(1, 1 - abs(i / (n / 3) - 1))))
        g = int(BRIGHTNESS * max(0, min(1, 1 - abs(i / (n / 3) - 2))))
        b = int(BRIGHTNESS * max(0, min(1, 1 - abs(i / (n / 3) - 3))))
        strip[i] = (r, g, b)
    strip.write()


def rainbow_all():
    for i in range(len(strips)):
        rainbow(i)
