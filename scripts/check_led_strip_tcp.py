"""Run a lightweight TCP server for testing the ESP32 LEDs."""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.led.led_strip_driver import TcpLedStripDriver  # noqa: E402

PATTERNS = (
    ("r", "g", "b"),
    ("g", "b", "r"),
    ("b", "r", "g"),
    ("off", "off", "off"),
)


def main():
    driver = TcpLedStripDriver(port=8765)
    driver.start()
    print("Listening on 0.0.0.0:8765; press Ctrl-C to stop")

    try:
        while True:
            for colors in PATTERNS:
                if not driver.get_status()["connected"]:
                    print("Waiting for ESP32 connection...")
                    while not driver.get_status()["connected"]:
                        time.sleep(0.1)
                regions = [{"region": i, "color": color} for i, color in enumerate(colors)]
                driver.update(regions)
                print("connected:", driver.get_status()["connected"], "colors:", colors)
                time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
