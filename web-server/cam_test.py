# 1. Reduce JPEG quality further and frame size
STREAM_WIDTH = 160
STREAM_HEIGHT = 120
STREAM_FPS = 15
JPEG_QUALITY = 30  # Lower quality, smaller file size

# 2. Increase YOLO skip to run less frequently
YOLO_SKIP = 20  # Run YOLO every 20 frames instead of 12

# 3. Replace the capture_thread function with frame skipping
def capture_thread(cam):
    interval = 1.0 / STREAM_FPS
    frame_skip = 0
    while True:
        ret, frame = cam["cap"].read()
        if not ret:
            time.sleep(0.001)
            continue

        cam["frame_count"] += 1
        frame_skip += 1

        # Skip frames to maintain FPS
        if frame_skip < 2:
            continue
        frame_skip = 0

        # Run YOLO every YOLO_SKIP frames
        if cam["frame_count"] % YOLO_SKIP == 0:
            threading.Thread(target=run_yolo, args=(cam, frame.copy()), daemon=True).start()

        with cam["lock"]:
            cam["frame"] = frame

# 4. Use threading pool for YOLO (add at top)
from concurrent.futures import ThreadPoolExecutor
yolo_executor = ThreadPoolExecutor(max_workers=2)

# 5. Replace YOLO thread creation with:
        if cam["frame_count"] % YOLO_SKIP == 0:
            yolo_executor.submit(run_yolo, cam, frame.copy())
