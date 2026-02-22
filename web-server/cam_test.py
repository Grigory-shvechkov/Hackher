#!/usr/bin/env python3
import cv2
import time

# List of likely USB camera indices
USB_CAM_INDICES = [0, 1, 2, 3]

print("Starting USB camera test...")

for idx in USB_CAM_INDICES:
    print(f"\nTesting camera index {idx}...")
    cap = cv2.VideoCapture(idx)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print(f"Camera {idx} could NOT be opened.")
        continue

    print(f"Camera {idx} opened successfully. Showing feed for 5 seconds...")
    start_time = time.time()

    while time.time() - start_time < 5:
        ret, frame = cap.read()
        if not ret:
            print(f"Camera {idx} frame read failed!")
            break

        cv2.imshow(f"Camera {idx}", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Camera {idx} test finished.")

print("\nUSB camera test complete!")