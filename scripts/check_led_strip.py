"""CLI sanity check for region-focus engine and LED driver.

Usage:
    uv run python scripts/check_led_strip.py
"""

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.vision.region_focus import RegionFocusEngine
from src.led.led_strip_driver import MockLedDriver

def main():
    engine = RegionFocusEngine(num_regions=5, red_threshold=30.0, green_threshold=60.0)
    driver = MockLedDriver(log_path=PROJECT_ROOT / "data" / "led_strip_log.jsonl")

    now = time.time()
    students = [
        {"position": 500, "focus_score": 90},
        {"position": 400, "focus_score": 75},
        {"position": 350, "focus_score": 60},
        {"position": 200, "focus_score": 25},
        {"position": 100, "focus_score": 10},
    ]
    regions = engine.update(students, now)
    driver.update(regions)

    print("region states:")
    for r in regions:
        print(f"  region {r['region']}: color={r['color']}, median={r['median']}, count={r['count']}")

    status = driver.get_status()
    assert status["region_states"] == regions
    assert status["driver"] == "mock"

    with open(driver.log_path) as f:
        logged = json.loads(f.readline())
    print(f"\nlogged to {driver.log_path}: {json.dumps(logged, ensure_ascii=False)}")
    print("\nOK")

if __name__ == "__main__":
    main()
