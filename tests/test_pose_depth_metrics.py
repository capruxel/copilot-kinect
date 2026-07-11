from src.vision.pose_depth_metrics import (
    PoseDepthMetricEngine,
    StudentMetricState,
    _clamp,
    _distance,
    _format_time_label,
    _safe_mean,
    _safe_std,
    _trim_metric_rows,
    _trim_time_series,
)


def test_clamp_within_range():
    assert _clamp(5, 0, 10) == 5


def test_clamp_below_min():
    assert _clamp(-1, 0, 10) == 0


def test_clamp_above_max():
    assert _clamp(15, 0, 10) == 10


def test_distance():
    d = _distance((0, 0), (3, 4))
    assert abs(d - 5.0) < 1e-9


def test_distance_zero():
    assert _distance((5, 5), (5, 5)) == 0.0


def test_safe_mean_empty():
    assert _safe_mean([]) == 0.0


def test_safe_mean_single():
    assert _safe_mean([5.0]) == 5.0


def test_safe_mean_multiple():
    assert _safe_mean([1, 2, 3, 4, 5]) == 3.0


def test_safe_std_empty():
    assert _safe_std([]) == 0.0


def test_safe_std_single():
    assert _safe_std([5.0]) == 0.0


def test_safe_std_two_values():
    assert _safe_std([0, 2]) == 1.0


def test_format_time_label():
    assert _format_time_label(0) == "08:00:00"


def test_trim_time_series_removes_old():
    now = 1000.0
    points = [(500, 1), (800, 2), (900, 3)]
    trimmed = _trim_time_series(points, now, 200)
    assert len(trimmed) == 2


def test_trim_time_series_keeps_all_within_window():
    now = 1000.0
    points = [(850, 1), (900, 2), (950, 3)]
    assert _trim_time_series(points, now, 200) == points


def test_trim_metric_rows_removes_old():
    now = 1000.0
    rows = [{"t": 500}, {"t": 800}, {"t": 900}]
    trimmed = _trim_metric_rows(rows, now, 200)
    assert len(trimmed) == 2


def test_trim_metric_rows_empty():
    assert _trim_metric_rows([], 1000.0, 200) == []


_UNSET = object()


class TestPoseDepthMetricEngineHandRaise:
    def setup_method(self):
        self.engine = PoseDepthMetricEngine()
        self.shoulder_center = (100.0, 100.0)
        self.shoulder = (100.0, 100.0)
        self.torso_length = 100.0

    def is_raised(self, wrist, elbow, shoulder=_UNSET):
        return self.engine._is_hand_raised(
            wrist_point=wrist,
            elbow_point=elbow,
            shoulder_point=self.shoulder if shoulder is _UNSET else shoulder,
            shoulder_center=self.shoulder_center,
            torso_length=self.torso_length,
        )

    def test_clear_vertical_arm_raise_counts(self):
        assert self.is_raised(wrist=(108.0, 36.0), elbow=(106.0, 70.0))

    def test_bent_classroom_hand_raise_counts(self):
        assert self.is_raised(wrist=(112.0, 64.0), elbow=(118.0, 94.0))

    def test_low_head_near_shoulder_pose_does_not_count(self):
        assert not self.is_raised(wrist=(92.0, 84.0), elbow=(88.0, 128.0))

    def test_reading_or_holding_book_far_from_shoulder_does_not_count(self):
        assert not self.is_raised(wrist=(300.0, 40.0), elbow=(190.0, 160.0))

    def test_missing_elbow_or_shoulder_does_not_count(self):
        assert not self.is_raised(wrist=(108.0, 36.0), elbow=None)
        assert not self.is_raised(wrist=(108.0, 36.0), elbow=(106.0, 70.0), shoulder=None)

    def test_hand_high_and_straight_above_counts(self):
        assert self.is_raised(wrist=(105.0, 10.0), elbow=(104.0, 55.0))

    def test_wrist_at_same_height_as_shoulder_does_not_count(self):
        assert not self.is_raised(wrist=(105.0, 100.0), elbow=(104.0, 120.0))


class TestPoseDepthMetricEngineStillness:
    def setup_method(self):
        self.engine = PoseDepthMetricEngine()
        self.state = StudentMetricState()
        self.keypoint_map = {
            0: (100.0, 80.0),
            5: (80.0, 120.0),
            6: (120.0, 120.0),
            11: (90.0, 200.0),
            12: (110.0, 200.0),
            9: (70.0, 100.0),
            10: (130.0, 100.0),
        }
        self.bbox_center = (100.0, 150.0)
        self.torso_length = 80.0
        self.now = 1000.0

    def test_first_call_returns_false(self):
        result = self.engine._calculate_stillness_flag(
            self.state, self.keypoint_map, self.bbox_center, self.torso_length, self.now
        )
        assert result is False
        assert self.state.previous_frame_at == self.now

    def test_same_position_on_second_call_returns_true(self):
        self.engine._calculate_stillness_flag(
            self.state, self.keypoint_map, self.bbox_center, self.torso_length, self.now
        )
        result = self.engine._calculate_stillness_flag(
            self.state, self.keypoint_map, self.bbox_center, self.torso_length, self.now + 0.5
        )
        assert result is True


class TestPoseDepthMetricEngineDepth:
    def setup_method(self):
        self.engine = PoseDepthMetricEngine()

    def test_depth_at_with_none_frame_returns_none(self):
        assert self.engine._depth_at(None, (100, 100), "kinect") is None


class TestPoseDepthMetricEngineUpdate:
    def setup_method(self):
        self.engine = PoseDepthMetricEngine()

    def test_update_student_minimal_no_crash(self):
        user_id = "student_1"
        frame_shape = (480, 640)
        bbox = [50, 60, 200, 250]
        pose_detection = {
            "keypoints": [
                [320, 120],
                [340, 110],
                [300, 110],
                None,
                None,
                [280, 200],
                [360, 200],
                None,
                None,
                None,
                None,
                [290, 320],
                [350, 320],
            ],
        }
        self.engine.update_student(
            user_id=user_id,
            frame_shape=frame_shape,
            bbox=bbox,
            pose_detection=pose_detection,
            depth_frame=None,
            depth_source_mode="kinect",
            peer_centers=[],
            now=1000.0,
        )
        assert user_id in self.engine._students
