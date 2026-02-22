#!/usr/bin/env python3
import cv2
import time

USB_CAM_INDICES = [0, 1, 2, 3]

print("Starting headless USB camera test...")

for idx in USB_CAM_INDICES:
    print(f"\nTesting camera index {idx}...")
    cap = cv2.VideoCapture(idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print(f"Camera {idx} could NOT be opened.")
        continue

    print(f"Camera {idx} opened successfully. Reading 10 frames...")
    success_count = 0
    for i in range(10):
        ret, frame = cap.read()
        if ret:
            success_count += 1
        time.sleep(0.1)

    cap.release()
    print(f"Camera {idx} captured {success_count}/10 frames successfully.")

print("\nUSB camera test complete!")