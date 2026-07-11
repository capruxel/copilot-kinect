# Repository Guidelines

## Environment

- Windows, Python 3.11–3.12 (`>=3.11,<3.13`)
- NVIDIA GPU + CUDA 13.0 (cu130 PyTorch wheels)
- Kinect v1/v2 SDK

```powershell
uv python install 3.11
uv sync
```

`uv` creates `.venv/` in the project root, which the Kinect DLL loader expects. Missing VC++ Redistributable (x64) causes `c10.dll` failures.

## Config

`config.toml` (loaded by `src/config.py:33`) → env vars for YOLO model path, device, Kinect backend, InsightFace providers, webhook URL. **TOML paths must use forward slashes** — backslashes break parsing.

```powershell
Copy-Item config.example.toml config.toml
Copy-Item data\administrators.example.json data\administrators.json
```

## Commands

```powershell
uv run python app.py                          # Flask (debug=False, threaded)
uv run python -m pytest tests -v              # no hardware needed
uv run python scripts\rebuild_face_db.py
uv run python scripts\check_gpu_runtime.py
uv run python clustering\k_means.py
prek run --all-files                          # run all pre-commit hooks
```

## Pre-commit

`prek.toml` — prek (Rust drop-in for pre-commit). Hooks: ruff + ruff-format, basedpyright type-check, pytest, builtin checks (whitespace, EOF, yaml, toml, merge-conflict, private-key).

```powershell
prek install       # install git hook shims
prek run           # run on staged files
```

## Gotchas

- **Background thread at import time**: `MinuteStudentCsvExporter` (`app.py:633`) starts on module load, exports per-minute CSV to `history/`. Stopped via `atexit`.
- **Thread safety**: `pending_training_captures` uses `threading.Lock()`.
- **Tests**: Pure logic only (detector, face_recognition_db, pose_depth_metrics, config). Hardware/GPU/model checks are in `scripts/`.
- **Determinism**: `clustering/k_means.py` uses `RANDOM_SEED = 42`.
- **Large assets** (`.pt`, `.onnx`, videos, embeddings, captures): don't commit.
- **Route shapes**: Preserve existing API shapes unless explicitly asked.
- **Git**: Conventional Commits (`feat:`, `fix:`, `build:`, `docs:`, `perf:`, `refactor:`, `chore:`). No force-push.
