import sys
import cv2
import numpy as np


def test_kinect_v2():
    print("Testing Kinect v2...")

    import time
    if not hasattr(time, 'clock'):
        time.clock = time.perf_counter

    try:
        import comtypes
        if hasattr(comtypes, '_check_version'):
            comtypes._check_version = lambda *args, **kwargs: None
        from pykinect2 import PyKinectRuntime, PyKinectV2
    except ImportError as e:
        print(f"Failed to import PyKinect2: {e}")
        print("Make sure 'uv sync' has been run.")
        return False
    except Exception as e:
        print(f"Unexpected import error: {e}")
        return False

    print("PyKinect2 imported successfully. Opening sensor (may take 10-20s)...")
    try:
        runtime = PyKinectRuntime.PyKinectRuntime(
            PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Depth
        )
    except Exception as e:
        print(f"Failed to open Kinect v2 sensor: {e}")
        print("Is the Kinect v2 connected and the SDK installed?")
        return False

    print(f"Sensor opened successfully!")
    print(f"  Color frame: {runtime.color_frame_desc.Width}x{runtime.color_frame_desc.Height}")
    print(f"  Depth frame: {runtime.depth_frame_desc.Width}x{runtime.depth_frame_desc.Height}")

    print("Waiting for first color frame (up to 30 seconds)...")
    for i in range(300):
        if runtime.has_new_color_frame():
            frame = runtime.get_last_color_frame()
            h, w = runtime.color_frame_desc.Height, runtime.color_frame_desc.Width
            img = frame.reshape((h, w, 4))[:, :, :3]
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            print(f"  Frame {i + 1}: received ({img.shape[1]}x{img.shape[0]}), saving as test_kinect_output.jpg")
            cv2.imwrite("test_kinect_output.jpg", img)
            print("Kinect v2 is working correctly!")
            runtime.close()
            return True
        if i % 50 == 0:
            print(f"  ... waiting ({i // 10 + 1}s)")
        time.sleep(0.1)

    print("No color frame received after ~30 seconds.")
    print("Possible causes:")
    print("  1. Kinect is not plugged into a USB 3.0 (blue) port")
    print("  2. Kinect power supply is not connected")
    print("  3. Kinect sensor itself may have a hardware issue")
    runtime.close()
    return False


if __name__ == "__main__":
    if test_kinect_v2():
        sys.exit(0)
    else:
        sys.exit(1)
