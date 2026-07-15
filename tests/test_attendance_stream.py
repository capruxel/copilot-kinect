from types import SimpleNamespace

from src.vision.attendance_pipeline import RecognitionPipeline


def test_stream_uses_latest_kinect_frame():
    pipeline = RecognitionPipeline.__new__(RecognitionPipeline)
    pipeline.kinect_service = SimpleNamespace(
        get_latest_jpeg=lambda kind: f"raw-{kind}".encode(),
        get_latest_frame_marker=lambda: {"frame_seq": 42},
    )

    assert pipeline._get_stream_payload_and_token("color") == (b"raw-color", ("raw", 42))
    assert pipeline._get_stream_payload_and_token("depth") == (b"raw-depth", ("raw", 42))


def test_stream_bbox_is_normalized_and_clamped():
    pipeline = RecognitionPipeline.__new__(RecognitionPipeline)
    pipeline._stream_frame_size = (1280, 720)

    assert pipeline._normalize_stream_bbox([-10, 72, 640, 800]) == [0.0, 0.1, 0.5, 1.0]
