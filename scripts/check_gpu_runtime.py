import ctypes
import os
import subprocess
import sys
from pathlib import Path


def print_section(title):
    print(f'\n[{title}]')


def check_vc_runtime():
    if sys.platform != 'win32':
        print('vc++ runtime: skipped (not windows)')
        return

    missing = []
    for dll_name in ('vcruntime140.dll', 'msvcp140.dll'):
        try:
            ctypes.CDLL(dll_name)
            print(f'{dll_name}: OK')
        except OSError:
            missing.append(dll_name)
            print(f'{dll_name}: MISSING')
        except Exception as exc:  # pylint: disable=broad-except
            print(f'{dll_name}: unknown error ({exc})')

    if missing:
        print(
            '\n[!] Visual C++ Redistributable 未安裝或版本不完整。\n'
            '    PyTorch 需要 VC++ Runtime (2015-2022) 才能載入 c10.dll。\n'
            '    請從以下連結下載並安裝 x64 版本：\n'
            '    https://aka.ms/vc14/vc_redist.x64.exe\n'
            '    安裝後請重新開機。'
        )


def run_nvidia_smi():
    try:
        output = subprocess.check_output(
            [
                'nvidia-smi',
                '--query-gpu=name,driver_version,memory.total',
                '--format=csv,noheader',
            ],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=8,
        )
        print(output.strip())
    except Exception as exc:  # pylint: disable=broad-except
        print(f'nvidia-smi unavailable: {exc}')


def check_torch():
    try:
        import torch  # pylint: disable=import-outside-toplevel

        print(f'torch: {torch.__version__}')
        print(f'torch cuda build: {torch.version.cuda}')
        print(f'cuda available: {torch.cuda.is_available()}')
        print(f'cuda device count: {torch.cuda.device_count()}')
        if torch.cuda.is_available():
            print(f'cuda device 0: {torch.cuda.get_device_name(0)}')
    except Exception as exc:  # pylint: disable=broad-except
        print(f'torch unavailable: {exc}')


def check_onnxruntime():
    try:
        import onnxruntime as ort  # pylint: disable=import-outside-toplevel

        print(f'onnxruntime: {ort.__version__}')
        print(f'providers: {ort.get_available_providers()}')
    except Exception as exc:  # pylint: disable=broad-except
        print(f'onnxruntime unavailable: {exc}')


def check_imports():
    for package_name in ('ultralytics', 'insightface'):
        try:
            module = __import__(package_name)
            print(f'{package_name}: {getattr(module, "__version__", "installed")}')
        except Exception as exc:  # pylint: disable=broad-except
            print(f'{package_name}: unavailable ({exc})')


def check_config():
    from src.config import get_config_summary  # pylint: disable=import-outside-toplevel

    base_dir = Path(__file__).resolve().parent.parent
    config_path = base_dir / 'config.toml'
    summary = get_config_summary(config_path)

    if summary['source'] is None:
        print('config.toml: not found')
        return

    print(f'config.toml: {summary["source"]}')
    if not summary['values']:
        print('  (no values configured)')
        return

    for key, value in summary['values'].items():
        effective = os.getenv(key, value)
        source = 'config.toml' if os.getenv(key) else 'effective (not in env)'
        print(f'  {key} = {effective}  ({source})')


def main():
    print(f'python: {sys.executable}')
    print_section('Config')
    check_config()
    print_section('VC++ Runtime')
    check_vc_runtime()
    print_section('GPU')
    run_nvidia_smi()
    print_section('Torch / YOLO')
    check_torch()
    print(f'YOLO_DEVICE: {os.getenv("YOLO_DEVICE", "auto")}')
    print_section('ONNX Runtime / InsightFace')
    check_onnxruntime()
    print(f'INSIGHTFACE_PROVIDERS: {os.getenv("INSIGHTFACE_PROVIDERS", "auto")}')
    print(f'INSIGHTFACE_CTX_ID: {os.getenv("INSIGHTFACE_CTX_ID", "auto")}')
    print_section('Imports')
    check_imports()


if __name__ == '__main__':
    main()
