#!/usr/bin/env python3
import cv2
import glob
import os
import time

def detect_usb_cameras():
    """Return a list of /dev/video indices that are USB cameras."""
    usb_indices = []

    for dev in glob.glob("/dev/video*"):
        try:
            idx = int(dev.replace("/dev/video", ""))
            name_file = f"/sys/class/video4linux/{os.path.basename(dev)}/name"
            if os.path.exists(name_file):
                with open(name_file, "r") as f:
                    name = f.read().strip().lower()
                    # Include only USB or known camera names
                    if "usb" in name or "logitech" in name:
                        usb_indices.append(idx)
        except Exception:
            pass

    return usb_indices

def test_cameras():
    usb_cams = detect_usb_cameras()
    if not usb_cams:
        print("No USB cameras detected.")
        return

    print(f"Detected USB cameras at indices: {usb_cams}")

    for idx in usb_cams:
        print(f"\nTesting camera /dev/video{idx}...")
        cap = cv2.VideoCapture(idx, cv2.CAP_ANY)  # auto backend
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():
            print(f"Camera {idx} could NOT be opened.")
            cap.release()
            continue

        # Try to read 3 frames quickly
        success_count = 0
        for i in range(3):
            ret, _ = cap.read()
            if ret:
                success_count += 1
            time.sleep(0.05)  # small delay, non-blocking

        cap.release()
        print(f"Camera {idx} captured {success_count}/3 frames successfully.")

if __name__ == "__main__":
    test_cameras()