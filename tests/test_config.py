import os

from src.config import load_config, get_config_summary

_MINIMAL_TOML = """
[models]
pose_model = "models/yolo/yolo26m-pose.pt"
device = "cuda:0"

[kinect]
backend = "openni"

[env]
MY_CUSTOM_VAR = "hello"
ANOTHER_VAR = "42"
"""


def test_load_config_sets_env_vars(tmp_path, monkeypatch):
    cfg = tmp_path / "config.toml"
    cfg.write_text(_MINIMAL_TOML)

    for key in ("YOLO_POSE_MODEL", "YOLO_DEVICE", "KINECT_BACKEND", "MY_CUSTOM_VAR", "ANOTHER_VAR"):
        monkeypatch.delenv(key, raising=False)

    load_config(str(cfg))

    assert os.environ.get("YOLO_POSE_MODEL") == "models/yolo/yolo26m-pose.pt"
    assert os.environ.get("YOLO_DEVICE") == "cuda:0"
    assert os.environ.get("KINECT_BACKEND") == "openni"
    assert os.environ.get("MY_CUSTOM_VAR") == "hello"
    assert os.environ.get("ANOTHER_VAR") == "42"


def test_load_config_does_not_override_existing(monkeypatch, tmp_path):
    monkeypatch.setenv("YOLO_POSE_MODEL", "already-set")
    cfg = tmp_path / "config.toml"
    cfg.write_text(_MINIMAL_TOML)

    load_config(str(cfg))

    assert os.environ["YOLO_POSE_MODEL"] == "already-set"


def test_load_config_missing_file_is_noop(tmp_path):
    load_config(str(tmp_path / "nonexistent.toml"))


def test_load_config_invalid_toml_is_noop(tmp_path):
    cfg = tmp_path / "bad.toml"
    cfg.write_text("[[[invalid")
    load_config(str(cfg))


def test_load_config_empty_env_section_skips(monkeypatch, tmp_path):
    monkeypatch.delenv("YOLO_DEVICE", raising=False)
    cfg = tmp_path / "config.toml"
    cfg.write_text("[env]\n[models]\ndevice = \"cpu\"")

    load_config(str(cfg))

    assert os.environ.get("YOLO_DEVICE") == "cpu"


def test_get_config_summary_returns_values(tmp_path):
    cfg = tmp_path / "config.toml"
    cfg.write_text(_MINIMAL_TOML)

    result = get_config_summary(str(cfg))

    assert result["source"] == str(cfg)
    assert result["values"]["YOLO_POSE_MODEL"] == "models/yolo/yolo26m-pose.pt"
    assert result["values"]["MY_CUSTOM_VAR"] == "hello"


def test_get_config_summary_missing_file_returns_empty(tmp_path):
    result = get_config_summary(str(tmp_path / "no.toml"))
    assert result == {"source": None, "values": {}}
