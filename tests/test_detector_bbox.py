from src.vision.detector import PersonDetector, _env_float, _env_bool, _env_int


def detector():
    return PersonDetector('/tmp')


class TestBboxMath:
    def setup_method(self):
        self.d = detector()

    def test_bbox_iou_overlapping(self):
        iou = self.d._bbox_iou([0, 0, 10, 10], [5, 5, 15, 15])
        assert abs(iou - 25 / 175.0) < 1e-9

    def test_bbox_iou_no_overlap(self):
        assert self.d._bbox_iou([0, 0, 10, 10], [20, 20, 30, 30]) == 0.0

    def test_bbox_iou_contained(self):
        iou = self.d._bbox_iou([0, 0, 20, 20], [5, 5, 15, 15])
        assert abs(iou - 100 / 400.0) < 1e-9

    def test_bbox_center(self):
        cx, cy = self.d._bbox_center([10, 20, 30, 40])
        assert (cx, cy) == (20.0, 30.0)

    def test_bbox_center_distance(self):
        d = self.d._bbox_center_distance([0, 0, 10, 10], [10, 0, 20, 10])
        assert abs(d - 10.0) < 1e-9

    def test_bbox_max_side(self):
        assert self.d._bbox_max_side([0, 0, 30, 20]) == 30.0

    def test_current_bbox_area(self):
        assert self.d._current_bbox_area([0, 0, 10, 20]) == 200.0

    def test_boxes_likely_same_person_via_iou(self):
        assert self.d._boxes_likely_same_person(
            [0, 0, 10, 10], [2, 2, 8, 8],
            iou_threshold=0.1, center_ratio=0.5,
            area_ratio_limit=2.0, overlap_ratio=0.3,
        )

    def test_boxes_not_same_person(self):
        assert not self.d._boxes_likely_same_person(
            [0, 0, 10, 10], [50, 50, 60, 60],
            iou_threshold=0.1, center_ratio=0.3,
            area_ratio_limit=1.5, overlap_ratio=0.3,
        )

    def test_deduplicate_no_duplicates(self):
        candidates = [
            {'bbox': [0, 0, 10, 10], 'confidence': 0.9},
            {'bbox': [50, 50, 60, 60], 'confidence': 0.8},
        ]
        result = self.d._deduplicate_detection_boxes(candidates)
        assert len(result) == 2

    def test_deduplicate_removes_overlap(self):
        candidates = [
            {'bbox': [0, 0, 20, 20], 'confidence': 0.9},
            {'bbox': [2, 2, 18, 18], 'confidence': 0.8},
        ]
        result = self.d._deduplicate_detection_boxes(candidates)
        assert len(result) == 1

    def test_intersection_over_min_area(self):
        overlap = self.d._bbox_intersection_over_min_area(
            [0, 0, 10, 10], [5, 5, 15, 15]
        )
        assert abs(overlap - 25.0 / 100.0) < 1e-9


class TestPoseMethods:
    def setup_method(self):
        self.d = detector()

    def test_bbox_torso_point(self):
        cx, ty = self.d._bbox_torso_point([0, 0, 10, 20])
        assert (cx, ty) == (5.0, 8.4)

    def test_bbox_torso_point_float_input(self):
        cx, ty = self.d._bbox_torso_point([1.5, 2.5, 11.5, 22.5])
        assert (cx, ty) == (6.5, 10.9)

    def test_coerce_pose_arrays_pads_to_min_length(self):
        det = {
            'keypoints': [[1.0, 2.0], [3.0, 4.0]],
            'keypoint_conf': [0.5, 0.6],
        }
        pts, conf = self.d._coerce_pose_arrays(det, min_length=17)
        assert len(pts) == 17
        assert len(conf) == 17
        assert pts[0] == [1.0, 2.0]
        assert conf[1] == 0.6
        assert pts[2] == [0.0, 0.0]
        assert conf[2] == 0.0

    def test_coerce_pose_arrays_empty_arrays(self):
        det = {'keypoints': [], 'keypoint_conf': []}
        pts, conf = self.d._coerce_pose_arrays(det, min_length=17)
        assert len(pts) == 17
        assert len(conf) == 17
        assert all(p == [0.0, 0.0] for p in pts)
        assert all(c == 0.0 for c in conf)

    def test_coerce_pose_arrays_missing_keys(self):
        pts, conf = self.d._coerce_pose_arrays({}, min_length=5)
        assert len(pts) == 5
        assert len(conf) == 5

    def test_coerce_pose_arrays_none_points_padded(self):
        det = {
            'keypoints': [None, [1.0, 2.0]],
            'keypoint_conf': [0.3, 0.4],
        }
        pts, conf = self.d._coerce_pose_arrays(det, min_length=5)
        assert pts[0] == [0.0, 0.0]
        assert pts[1] == [1.0, 2.0]
        assert pts[4] == [0.0, 0.0]
        assert conf[4] == 0.0

    def test_pose_torso_depth_cm_median_of_five(self):
        profile = {0: 100.0, 5: 120.0, 6: 110.0, 11: 130.0, 12: 90.0}
        result = self.d._pose_torso_depth_cm(profile)
        assert result == 110.0

    def test_pose_torso_depth_cm_partial(self):
        profile = {5: 200.0, 11: 180.0}
        result = self.d._pose_torso_depth_cm(profile)
        assert result == 200.0

    def test_pose_torso_depth_cm_empty(self):
        assert self.d._pose_torso_depth_cm({}) is None

    def test_pose_torso_depth_cm_ignores_none(self):
        profile = {0: None, 5: 100.0, 6: None}
        result = self.d._pose_torso_depth_cm(profile)
        assert result == 100.0

    def test_user_id_for_match_student_id_wins(self):
        match = {'student_id': 'S123', 'label': 'John'}
        assert self.d._user_id_for_match(match) == 'S123'

    def test_user_id_for_match_label_fallback(self):
        match = {'label': 'John'}
        assert self.d._user_id_for_match(match) == 'John'

    def test_user_id_for_match_empty_student_id(self):
        match = {'student_id': '', 'label': 'Jane'}
        assert self.d._user_id_for_match(match) == 'Jane'

    def test_user_id_for_match_label_only(self):
        assert self.d._user_id_for_match({'label': 'Alice'}) == 'Alice'


class TestEnvHelpers:
    def test_env_float_valid(self, monkeypatch):
        monkeypatch.setenv('TEF_TEST', '3.14')
        assert _env_float('TEF_TEST', 0.0) == 3.14

    def test_env_float_empty(self, monkeypatch):
        monkeypatch.setenv('TEF_TEST', '')
        assert _env_float('TEF_TEST', 1.5) == 1.5

    def test_env_float_missing(self, monkeypatch):
        monkeypatch.delenv('TEF_MISSING', raising=False)
        assert _env_float('TEF_MISSING', 2.5) == 2.5

    def test_env_float_invalid(self, monkeypatch):
        monkeypatch.setenv('TEF_TEST', 'not_a_number')
        assert _env_float('TEF_TEST', 0.0) == 0.0

    def test_env_float_whitespace(self, monkeypatch):
        monkeypatch.setenv('TEF_TEST', '  42.5  ')
        assert _env_float('TEF_TEST', 0.0) == 42.5

    def test_env_float_negative(self, monkeypatch):
        monkeypatch.setenv('TEF_TEST', '-8.25')
        assert _env_float('TEF_TEST', 0.0) == -8.25

    def test_env_bool_true_variants(self, monkeypatch):
        for val in ['1', 'true', 'yes', 'on', 'TRUE', 'Yes', 'ON']:
            monkeypatch.setenv('TEB_TEST', val)
            assert _env_bool('TEB_TEST', False) is True

    def test_env_bool_false_variants(self, monkeypatch):
        for val in ['0', 'false', 'no', 'off', 'FALSE', 'No', 'OFF']:
            monkeypatch.setenv('TEB_TEST', val)
            assert _env_bool('TEB_TEST', True) is False

    def test_env_bool_empty(self, monkeypatch):
        monkeypatch.setenv('TEB_TEST', '')
        assert _env_bool('TEB_TEST', True) is True

    def test_env_bool_missing(self, monkeypatch):
        monkeypatch.delenv('TEB_MISSING', raising=False)
        assert _env_bool('TEB_MISSING', True) is True

    def test_env_bool_invalid(self, monkeypatch):
        monkeypatch.setenv('TEB_TEST', 'garbage')
        assert _env_bool('TEB_TEST', False) is False

    def test_env_int_valid(self, monkeypatch):
        monkeypatch.setenv('TEI_TEST', '42')
        assert _env_int('TEI_TEST', 0) == 42

    def test_env_int_empty(self, monkeypatch):
        monkeypatch.setenv('TEI_TEST', '')
        assert _env_int('TEI_TEST', 99) == 99

    def test_env_int_missing(self, monkeypatch):
        monkeypatch.delenv('TEI_MISSING', raising=False)
        assert _env_int('TEI_MISSING', 7) == 7

    def test_env_int_invalid(self, monkeypatch):
        monkeypatch.setenv('TEI_TEST', 'abc')
        assert _env_int('TEI_TEST', 10) == 10

    def test_env_int_negative(self, monkeypatch):
        monkeypatch.setenv('TEI_TEST', '-5')
        assert _env_int('TEI_TEST', 0) == -5

    def test_env_int_whitespace(self, monkeypatch):
        monkeypatch.setenv('TEI_TEST', '  100  ')
        assert _env_int('TEI_TEST', 0) == 100
