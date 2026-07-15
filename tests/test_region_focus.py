from types import SimpleNamespace

from src.vision.attendance_pipeline import RecognitionPipeline
from src.vision.region_focus import RegionFocusEngine, assign_regions, classify_color, compute_region_colors


class TestClassifyColor:
    def test_green(self):
        assert classify_color(85, 30.0, 60.0) == "g"

    def test_red(self):
        assert classify_color(15, 30.0, 60.0) == "r"

    def test_blue(self):
        assert classify_color(45, 30.0, 60.0) == "b"

    def test_boundary_green(self):
        assert classify_color(60.0, 30.0, 60.0) == "g"

    def test_boundary_red(self):
        assert classify_color(30.0, 30.0, 60.0) == "r"


class TestAssignRegions:
    def test_basic_split(self):
        students = [
            {"position": 500, "focus_score": 90},  # front row
            {"position": 400, "focus_score": 70},
            {"position": 300, "focus_score": 50},
            {"position": 200, "focus_score": 30},
            {"position": 100, "focus_score": 10},  # back row
        ]
        regions = assign_regions(students, num_regions=5)
        assert len(regions) == 5
        assert regions[0] == [90]
        assert regions[4] == [10]

    def test_multiple_per_region(self):
        students = [
            {"position": 500, "focus_score": 90},
            {"position": 480, "focus_score": 80},
            {"position": 100, "focus_score": 10},
            {"position": 90, "focus_score": 5},
        ]
        regions = assign_regions(students, num_regions=3)
        assert regions[0] == [90, 80]
        assert regions[2] == [10, 5]

    def test_empty(self):
        regions = assign_regions([], num_regions=5)
        assert len(regions) == 5
        assert all(len(v) == 0 for v in regions.values())

    def test_single_student(self):
        students = [{"position": 200, "focus_score": 50}]
        regions = assign_regions(students, num_regions=5)
        assert len(regions[0]) == 1
        assert len(regions[1]) == 0

    def test_all_same_position(self):
        students = [
            {"position": 200, "focus_score": 80},
            {"position": 200, "focus_score": 60},
        ]
        regions = assign_regions(students, num_regions=5)
        total = sum(len(v) for v in regions.values())
        assert total == 2


class TestComputeRegionColors:
    def test_all_colored(self):
        regions = {0: [90], 1: [50], 2: [15]}
        result = compute_region_colors(regions, 30.0, 60.0)
        assert result[0]["color"] == "g"
        assert result[1]["color"] == "b"
        assert result[2]["color"] == "r"

    def test_empty_region_off(self):
        regions = {0: [90], 1: [], 2: [15]}
        result = compute_region_colors(regions, 30.0, 60.0)
        assert result[1]["color"] == "off"
        assert result[1]["count"] == 0
        assert result[1]["median"] is None

    def test_median_computed(self):
        regions = {0: [80, 60, 70]}
        result = compute_region_colors(regions, 30.0, 60.0)
        assert result[0]["median"] == 70.0
        assert result[0]["count"] == 3

    def test_all_off(self):
        regions = {i: [] for i in range(5)}
        result = compute_region_colors(regions, 30.0, 60.0)
        for item in result:
            assert item["color"] == "off"


class TestRegionFocusEngine:
    def test_update_and_get_state(self):
        engine = RegionFocusEngine(num_regions=3, red_threshold=30.0, green_threshold=60.0)
        students = [
            {"user_id": "s1", "position": 500, "focus_score": 90},
            {"user_id": "s2", "position": 300, "focus_score": 50},
            {"user_id": "s3", "position": 100, "focus_score": 15},
        ]
        result = engine.update(students, now=1000.0)
        assert len(result) == 3
        colors = [r["color"] for r in result]
        assert colors == ["g", "b", "r"]
        cached = engine.get_region_state()
        assert cached == result

    def test_no_students(self):
        engine = RegionFocusEngine()
        result = engine.update([], now=1000.0)
        assert len(result) == 3
        all_off = all(r["color"] == "off" for r in result)
        assert all_off

    def test_different_num_regions(self):
        engine = RegionFocusEngine(num_regions=2)
        students = [
            {"position": 500, "focus_score": 90},
            {"position": 100, "focus_score": 10},
        ]
        result = engine.update(students, now=1000.0)
        assert len(result) == 2
        assert result[0]["color"] == "g"
        assert result[1]["color"] == "r"


def test_pipeline_uses_only_focus_rows_inside_window():
    pipeline = RecognitionPipeline.__new__(RecognitionPipeline)
    pipeline._confirmed_people = {"s1": SimpleNamespace(user_id="s1", current_status="present", bbox=[0, 100, 10, 200])}
    pipeline._metric_engine = SimpleNamespace(
        _students={
            "s1": SimpleNamespace(
                metric_rows={
                    "focus-ratio": [
                        {"t": 89.0, "value": 10.0},
                        {"t": 95.0, "value": 80.0},
                    ]
                }
            )
        }
    )
    pipeline._region_engine = RegionFocusEngine(num_regions=1)
    pipeline._region_window_seconds = 10.0

    pipeline._update_region_focus_locked(100.0)

    assert pipeline._region_state[0]["median"] == 80.0
