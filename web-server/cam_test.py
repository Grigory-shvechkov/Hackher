#!/usr/bin/env python3
import cv2
import time

USB_CAM_INDICES = [0, 1, 2, 3]

print("Starting headless USB camera test...")

for idx in USB_CAM_INDICES:
    print(f"\nTesting camera index {idx}...")

    # Use V4L2 backend for Linux (faster and fewer warnings)
    cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # kill buffering
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print(f"Camera {idx} could NOT be opened.")
        cap.release()
        continue

    print(f"Camera {idx} opened successfully. Reading 10 frames...")

    success_count = 0
    for i in range(10):
        start = time.time()
        ret, frame = cap.read()
        if ret:
            success_count += 1
        # quick timeout to avoid hanging
        elapsed = time.time() - start
        time.sleep(max(0, 0.1 - elapsed))

    cap.release()
    print(f"Camera {idx} captured {success_count}/10 frames successfully.")

print("\nUSB camera test complete!")