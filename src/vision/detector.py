import json
import os
import threading
from pathlib import Path


def _env_float(name, default):
    raw = os.getenv(name, "")
    if raw is None:
        return float(default)
    raw = str(raw).strip()
    if raw == "":
        return float(default)
    try:
        return float(raw)
    except Exception:
        return float(default)


def _env_bool(name, default):
    raw = os.getenv(name, "")
    if raw is None:
        return bool(default)
    raw = str(raw).strip().lower()
    if raw == "":
        return bool(default)
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return bool(default)


def _env_int(name, default):
    raw = os.getenv(name, "")
    if raw is None:
        return int(default)
    raw = str(raw).strip()
    if raw == "":
        return int(default)
    try:
        return int(raw)
    except Exception:
        return int(default)


class PersonDetector:
    PERSON_CLASS_ID = 0
    YOLO_DETECT_INTERVAL = 0.18
    TRACKED_YOLO_DETECT_INTERVAL = _env_float("ATTENDANCE_TRACKED_DETECT_INTERVAL", 0.32)
    YOLO_IMAGE_SIZE = 640
    YOLO_CONFIDENCE = 0.22
    YOLO_WARMUP_CONFIDENCE = 0.30
    YOLO_WARMUP_MAX_DETECTIONS = 300
    MAX_INFERENCE_WIDTH = 1600
    TRACK_IOU_THRESHOLD = 0.08
    TRACK_CENTER_DISTANCE_RATIO = 0.58
    TRACK_MIN_OVERLAP_RATIO = 0.38
    TRACK_MAX_AREA_RATIO = 4.5
    MAX_DETECTIONS = 12
    MIN_PERSON_BOX_WIDTH = 24.0
    MIN_PERSON_BOX_HEIGHT = 32.0
    DETECTION_DUPLICATE_IOU_THRESHOLD = 0.64
    DETECTION_DUPLICATE_CENTER_RATIO = 0.22
    DETECTION_DUPLICATE_AREA_RATIO = 1.8
    DETECTION_DUPLICATE_MIN_OVERLAP_RATIO = 0.72
    POSE_KEYPOINT_MIN_CONFIDENCE = 0.18
    FACE_ANALYSIS_MAX_SIDE = 384
    FACE_REGION_TOP_RATIO = 0.02
    FACE_REGION_BOTTOM_RATIO = 0.64
    FACE_PERSON_FALLBACK_ENABLED = _env_bool("ATTENDANCE_FACE_PERSON_FALLBACK_ENABLED", True)
    FACE_PERSON_FALLBACK_INTERVAL = _env_float("ATTENDANCE_FACE_PERSON_FALLBACK_INTERVAL", 0.70)
    FACE_PERSON_FALLBACK_MIN_SCORE = _env_float("ATTENDANCE_FACE_PERSON_FALLBACK_MIN_SCORE", 0.50)
    FACE_PERSON_FALLBACK_MIN_SIZE = _env_float("ATTENDANCE_FACE_PERSON_FALLBACK_MIN_SIZE", 12.0)
    FACE_PERSON_FALLBACK_MAX_WIDTH = _env_int("ATTENDANCE_FACE_PERSON_FALLBACK_MAX_WIDTH", 960)
    FACE_PERSON_FALLBACK_SKIP_UNTIL_READY = _env_bool("ATTENDANCE_FACE_PERSON_FALLBACK_SKIP_UNTIL_READY", True)
    FACE_PERSON_FALLBACK_BOX_SCALE_X = _env_float("ATTENDANCE_FACE_PERSON_FALLBACK_BOX_SCALE_X", 3.0)
    FACE_PERSON_FALLBACK_BOX_TOP_SCALE = _env_float("ATTENDANCE_FACE_PERSON_FALLBACK_BOX_TOP_SCALE", 0.45)
    FACE_PERSON_FALLBACK_BOX_BOTTOM_SCALE = _env_float("ATTENDANCE_FACE_PERSON_FALLBACK_BOX_BOTTOM_SCALE", 2.35)
    DEPTH_SAMPLE_RADIUS = 7
    DEPTH_SMOOTHING_ALPHA = 0.38
    DEPTH_SMOOTHING_FAST_ALPHA = 0.64
    DEPTH_FAST_JUMP_CM = 45.0
    DEPTH_MIN_VALID_CM = 35.0
    DEPTH_MAX_VALID_CM = 450.0
    DEPTH_DISTANCE_SCALE = _env_float("KINECT_DEPTH_DISTANCE_SCALE", 1.0)
    DEPTH_DISTANCE_BIAS_CM = _env_float("KINECT_DEPTH_DISTANCE_BIAS_CM", 0.0)
    POSE_DEPTH_FUSION_ENABLED = _env_bool("KINECT_POSE_DEPTH_FUSION_ENABLED", True)
    POSE_DEPTH_FUSION_MIN_CONFIDENCE = _env_float("KINECT_POSE_DEPTH_FUSION_MIN_CONFIDENCE", 0.12)
    POSE_DEPTH_FUSION_OUTLIER_CM = _env_float("KINECT_POSE_DEPTH_FUSION_OUTLIER_CM", 72.0)
    POSE_DEPTH_FUSION_OUTLIER_CONF_MAX = _env_float("KINECT_POSE_DEPTH_FUSION_OUTLIER_CONF_MAX", 0.55)
    POSE_DEPTH_FUSION_BASE_ALPHA = _env_float("KINECT_POSE_DEPTH_FUSION_BASE_ALPHA", 0.62)
    POSE_DEPTH_FUSION_FAST_ALPHA = _env_float("KINECT_POSE_DEPTH_FUSION_FAST_ALPHA", 0.42)
    POSE_DEPTH_FUSION_OUTLIER_ALPHA = _env_float("KINECT_POSE_DEPTH_FUSION_OUTLIER_ALPHA", 0.24)
    POSE_DEPTH_FUSION_DEPTH_JUMP_CM = _env_float("KINECT_POSE_DEPTH_FUSION_DEPTH_JUMP_CM", 18.0)
    POSE_DEPTH_FUSION_DEPTH_JUMP_ALPHA = _env_float("KINECT_POSE_DEPTH_FUSION_DEPTH_JUMP_ALPHA", 0.35)
    POSE_DEPTH_FUSION_DISP_NORM_FAST = _env_float("KINECT_POSE_DEPTH_FUSION_DISP_NORM_FAST", 0.16)
    POSE_DEPTH_FUSION_TRACK_MAX_AGE_SECONDS = _env_float("KINECT_POSE_DEPTH_FUSION_TRACK_MAX_AGE_SECONDS", 1.8)
    POSE_DEPTH_FUSION_HOLD_SECONDS = _env_float("KINECT_POSE_DEPTH_FUSION_HOLD_SECONDS", 0.22)
    POSE_DEPTH_FUSION_HOLD_MIN_CONF = _env_float("KINECT_POSE_DEPTH_FUSION_HOLD_MIN_CONF", 0.18)
    POSE_DEPTH_FUSION_HOLD_DECAY = _env_float("KINECT_POSE_DEPTH_FUSION_HOLD_DECAY", 0.85)
    POSE_DEPTH_FUSION_HOLD_FLOOR = _env_float("KINECT_POSE_DEPTH_FUSION_HOLD_FLOOR", 0.10)
    POSE_DEPTH_FUSION_TRACK_MATCH_IOU = _env_float("KINECT_POSE_DEPTH_FUSION_TRACK_MATCH_IOU", 0.10)
    POSE_DEPTH_FUSION_TRACK_MATCH_CENTER_RATIO = _env_float("KINECT_POSE_DEPTH_FUSION_TRACK_MATCH_CENTER_RATIO", 0.55)
    KINECT_RAW_MIN = 300.0
    KINECT_RAW_MAX = 1080.0
    KINECT_RAW_COEFF_A = -0.0030711016
    KINECT_RAW_COEFF_B = 3.3309495161
    POSE_SKELETON_EDGES = (
        (5, 6),
        (5, 7),
        (7, 9),
        (6, 8),
        (8, 10),
        (5, 11),
        (6, 12),
        (11, 12),
        (11, 13),
        (13, 15),
        (12, 14),
        (14, 16),
        (0, 1),
        (0, 2),
        (1, 3),
        (2, 4),
    )
    MODEL_CANDIDATES = (
        ("yolo26x-pose", "models/yolo/yolo26x-pose.pt", True),
        ("yolo26s-pose", "models/yolo/yolo26s-pose.pt", True),
        ("yolo26n-pose", "models/yolo/yolo26n-pose.pt", True),
        ("yolo11n-pose", "models/yolo/yolo11n-pose.pt", True),
        ("yolov8n-pose", "models/yolo/yolov8n-pose.pt", True),
        ("yolo11n-pose", "yolo11n-pose.pt", False),
        ("yolov8n-pose", "yolov8n-pose.pt", False),
    )
    RUNTIME_TUNING_FIELDS = {
        "max_inference_width": int,
        "yolo_image_size": int,
        "yolo_detect_interval": float,
        "tracked_yolo_detect_interval": float,
        "yolo_confidence": float,
        "track_iou_threshold": float,
        "max_detections": int,
        "min_person_box_width": float,
        "min_person_box_height": float,
        "detection_duplicate_iou_threshold": float,
        "detection_duplicate_center_ratio": float,
        "detection_duplicate_area_ratio": float,
        "face_person_fallback_interval": float,
        "face_person_fallback_min_score": float,
        "face_person_fallback_min_size": float,
        "face_person_fallback_max_width": int,
        "face_person_fallback_box_scale_x": float,
        "face_person_fallback_box_top_scale": float,
        "face_person_fallback_box_bottom_scale": float,
    }

    def __init__(self, base_dir, face_db=None):
        self.base_dir = Path(base_dir)
        self.face_db = face_db
        self._runtime_tuning_file = self.base_dir / "data" / "runtime_tuning_profile.json"
        self._cv_modules = None
        self._yolo_model = None
        self._yolo_error = None
        self._yolo_device = self._resolve_yolo_device()
        self._model_lock = threading.Lock()
        self._last_pose_detections = []
        self._last_face_person_boxes = []
        self._last_face_person_fallback_at = 0.0
        self._last_person_detect_at = 0.0
        self._distance_smooth_cache = {}
        self._pose_fusion_tracks = {}
        self._pose_fusion_next_track_id = 1
        self._last_source_frame_seq = -1
        self._last_source_frame_timestamp = 0.0
        self._last_person_boxes = []
        self.apply_runtime_tuning_profile()

    def _get_cv_modules(self):
        if self._cv_modules is not None:
            return self._cv_modules

        import cv2  # pylint: disable=import-outside-toplevel
        import numpy as np  # pylint: disable=import-outside-toplevel

        self._cv_modules = (cv2, np)
        return self._cv_modules

    def _resolve_yolo_device(self):
        raw_device = str(os.getenv("YOLO_DEVICE", "auto")).strip()
        if raw_device and raw_device.lower() != "auto":
            return raw_device

        try:
            import torch  # pylint: disable=import-outside-toplevel

            if torch.cuda.is_available():
                return 0
        except Exception:
            pass
        return "cpu"

    def _yolo_device_label(self):
        if self._yolo_device == 0:
            return "cuda:0"
        return str(self._yolo_device)

    def _run_yolo_person_inference(self, frame, conf, max_det):
        model = self.get_yolo_model()
        with self._model_lock:
            return model(
                frame,
                verbose=False,
                classes=[self.PERSON_CLASS_ID],
                imgsz=self.YOLO_IMAGE_SIZE,
                conf=conf,
                max_det=max_det,
                device=self._yolo_device,
            )[0]

    def get_yolo_model(self):
        if self._yolo_model is not None:
            return self._yolo_model
        if self._yolo_error is not None:
            raise RuntimeError(self._yolo_error)

        with self._model_lock:
            if self._yolo_model is not None:
                return self._yolo_model
            if self._yolo_error is not None:
                raise RuntimeError(self._yolo_error)

            try:
                from ultralytics import YOLO  # pylint: disable=import-outside-toplevel

                selected_model_ref = None
                model_candidates = list(self.MODEL_CANDIDATES)
                model_override = str(os.getenv("YOLO_POSE_MODEL", "")).strip()
                if model_override:
                    override_path = Path(model_override)
                    if not override_path.is_absolute():
                        override_path = self.base_dir / override_path

                    if override_path.exists():
                        model_candidates.insert(0, (override_path.stem, str(override_path), True))
                    else:
                        override_name = Path(model_override).stem or model_override
                        model_candidates.insert(0, (override_name, model_override, False))

                for candidate_name, model_ref, is_local in model_candidates:
                    if is_local:
                        candidate_path = self.base_dir / model_ref
                        if Path(model_ref).is_absolute():
                            candidate_path = Path(model_ref)
                        if not candidate_path.exists():
                            continue
                        selected_model_ref = str(candidate_path)
                        break

                    selected_model_ref = str(model_ref)
                    break

                if selected_model_ref is None:
                    raise FileNotFoundError("No YOLO pose model was found.")

                self._yolo_model = YOLO(selected_model_ref)
            except Exception as exc:
                self._yolo_error = f"YOLO is not available: {exc}"
                raise RuntimeError(self._yolo_error) from exc
        return self._yolo_model

    def warm_models(self):
        try:
            _, np = self._get_cv_modules()
            dummy_frame = np.zeros((self.YOLO_IMAGE_SIZE, self.YOLO_IMAGE_SIZE, 3), dtype=np.uint8)
            self._run_yolo_person_inference(
                dummy_frame,
                conf=self.YOLO_WARMUP_CONFIDENCE,
                max_det=self.YOLO_WARMUP_MAX_DETECTIONS,
            )
        except Exception:
            return

    def apply_runtime_tuning_profile(self, profile_data=None):
        if profile_data is not None:
            params = profile_data.get("best_params") or profile_data.get("params") or profile_data
        else:
            if not self._runtime_tuning_file.exists():
                return
            try:
                with self._runtime_tuning_file.open("r", encoding="utf-8") as profile_file:
                    payload = json.load(profile_file)
            except Exception:
                return
            params = payload.get("best_params") or payload.get("params") or payload

        if not isinstance(params, dict):
            return

        field_to_attr = {
            "max_inference_width": "MAX_INFERENCE_WIDTH",
            "yolo_image_size": "YOLO_IMAGE_SIZE",
            "yolo_detect_interval": "YOLO_DETECT_INTERVAL",
            "tracked_yolo_detect_interval": "TRACKED_YOLO_DETECT_INTERVAL",
            "yolo_confidence": "YOLO_CONFIDENCE",
            "track_iou_threshold": "TRACK_IOU_THRESHOLD",
            "max_detections": "MAX_DETECTIONS",
            "min_person_box_width": "MIN_PERSON_BOX_WIDTH",
            "min_person_box_height": "MIN_PERSON_BOX_HEIGHT",
            "detection_duplicate_iou_threshold": "DETECTION_DUPLICATE_IOU_THRESHOLD",
            "detection_duplicate_center_ratio": "DETECTION_DUPLICATE_CENTER_RATIO",
            "detection_duplicate_area_ratio": "DETECTION_DUPLICATE_AREA_RATIO",
            "face_person_fallback_interval": "FACE_PERSON_FALLBACK_INTERVAL",
            "face_person_fallback_min_score": "FACE_PERSON_FALLBACK_MIN_SCORE",
            "face_person_fallback_min_size": "FACE_PERSON_FALLBACK_MIN_SIZE",
            "face_person_fallback_max_width": "FACE_PERSON_FALLBACK_MAX_WIDTH",
            "face_person_fallback_box_scale_x": "FACE_PERSON_FALLBACK_BOX_SCALE_X",
            "face_person_fallback_box_top_scale": "FACE_PERSON_FALLBACK_BOX_TOP_SCALE",
            "face_person_fallback_box_bottom_scale": "FACE_PERSON_FALLBACK_BOX_BOTTOM_SCALE",
        }

        for field_name, cast in self.RUNTIME_TUNING_FIELDS.items():
            attr_name = field_to_attr[field_name]
            raw_value = params.get(field_name)
            if raw_value is None:
                continue
            try:
                setattr(self, attr_name, cast(raw_value))
            except Exception:
                continue

    def _resize_for_inference(self, frame):
        cv2, _ = self._get_cv_modules()
        height, width = frame.shape[:2]
        if width <= self.MAX_INFERENCE_WIDTH:
            return frame, 1.0

        scale = self.MAX_INFERENCE_WIDTH / float(width)
        resized = cv2.resize(frame, (int(width * scale), int(height * scale)))
        return resized, scale

    def _bbox_iou(self, left_bbox, right_bbox):
        left = max(left_bbox[0], right_bbox[0])
        top = max(left_bbox[1], right_bbox[1])
        right = min(left_bbox[2], right_bbox[2])
        bottom = min(left_bbox[3], right_bbox[3])
        if right <= left or bottom <= top:
            return 0.0

        inter_area = (right - left) * (bottom - top)
        left_area = max(0.0, left_bbox[2] - left_bbox[0]) * max(0.0, left_bbox[3] - left_bbox[1])
        right_area = max(0.0, right_bbox[2] - right_bbox[0]) * max(0.0, right_bbox[3] - right_bbox[1])
        union_area = left_area + right_area - inter_area
        if union_area <= 0:
            return 0.0
        return inter_area / union_area

    def _bbox_intersection_over_min_area(self, left_bbox, right_bbox):
        left = max(float(left_bbox[0]), float(right_bbox[0]))
        top = max(float(left_bbox[1]), float(right_bbox[1]))
        right = min(float(left_bbox[2]), float(right_bbox[2]))
        bottom = min(float(left_bbox[3]), float(right_bbox[3]))
        if right <= left or bottom <= top:
            return 0.0

        inter_area = (right - left) * (bottom - top)
        left_area = max(0.0, float(left_bbox[2]) - float(left_bbox[0])) * max(
            0.0, float(left_bbox[3]) - float(left_bbox[1])
        )
        right_area = max(0.0, float(right_bbox[2]) - float(right_bbox[0])) * max(
            0.0, float(right_bbox[3]) - float(right_bbox[1])
        )
        min_area = min(left_area, right_area)
        if min_area <= 0.0:
            return 0.0
        return inter_area / min_area

    def _boxes_likely_same_person(
        self, left_bbox, right_bbox, iou_threshold, center_ratio, area_ratio_limit, overlap_ratio
    ):
        iou = self._bbox_iou(left_bbox, right_bbox)
        if iou >= float(iou_threshold):
            return True

        overlap = self._bbox_intersection_over_min_area(left_bbox, right_bbox)
        if overlap >= float(overlap_ratio):
            return True

        center_distance = self._bbox_center_distance(left_bbox, right_bbox)
        min_side = min(self._bbox_max_side(left_bbox), self._bbox_max_side(right_bbox))
        center_limit = max(12.0, min_side * float(center_ratio))
        area_left = max(1.0, self._current_bbox_area(left_bbox))
        area_right = max(1.0, self._current_bbox_area(right_bbox))
        area_ratio = max(area_left, area_right) / min(area_left, area_right)
        return center_distance <= center_limit and area_ratio <= float(area_ratio_limit)

    def _bbox_center(self, bbox):
        return (
            (float(bbox[0]) + float(bbox[2])) / 2.0,
            (float(bbox[1]) + float(bbox[3])) / 2.0,
        )

    def _bbox_torso_point(self, bbox):
        x1, y1, x2, y2 = [float(value) for value in bbox]
        return (
            (x1 + x2) / 2.0,
            y1 + ((y2 - y1) * 0.42),
        )

    def _bbox_center_distance(self, left_bbox, right_bbox):
        left_center = self._bbox_center(left_bbox)
        right_center = self._bbox_center(right_bbox)
        delta_x = left_center[0] - right_center[0]
        delta_y = left_center[1] - right_center[1]
        return (delta_x * delta_x + delta_y * delta_y) ** 0.5

    def _bbox_max_side(self, bbox):
        return max(
            max(0.0, float(bbox[2]) - float(bbox[0])),
            max(0.0, float(bbox[3]) - float(bbox[1])),
        )

    def _current_bbox_area(self, bbox):
        return max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])

    def _detection_candidates_from_result(self, result, factor):
        candidates = []
        keypoints_xy = None
        keypoints_conf = None
        if getattr(result, "keypoints", None) is not None:
            keypoints_xy = getattr(result.keypoints, "xy", None)
            keypoints_conf = getattr(result.keypoints, "conf", None)

        for index, box in enumerate(result.boxes):
            xyxy = [float(value) * factor for value in box.xyxy[0].tolist()]
            confidence = float(box.conf[0].item()) if box.conf is not None and len(box.conf) > 0 else 0.0
            width = max(0.0, xyxy[2] - xyxy[0])
            height = max(0.0, xyxy[3] - xyxy[1])
            if width < self.MIN_PERSON_BOX_WIDTH or height < self.MIN_PERSON_BOX_HEIGHT:
                continue

            pose_points = []
            pose_confidence = []
            if keypoints_xy is not None and len(keypoints_xy) > index:
                try:
                    raw_points = keypoints_xy[index].tolist()
                    for point in raw_points:
                        pose_points.append([float(point[0]) * factor, float(point[1]) * factor])
                except Exception:
                    pose_points = []

            if keypoints_conf is not None and len(keypoints_conf) > index:
                try:
                    pose_confidence = [float(value) for value in keypoints_conf[index].tolist()]
                except Exception:
                    pose_confidence = []

            candidates.append(
                {
                    "bbox": xyxy,
                    "confidence": confidence,
                    "keypoints": pose_points,
                    "keypoint_conf": pose_confidence,
                }
            )
        return candidates

    def _person_bbox_from_face_bbox(self, face_bbox, frame_shape):
        height, width = frame_shape[:2]
        x1, y1, x2, y2 = [float(value) for value in face_bbox]
        face_w = max(1.0, x2 - x1)
        face_h = max(1.0, y2 - y1)
        center_x = (x1 + x2) * 0.5

        box_half_w = max(self.MIN_PERSON_BOX_WIDTH * 0.5, face_w * self.FACE_PERSON_FALLBACK_BOX_SCALE_X * 0.5)
        box_top = y1 - (face_h * self.FACE_PERSON_FALLBACK_BOX_TOP_SCALE)
        box_bottom = y2 + (face_h * self.FACE_PERSON_FALLBACK_BOX_BOTTOM_SCALE)

        bbox = [
            max(0.0, center_x - box_half_w),
            max(0.0, box_top),
            min(float(width), center_x + box_half_w),
            min(float(height), box_bottom),
        ]
        if bbox[2] - bbox[0] < self.MIN_PERSON_BOX_WIDTH or bbox[3] - bbox[1] < self.MIN_PERSON_BOX_HEIGHT:
            return None
        return bbox

    def _face_person_fallback_candidates(self, frame, now, existing_candidates):
        if not self.FACE_PERSON_FALLBACK_ENABLED:
            return []

        if self.FACE_PERSON_FALLBACK_SKIP_UNTIL_READY:
            is_ready = getattr(self.face_db, "is_analysis_ready", lambda: True)
            if not is_ready():
                return []

        interval = max(0.0, float(self.FACE_PERSON_FALLBACK_INTERVAL))
        if self._last_face_person_boxes and now - self._last_face_person_fallback_at < interval:
            return [
                {
                    "bbox": list(bbox),
                    "confidence": max(0.0, float(self.FACE_PERSON_FALLBACK_MIN_SCORE)),
                    "keypoints": [],
                    "keypoint_conf": [],
                    "source": "face_fallback",
                }
                for bbox in self._last_face_person_boxes
            ]

        self._last_face_person_fallback_at = now
        self._last_face_person_boxes = []

        try:
            cv2, _ = self._get_cv_modules()
            analyze_frame = frame
            analysis_scale = 1.0
            max_width = max(0, int(self.FACE_PERSON_FALLBACK_MAX_WIDTH))
            if max_width and frame.shape[1] > max_width:
                analysis_scale = max_width / float(frame.shape[1])
                resized_height = max(1, int(round(frame.shape[0] * analysis_scale)))
                analyze_frame = cv2.resize(frame, (max_width, resized_height), interpolation=cv2.INTER_AREA)

            analysis = self.face_db.analyze_faces(analyze_frame)
        except Exception:
            return []
        if analysis.get("status") != "ok":
            return []

        scale_back = (1.0 / analysis_scale) if analysis_scale > 0 else 1.0
        existing_boxes = [item["bbox"] for item in existing_candidates]
        candidates = []
        for face in analysis.get("faces") or []:
            face_bbox = face.get("bbox") or []
            if len(face_bbox) != 4:
                continue
            if scale_back != 1.0:
                face_bbox = [float(value) * scale_back for value in face_bbox]
            det_score = float(face.get("det_score", 0.0))
            if det_score < float(self.FACE_PERSON_FALLBACK_MIN_SCORE):
                continue

            face_w = max(0.0, float(face_bbox[2]) - float(face_bbox[0]))
            face_h = max(0.0, float(face_bbox[3]) - float(face_bbox[1]))
            if min(face_w, face_h) < float(self.FACE_PERSON_FALLBACK_MIN_SIZE):
                continue

            face_center = self._bbox_center(face_bbox)
            face_inside_existing = False
            for bbox in existing_boxes:
                if float(bbox[0]) <= face_center[0] <= float(bbox[2]) and float(bbox[1]) <= face_center[1] <= float(
                    bbox[3]
                ):
                    face_inside_existing = True
                    break
            if face_inside_existing:
                continue

            person_bbox = self._person_bbox_from_face_bbox(face_bbox, frame.shape)
            if person_bbox is None:
                continue

            existing_boxes.append(person_bbox)
            self._last_face_person_boxes.append(list(person_bbox))
            candidates.append(
                {
                    "bbox": person_bbox,
                    "confidence": det_score,
                    "keypoints": [],
                    "keypoint_conf": [],
                    "source": "face_fallback",
                }
            )

        return candidates

    def _coerce_pose_arrays(self, detection, min_length=17):
        keypoints = detection.get("keypoints") or []
        keypoint_conf = detection.get("keypoint_conf") or []
        target_length = max(min_length, len(keypoints), len(keypoint_conf))
        normalized_points = []
        normalized_conf = []

        for index in range(target_length):
            point = keypoints[index] if index < len(keypoints) else None
            conf = keypoint_conf[index] if index < len(keypoint_conf) else 0.0

            if point is None or len(point) < 2:
                normalized_points.append([0.0, 0.0])
            else:
                try:
                    normalized_points.append([float(point[0]), float(point[1])])
                except Exception:
                    normalized_points.append([0.0, 0.0])

            try:
                normalized_conf.append(float(conf))
            except Exception:
                normalized_conf.append(0.0)

        return normalized_points, normalized_conf

    def _pose_depth_profile(self, keypoints, keypoint_conf, depth_frame, source_mode):
        if depth_frame is None:
            return {}

        profile = {}
        for index, point in enumerate(keypoints):
            confidence = keypoint_conf[index] if index < len(keypoint_conf) else 0.0
            if float(confidence) < self.POSE_DEPTH_FUSION_MIN_CONFIDENCE:
                continue
            if point is None or len(point) < 2:
                continue
            depth_value = self._depth_patch_distance_cm(
                depth_frame,
                point,
                source_mode=source_mode,
            )
            if depth_value is not None:
                profile[index] = float(depth_value)
        return profile

    def _pose_torso_depth_cm(self, profile):
        candidates = []
        for index in (0, 5, 6, 11, 12):
            depth_value = profile.get(index)
            if depth_value is not None:
                candidates.append(float(depth_value))

        if not candidates:
            return None
        candidates.sort()
        return float(candidates[len(candidates) // 2])

    def _match_pose_fusion_tracks(self, detections, now):
        if not self._pose_fusion_tracks or not detections:
            return {}

        candidates = []
        for detection_index, detection in enumerate(detections):
            detection_bbox = detection.get("bbox")
            if detection_bbox is None:
                continue
            detection_side = max(1.0, self._bbox_max_side(detection_bbox))

            for track_id, state in self._pose_fusion_tracks.items():
                age = float(now) - float(state.get("updated_at", 0.0))
                if age > self.POSE_DEPTH_FUSION_TRACK_MAX_AGE_SECONDS:
                    continue

                track_bbox = state.get("bbox")
                if track_bbox is None:
                    continue

                overlap = self._bbox_iou(detection_bbox, track_bbox)
                center_distance = self._bbox_center_distance(detection_bbox, track_bbox)
                normalized_distance = center_distance / detection_side
                if (
                    overlap < self.POSE_DEPTH_FUSION_TRACK_MATCH_IOU
                    and normalized_distance > self.POSE_DEPTH_FUSION_TRACK_MATCH_CENTER_RATIO
                ):
                    continue

                score = (overlap * 3.0) + (1.0 - min(1.0, normalized_distance))
                score += max(0.0, 0.2 - min(0.2, age * 0.15))
                candidates.append((score, detection_index, track_id))

        matches = {}
        used_detection_indexes = set()
        used_track_ids = set()

        for _, detection_index, track_id in sorted(candidates, key=lambda item: item[0], reverse=True):
            if detection_index in used_detection_indexes or track_id in used_track_ids:
                continue
            used_detection_indexes.add(detection_index)
            used_track_ids.add(track_id)
            matches[detection_index] = track_id

        return matches

    def _fuse_pose_detection(self, detection, track_state, now, depth_frame, source_mode):
        keypoints, keypoint_conf = self._coerce_pose_arrays(detection)
        depth_profile = self._pose_depth_profile(keypoints, keypoint_conf, depth_frame, source_mode)
        torso_depth = self._pose_torso_depth_cm(depth_profile)

        previous_points = track_state.get("keypoints") or []
        previous_conf = track_state.get("keypoint_conf") or []
        previous_depth = track_state.get("depth_by_index") or {}
        previous_updated_at = float(track_state.get("updated_at", 0.0))
        time_delta = max(0.0, float(now) - previous_updated_at)
        bbox = detection.get("bbox") or [0.0, 0.0, 1.0, 1.0]
        bbox_side = max(1.0, self._bbox_max_side(bbox))

        fused_points = []
        fused_conf = []
        fused_depth = {}

        for index, point in enumerate(keypoints):
            confidence = keypoint_conf[index] if index < len(keypoint_conf) else 0.0
            valid_point = point is not None and len(point) >= 2
            is_valid = bool(valid_point and float(confidence) >= self.POSE_DEPTH_FUSION_MIN_CONFIDENCE)
            current_depth = depth_profile.get(index)
            depth_outlier = bool(
                is_valid
                and current_depth is not None
                and torso_depth is not None
                and abs(float(current_depth) - float(torso_depth)) > self.POSE_DEPTH_FUSION_OUTLIER_CM
                and float(confidence) <= self.POSE_DEPTH_FUSION_OUTLIER_CONF_MAX
            )

            previous_point = previous_points[index] if index < len(previous_points) else None
            previous_point_valid = previous_point is not None and len(previous_point) >= 2
            previous_confidence = float(previous_conf[index]) if index < len(previous_conf) else 0.0
            previous_depth_value = previous_depth.get(index)

            if not is_valid:
                if (
                    previous_point_valid
                    and time_delta <= self.POSE_DEPTH_FUSION_HOLD_SECONDS
                    and previous_confidence >= self.POSE_DEPTH_FUSION_HOLD_MIN_CONF
                ):
                    hold_confidence = max(
                        self.POSE_DEPTH_FUSION_HOLD_FLOOR,
                        previous_confidence * self.POSE_DEPTH_FUSION_HOLD_DECAY,
                    )
                    fused_points.append([float(previous_point[0]), float(previous_point[1])])
                    fused_conf.append(float(hold_confidence))
                    if previous_depth_value is not None:
                        fused_depth[index] = float(previous_depth_value)
                else:
                    fused_points.append([0.0, 0.0])
                    fused_conf.append(0.0)
                continue

            fused_x = float(point[0])
            fused_y = float(point[1])
            fused_confidence = float(confidence)
            if previous_point_valid and time_delta <= self.POSE_DEPTH_FUSION_TRACK_MAX_AGE_SECONDS:
                displacement = (
                    ((fused_x - float(previous_point[0])) ** 2) + ((fused_y - float(previous_point[1])) ** 2)
                ) ** 0.5
                displacement_norm = displacement / bbox_side

                alpha = float(self.POSE_DEPTH_FUSION_BASE_ALPHA)
                if displacement_norm > self.POSE_DEPTH_FUSION_DISP_NORM_FAST:
                    alpha = min(alpha, float(self.POSE_DEPTH_FUSION_FAST_ALPHA))

                if (
                    current_depth is not None
                    and previous_depth_value is not None
                    and abs(float(current_depth) - float(previous_depth_value)) > self.POSE_DEPTH_FUSION_DEPTH_JUMP_CM
                ):
                    alpha = min(alpha, float(self.POSE_DEPTH_FUSION_DEPTH_JUMP_ALPHA))

                if depth_outlier:
                    alpha = min(alpha, float(self.POSE_DEPTH_FUSION_OUTLIER_ALPHA))
                    fused_confidence = max(fused_confidence, previous_confidence * 0.75)

                fused_x = (float(previous_point[0]) * (1.0 - alpha)) + (fused_x * alpha)
                fused_y = (float(previous_point[1]) * (1.0 - alpha)) + (fused_y * alpha)

            fused_points.append([float(fused_x), float(fused_y)])
            fused_conf.append(float(fused_confidence))
            if current_depth is not None:
                fused_depth[index] = float(current_depth)
            elif previous_depth_value is not None:
                fused_depth[index] = float(previous_depth_value)

        detection["keypoints"] = fused_points
        detection["keypoint_conf"] = fused_conf
        return fused_points, fused_conf, fused_depth

    def _cleanup_pose_fusion_tracks(self, now, active_track_ids=None, reset=False):
        if reset:
            self._pose_fusion_tracks = {}
            self._pose_fusion_next_track_id = 1
            return

        active = set(active_track_ids or [])
        max_age = float(self.POSE_DEPTH_FUSION_TRACK_MAX_AGE_SECONDS)
        self._pose_fusion_tracks = {
            track_id: state
            for track_id, state in self._pose_fusion_tracks.items()
            if (track_id in active or (float(now) - float(state.get("updated_at", 0.0))) <= max_age)
        }

    def _apply_depth_pose_fusion(self, detections, depth_frame, now, source_mode):
        if not detections:
            self._cleanup_pose_fusion_tracks(now, active_track_ids=[], reset=False)
            return detections

        if (not self.POSE_DEPTH_FUSION_ENABLED) or depth_frame is None:
            self._cleanup_pose_fusion_tracks(now, active_track_ids=[], reset=True)
            return detections

        matches = self._match_pose_fusion_tracks(detections, now)
        active_track_ids = []
        for detection_index, detection in enumerate(detections):
            track_id = matches.get(detection_index)
            if track_id is None:
                track_id = int(self._pose_fusion_next_track_id)
                self._pose_fusion_next_track_id += 1

            track_state = self._pose_fusion_tracks.get(track_id, {})
            fused_points, fused_conf, fused_depth = self._fuse_pose_detection(
                detection,
                track_state,
                now=now,
                depth_frame=depth_frame,
                source_mode=source_mode,
            )
            self._pose_fusion_tracks[track_id] = {
                "bbox": list(detection.get("bbox") or [0.0, 0.0, 1.0, 1.0]),
                "keypoints": fused_points,
                "keypoint_conf": fused_conf,
                "depth_by_index": fused_depth,
                "updated_at": float(now),
            }
            active_track_ids.append(track_id)

        self._cleanup_pose_fusion_tracks(now, active_track_ids=active_track_ids, reset=False)
        return detections

    def _deduplicate_detection_boxes(self, candidates):
        if not candidates:
            return []

        prioritized = sorted(
            candidates,
            key=lambda item: (item["confidence"], self._current_bbox_area(item["bbox"])),
            reverse=True,
        )
        kept = []

        for candidate in prioritized:
            bbox = candidate["bbox"]
            duplicate_found = False
            for kept_item in kept:
                if self._boxes_likely_same_person(
                    bbox,
                    kept_item["bbox"],
                    iou_threshold=self.DETECTION_DUPLICATE_IOU_THRESHOLD,
                    center_ratio=self.DETECTION_DUPLICATE_CENTER_RATIO,
                    area_ratio_limit=self.DETECTION_DUPLICATE_AREA_RATIO,
                    overlap_ratio=self.DETECTION_DUPLICATE_MIN_OVERLAP_RATIO,
                ):
                    duplicate_found = True
                    break

            if not duplicate_found:
                kept.append(candidate)

        kept.sort(key=lambda item: (item["bbox"][0], item["bbox"][1]))
        return kept

    def _tracking_match_score(self, detection_bbox, entity_bbox):
        iou = self._bbox_iou(detection_bbox, entity_bbox)
        if iou >= self.TRACK_IOU_THRESHOLD:
            return 2.0 + iou

        overlap = self._bbox_intersection_over_min_area(detection_bbox, entity_bbox)
        if overlap >= self.TRACK_MIN_OVERLAP_RATIO:
            return 1.6 + (overlap * 0.6)

        area_left = max(1.0, self._current_bbox_area(detection_bbox))
        area_right = max(1.0, self._current_bbox_area(entity_bbox))
        area_ratio = max(area_left, area_right) / min(area_left, area_right)
        if area_ratio > self.TRACK_MAX_AREA_RATIO:
            return None

        distance = self._bbox_center_distance(detection_bbox, entity_bbox)
        min_side = min(self._bbox_max_side(detection_bbox), self._bbox_max_side(entity_bbox))
        distance_limit = max(18.0, min_side * self.TRACK_CENTER_DISTANCE_RATIO)
        if overlap > 0.0:
            distance_limit *= 1.0 + min(0.42, overlap * 0.45)
        if distance > distance_limit:
            return None

        size_penalty = min(0.35, max(0.0, area_ratio - 1.0) * 0.09)
        return 1.0 - (distance / distance_limit) - size_penalty

    def _user_id_for_match(self, match):
        return match.get("student_id") or match["label"]

    def depth_source_mode(self):
        return "kinect"

    def _depth_raw_value_to_cm(self, raw_value, source_mode):
        try:
            value = float(raw_value)
        except Exception:
            return None
        if value <= 0:
            return None

        if source_mode == "kinect":
            if value < self.KINECT_RAW_MIN or value > self.KINECT_RAW_MAX:
                return None
            denominator = (self.KINECT_RAW_COEFF_A * value) + self.KINECT_RAW_COEFF_B
            if denominator <= 0:
                return None
            distance_cm = 100.0 / denominator
        elif source_mode in {"kinect_v1_registered", "kinect_v2"}:
            distance_cm = value / 10.0
        else:
            distance_cm = value / 10.0

        distance_cm = (distance_cm * self.DEPTH_DISTANCE_SCALE) + self.DEPTH_DISTANCE_BIAS_CM
        if distance_cm < self.DEPTH_MIN_VALID_CM or distance_cm > self.DEPTH_MAX_VALID_CM:
            return None
        return float(distance_cm)

    def _depth_patch_distance_cm(self, depth_frame, point, source_mode):
        if depth_frame is None or point is None:
            return None

        height = int(getattr(depth_frame, "shape", [0, 0])[0] or 0)
        width = int(getattr(depth_frame, "shape", [0, 0])[1] or 0)
        if width <= 0 or height <= 0:
            return None

        center_x = int(round(point[0]))
        center_y = int(round(point[1]))
        radius = int(self.DEPTH_SAMPLE_RADIUS)
        x1 = max(0, center_x - radius)
        y1 = max(0, center_y - radius)
        x2 = min(width, center_x + radius + 1)
        y2 = min(height, center_y + radius + 1)
        if x2 <= x1 or y2 <= y1:
            return None

        patch = depth_frame[y1:y2, x1:x2]
        if patch is None or getattr(patch, "size", 0) == 0:
            return None

        values_cm = []
        if len(patch.shape) == 3 and patch.shape[2] >= 3:
            gray_values = (patch[..., 0] * 0.114) + (patch[..., 1] * 0.587) + (patch[..., 2] * 0.299)
            for item in gray_values.reshape(-1):
                value = float(item)
                if value <= 0:
                    continue
                approx_cm = 30.0 + (value / 255.0) * 160.0
                if self.DEPTH_MIN_VALID_CM <= approx_cm <= self.DEPTH_MAX_VALID_CM:
                    values_cm.append(approx_cm)
        else:
            for item in patch.reshape(-1):
                converted = self._depth_raw_value_to_cm(item, source_mode)
                if converted is not None:
                    values_cm.append(converted)

        if not values_cm:
            return None

        values_cm.sort()
        trim_count = int(len(values_cm) * 0.18)
        if (trim_count * 2) >= len(values_cm):
            trimmed = values_cm
        else:
            trimmed = values_cm[trim_count : len(values_cm) - trim_count]

        if not trimmed:
            return None
        return float(trimmed[len(trimmed) // 2])

    def _estimate_distance_cm(self, depth_frame, bbox, pose_detection=None, smoothing_key=None, source_mode=None):
        if depth_frame is None or bbox is None:
            return None

        if source_mode is None:
            source_mode = self.depth_source_mode()
        sample_points = []

        nose_point = self._pose_point(pose_detection, 0)
        if nose_point is not None:
            sample_points.append((nose_point, 0.45))

        left_shoulder = self._pose_point(pose_detection, 5)
        right_shoulder = self._pose_point(pose_detection, 6)
        if left_shoulder is not None and right_shoulder is not None:
            shoulder_center = (
                (left_shoulder[0] + right_shoulder[0]) * 0.5,
                (left_shoulder[1] + right_shoulder[1]) * 0.5,
            )
            sample_points.append((shoulder_center, 0.35))

        sample_points.append((self._bbox_torso_point(bbox), 0.20))

        weighted_sum = 0.0
        weight_total = 0.0
        for point, weight in sample_points:
            point_distance = self._depth_patch_distance_cm(depth_frame, point, source_mode)
            if point_distance is None:
                continue
            weighted_sum += point_distance * float(weight)
            weight_total += float(weight)

        if weight_total <= 0.0:
            return None

        raw_distance = weighted_sum / weight_total
        if smoothing_key is None:
            return raw_distance

        previous_distance = self._distance_smooth_cache.get(smoothing_key)
        if previous_distance is None:
            smoothed = raw_distance
        else:
            alpha = self.DEPTH_SMOOTHING_ALPHA
            if abs(raw_distance - previous_distance) >= self.DEPTH_FAST_JUMP_CM:
                alpha = self.DEPTH_SMOOTHING_FAST_ALPHA
            smoothed = (previous_distance * (1.0 - alpha)) + (raw_distance * alpha)
        self._distance_smooth_cache[smoothing_key] = smoothed
        return smoothed

    def _cleanup_distance_smoothing_locked(self, active_keys):
        active = {str(item) for item in (active_keys or []) if str(item).strip()}
        self._distance_smooth_cache = {
            key: value for key, value in self._distance_smooth_cache.items() if key in active
        }

    def _valid_point(self, keypoints, keypoint_conf, index):
        if index >= len(keypoints):
            return None
        if keypoint_conf and index < len(keypoint_conf):
            if float(keypoint_conf[index]) < self.POSE_KEYPOINT_MIN_CONFIDENCE:
                return None
        point = keypoints[index]
        if point is None or len(point) < 2:
            return None
        return int(point[0]), int(point[1])

    def _pose_point(self, pose_detection, keypoint_index):
        if not pose_detection:
            return None

        keypoints = pose_detection.get("keypoints") or []
        keypoint_conf = pose_detection.get("keypoint_conf") or []
        if keypoint_index >= len(keypoints):
            return None
        if keypoint_conf and keypoint_index < len(keypoint_conf):
            if float(keypoint_conf[keypoint_index]) < self.POSE_KEYPOINT_MIN_CONFIDENCE:
                return None

        point = keypoints[keypoint_index]
        if point is None or len(point) < 2:
            return None
        return float(point[0]), float(point[1])

    def detect_people(self, frame, now, depth_frame=None, depth_source_mode=None):
        detect_interval = self.TRACKED_YOLO_DETECT_INTERVAL if self._last_person_boxes else self.YOLO_DETECT_INTERVAL
        if now - self._last_person_detect_at < detect_interval:
            return list(self._last_person_boxes)

        resized, scale = self._resize_for_inference(frame)
        result = self._run_yolo_person_inference(
            resized,
            conf=self.YOLO_CONFIDENCE,
            max_det=self.MAX_DETECTIONS,
        )

        factor = 1.0 / scale
        candidates = self._detection_candidates_from_result(result, factor)
        candidates.extend(self._face_person_fallback_candidates(frame, now, candidates))
        detections = self._deduplicate_detection_boxes(candidates)
        if depth_source_mode is None:
            depth_source_mode = self.depth_source_mode()
        detections = self._apply_depth_pose_fusion(
            detections,
            depth_frame=depth_frame,
            now=now,
            source_mode=depth_source_mode,
        )
        boxes = [item["bbox"] for item in detections]

        self._last_person_boxes = boxes
        self._last_pose_detections = detections
        self._last_person_detect_at = now
        return boxes

    def match_pose_detection_to_bbox(self, bbox, detections, used_indexes=None):
        if not detections:
            return None, None

        best_index = None
        best_detection = None
        best_score = None

        for index, detection in enumerate(detections):
            if used_indexes is not None and index in used_indexes:
                continue

            detection_bbox = detection.get("bbox")
            if detection_bbox is None:
                continue

            iou = self._bbox_iou(bbox, detection_bbox)
            if iou > 0:
                score = 2.0 + iou
            else:
                distance = self._bbox_center_distance(bbox, detection_bbox)
                min_side = min(self._bbox_max_side(bbox), self._bbox_max_side(detection_bbox))
                distance_limit = max(18.0, min_side * self.TRACK_CENTER_DISTANCE_RATIO)
                if distance > distance_limit:
                    continue
                score = 1.0 - (distance / distance_limit)

            if best_score is None or score > best_score:
                best_score = score
                best_index = index
                best_detection = detection

        return best_index, best_detection

    def _crop_frame_for_training(self, frame, bbox):
        height, width = frame.shape[:2]
        x1, y1, x2, y2 = [int(value) for value in bbox]
        pad_x = max(16, int((x2 - x1) * 0.12))
        pad_y = max(16, int((y2 - y1) * 0.12))
        x1 = max(0, x1 - pad_x)
        y1 = max(0, y1 - pad_y)
        x2 = min(width, x2 + pad_x)
        y2 = min(height, y2 + pad_y)
        cropped = frame[y1:y2, x1:x2]
        if cropped.size == 0:
            return frame.copy()
        return cropped.copy()

    def _analyze_face_inside_bbox_fast(self, frame, bbox):
        cv2, _ = self._get_cv_modules()
        height, width = frame.shape[:2]

        box_w = max(1.0, float(bbox[2]) - float(bbox[0]))
        box_h = max(1.0, float(bbox[3]) - float(bbox[1]))
        pad_x = int(box_w * 0.08)
        pad_y = int(box_h * 0.08)

        base_x1 = max(0, int(bbox[0] - pad_x))
        base_y1 = max(0, int(bbox[1] - pad_y))
        base_x2 = min(width, int(bbox[2] + pad_x))
        base_y2 = min(height, int(bbox[3] + pad_y))
        if base_x2 <= base_x1 or base_y2 <= base_y1:
            return {"status": "no_face", "message": "Invalid person region for face analysis."}

        upper_y1 = max(
            base_y1,
            int(float(bbox[1]) + (box_h * self.FACE_REGION_TOP_RATIO)),
        )
        upper_y2 = min(
            base_y2,
            int(float(bbox[1]) + (box_h * self.FACE_REGION_BOTTOM_RATIO)),
        )

        regions = []
        if upper_y2 > upper_y1:
            regions.append((base_x1, upper_y1, base_x2, upper_y2))
        regions.append((base_x1, base_y1, base_x2, base_y2))

        last_failure = {"status": "no_face", "message": "No face detected in selected person box."}
        for x1, y1, x2, y2 in regions:
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            analysis_scale = 1.0
            analyze_frame = crop
            max_side = max(crop.shape[0], crop.shape[1])
            if max_side > self.FACE_ANALYSIS_MAX_SIDE:
                analysis_scale = self.FACE_ANALYSIS_MAX_SIDE / float(max_side)
                resized_w = max(1, int(round(crop.shape[1] * analysis_scale)))
                resized_h = max(1, int(round(crop.shape[0] * analysis_scale)))
                analyze_frame = cv2.resize(crop, (resized_w, resized_h), interpolation=cv2.INTER_AREA)

            analysis = self.face_db.analyze_faces(analyze_frame)
            if analysis["status"] != "ok" or not analysis["faces"]:
                last_failure = {"status": analysis["status"], "message": analysis["message"]}
                continue

            best_face = max(analysis["faces"], key=lambda item: self._current_bbox_area(item["bbox"]))
            scale_back = (1.0 / analysis_scale) if analysis_scale > 0 else 1.0
            face_bbox = [
                (best_face["bbox"][0] * scale_back) + x1,
                (best_face["bbox"][1] * scale_back) + y1,
                (best_face["bbox"][2] * scale_back) + x1,
                (best_face["bbox"][3] * scale_back) + y1,
            ]
            return {
                "status": "ok",
                "message": "Face detected inside the selected person box.",
                "bbox": face_bbox,
                "embedding": best_face["embedding"],
                "det_score": float(best_face.get("det_score", 0.0)),
            }

        return last_failure

    def crop_face_for_training(self, frame, person_bbox):
        analysis = self._analyze_face_inside_bbox_fast(frame, person_bbox)
        if analysis.get("status") != "ok" or not analysis.get("bbox"):
            message = str(analysis.get("message") or "").strip() or "No face detected in current frame."
            raise RuntimeError(message)

        face_bbox = [float(value) for value in analysis.get("bbox", [])]
        if len(face_bbox) != 4:
            raise RuntimeError("Invalid face region in current frame.")

        height, width = frame.shape[:2]
        x1, y1, x2, y2 = face_bbox
        face_w = max(1.0, x2 - x1)
        face_h = max(1.0, y2 - y1)
        pad_x = max(12, int(round(face_w * 0.35)))
        pad_y_top = max(14, int(round(face_h * 0.45)))
        pad_y_bottom = max(10, int(round(face_h * 0.22)))

        crop_x1 = max(0, int(round(x1 - pad_x)))
        crop_y1 = max(0, int(round(y1 - pad_y_top)))
        crop_x2 = min(width, int(round(x2 + pad_x)))
        crop_y2 = min(height, int(round(y2 + pad_y_bottom)))
        if crop_x2 <= crop_x1 or crop_y2 <= crop_y1:
            raise RuntimeError("Unable to crop face in current frame.")

        cropped = frame[crop_y1:crop_y2, crop_x1:crop_x2]
        if cropped is None or cropped.size == 0:
            raise RuntimeError("Unable to crop face in current frame.")
        return cropped.copy()
