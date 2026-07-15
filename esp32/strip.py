import time

from machine import PWM, Pin

LED_PINS = (
    (25, 26, 27),  # front: R, G, B
    (32, 33, 14),  # middle: R, G, B
    (18, 19, 21),  # back: R, G, B
)
BRIGHTNESS = 80
PWM_FREQUENCY = 1000
BREATH_PERIOD_MS = 2000

leds = [[PWM(Pin(pin), freq=PWM_FREQUENCY, duty_u16=0) for pin in pins] for pins in LED_PINS]


def set_rgb(idx, red, green, blue):
    if idx < 0 or idx >= len(leds):
        return
    for pwm, value in zip(leds[idx], (red, green, blue)):
        pwm.duty_u16(max(0, min(255, value)) * 257)


def set_led(idx, color_name):
    colors = {
        "g": (0, BRIGHTNESS, 0),
        "r": (BRIGHTNESS, 0, 0),
        "b": (0, 0, BRIGHTNESS),
        "off": (0, 0, 0),
    }
    set_rgb(idx, *colors.get(color_name, colors["off"]))


def breathe_all():
    phase = time.ticks_ms() % BREATH_PERIOD_MS
    half_period = BREATH_PERIOD_MS // 2
    level = BRIGHTNESS * (half_period - abs(phase - half_period)) // half_period
    for idx in range(len(leds)):
        set_rgb(idx, 0, 0, level)
