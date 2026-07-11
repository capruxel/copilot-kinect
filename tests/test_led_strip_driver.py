import json
import os
import tempfile

from src.led.led_strip_driver import MockLedDriver


class TestMockLedDriver:
    def test_update_writes_log(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.jsonl")
            driver = MockLedDriver(log_path=log_path)
            state = [
                {"region": 0, "color": "g", "median": 85.0, "count": 3},
                {"region": 1, "color": "off", "median": None, "count": 0},
            ]
            driver.update(state)

            assert os.path.exists(log_path)
            with open(log_path) as f:
                line = f.readline()
            entry = json.loads(line)
            assert entry["regions"] == state
            assert "t" in entry

    def test_update_twice_appends(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.jsonl")
            driver = MockLedDriver(log_path=log_path)
            driver.update([{"region": 0, "color": "g", "median": 90.0, "count": 1}])
            driver.update([{"region": 0, "color": "r", "median": 10.0, "count": 1}])

            with open(log_path) as f:
                lines = f.readlines()
            assert len(lines) == 2

    def test_get_status_reflects_last_update(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "test.jsonl")
            driver = MockLedDriver(log_path=log_path)
            state = [{"region": 0, "color": "b", "median": 45.0, "count": 2}]
            driver.update(state)
            status = driver.get_status()
            assert status["driver"] == "mock"
            assert status["region_states"] == state
            assert status["last_update"] > 0

    def test_get_status_default_empty(self):
        driver = MockLedDriver(log_path="/tmp/test_empty.jsonl")
        status = driver.get_status()
        assert status["region_states"] == []
        assert status["last_update"] == 0.0

    def test_close_noop(self):
        driver = MockLedDriver()
        driver.close()
