import os
import tomllib
from pathlib import Path

SECTION_KEY_MAP = {
    ("models", "pose_model"): "YOLO_POSE_MODEL",
    ("models", "device"): "YOLO_DEVICE",
    ("insightface", "providers"): "INSIGHTFACE_PROVIDERS",
    ("kinect", "backend"): "KINECT_BACKEND",
    ("kinect", "test_video"): "KINECT_TEST_VIDEO",
    ("kinect", "video_source"): "KINECT_VIDEO_SOURCE",
    ("kinect", "video_loop"): "KINECT_VIDEO_LOOP",
    ("webhook", "power_automate_url"): "POWER_AUTOMATE_UPLOAD_URL",
    ("led_strip", "driver"): "LED_STRIP_DRIVER",
    ("led_strip", "host_port"): "LED_STRIP_HOST_PORT",
    ("led_strip", "num_regions"): "LED_STRIP_NUM_REGIONS",
    ("led_strip", "red_threshold"): "LED_STRIP_RED_THRESHOLD",
    ("led_strip", "green_threshold"): "LED_STRIP_GREEN_THRESHOLD",
    ("led_strip", "window_seconds"): "LED_STRIP_WINDOW_SECONDS",
    ("led_strip", "update_interval"): "LED_STRIP_UPDATE_INTERVAL",
    ("led_strip", "esp32_host"): "LED_STRIP_ESP32_HOST",
    ("led_strip", "log_path"): "LED_STRIP_LOG_PATH",
}


def _set_env(name, value):
    if name in os.environ:
        return
    if value is None:
        return
    text = str(value).strip()
    if text:
        os.environ[name] = text


def load_config(config_path):
    config_path = Path(config_path)
    if not config_path.is_file():
        print(f"[config] 找不到 {config_path}，使用現有環境變數")
        return

    try:
        with open(config_path, "rb") as fh:
            data = tomllib.load(fh)
    except Exception as exc:
        print(f"[config] {config_path} 解析失敗: {exc}")
        if "\\" in str(exc).lower() or "escape" in str(exc).lower():
            print("[config] TOML 路徑請使用正斜線 / 而非反斜線 \\")
            print('         例: pose_model = "models/yolo/yolo26m-pose.pt"')
        return

    configured = []

    for (section, key), env_name in SECTION_KEY_MAP.items():
        try:
            value = data[section][key]
        except KeyError:
            continue
        _set_env(env_name, value)
        configured.append(env_name)

    env_section = data.get("env", {})
    if isinstance(env_section, dict):
        for key, value in env_section.items():
            _set_env(key, value)
            configured.append(str(key))

    if configured:
        print(f"[config] 已從 {config_path} 載入 {len(configured)} 個設定值")
    else:
        print(f"[config] {config_path} 未找到需要套用的設定")


def get_config_summary(config_path):
    config_path = Path(config_path)
    if not config_path.is_file():
        return {"source": None, "values": {}}

    with open(config_path, "rb") as fh:
        try:
            data = tomllib.load(fh)
        except Exception as exc:
            return {"source": str(config_path), "values": {}, "error": str(exc)}

    values = {}
    for (section, key), env_name in SECTION_KEY_MAP.items():
        try:
            values[env_name] = data[section][key]
        except (KeyError, TypeError):
            pass

    env_section = data.get("env", {})
    if isinstance(env_section, dict):
        for key, value in env_section.items():
            values[str(key)] = value

    return {"source": str(config_path), "values": values}
