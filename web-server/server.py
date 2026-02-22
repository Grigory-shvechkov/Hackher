from flask import Flask, Response, abort, jsonify
import cv2
from flask_cors import CORS
import threading
import time
from ultralytics import YOLO
import sys
import glob
import os

# ------------------------
# Debug flag
# ------------------------
DEBUG = len(sys.argv) > 1 and sys.argv[1].lower() == "debug"

# ------------------------
# Flask setup
# ------------------------
app = Flask(__name__)
CORS(app)

# ------------------------
# Configuration
# ------------------------
CAP_WIDTH = 640
CAP_HEIGHT = 480
STREAM_WIDTH = 320
STREAM_HEIGHT = 240
STREAM_FPS = 8
JPEG_QUALITY = 45
YOLO_SKIP = 12

# ------------------------
# Load YOLO
# ------------------------
model = YOLO("./best.pt")
try:
    model.fuse()
except AttributeError:
    pass

# ------------------------
# Detect cameras fast (Pi-safe)
# ------------------------
def detect_cameras(max_test=10):
    devices = glob.glob("/dev/video*")
    working = []

    for dev in devices:
        try:
            idx = int(dev.replace("/dev/video", ""))

            # Quick check using V4L2 info (avoids warnings)
            dev_name_path = f"/sys/class/video4linux/{os.path.basename(dev)}/name"
            if os.path.exists(dev_name_path):
                with open(dev_name_path, "r") as f:
                    name = f.read().strip().lower()
                    if not any(k in name for k in ("usb", "camera")):
                        continue

            # Optional: fast VideoCapture check (0.1s timeout)
            cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            start = time.time()
            ret = False
            while time.time() - start < 0.1:
                ret, _ = cap.read()
                if ret:
                    break
            cap.release()
            if ret:
                working.append(idx)
                if DEBUG:
                    print(f"[DEBUG] Camera detected: /dev/video{idx}")

            if len(working) >= max_test:
                break

        except Exception:
            pass

    return working[:max_test]

CAM_DEVICES = detect_cameras()
if not CAM_DEVICES:
    print("No cameras detected. Exiting.")
    sys.exit(1)

# ------------------------
# Initialize cameras
# ------------------------
def init_cams(indices):
    cams = []

    for i, idx in enumerate(indices):
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        dev_name = f"/dev/video{idx}"

        if not cap.isOpened():
            if DEBUG:
                print(f"[DEBUG] Failed to open {dev_name}")
            cap.release()
            continue

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAP_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAP_HEIGHT)

        # Warm-up
        for _ in range(3):
            cap.read()

        cams.append({
            "index": i,
            "dev": dev_name,
            "cap": cap,
            "frame": None,
            "detections": [],
            "frame_count": 0,
            "lock": threading.Lock()
        })

        if DEBUG:
            print(f"[DEBUG] Initialized camera {i} ({dev_name})")

    return cams

cams = init_cams(CAM_DEVICES)
cam_map = {cam["index"]: cam for cam in cams}

# ------------------------
# Asynchronous YOLO function
# ------------------------
def run_yolo(cam, frame):
    try:
        results = model.predict(frame, imgsz=320, conf=0.25, verbose=False)
        detections = [{
            "class": int(box.cls[0]),
            "confidence": float(box.conf[0]),
            "bbox": box.xyxy[0].tolist()
        } for box in results[0].boxes]

        with cam["lock"]:
            cam["detections"] = detections

        if DEBUG:
            print(f"[YOLO] Cam {cam['index']} detections: {len(detections)}")

    except Exception as e:
        print(f"YOLO error on cam {cam['index']}: {e}")

# ------------------------
# Capture & YOLO thread
# ------------------------
def capture_thread(cam):
    interval = 1.0 / STREAM_FPS

    while True:
        start = time.time()
        ret, frame = cam["cap"].read()
        if not ret:
            time.sleep(0.01)
            continue

        cam["frame_count"] += 1

        # Async YOLO on every YOLO_SKIP frame
        if cam["frame_count"] % YOLO_SKIP == 0:
            threading.Thread(target=run_yolo, args=(cam, frame.copy()), daemon=True).start()

        with cam["lock"]:
            cam["frame"] = frame

        elapsed = time.time() - start
        time.sleep(max(0, interval - elapsed))

# Start threads
for cam in cams:
    threading.Thread(target=capture_thread, args=(cam,), daemon=True).start()

# ------------------------
# MJPEG streaming
# ------------------------
def gen_frames(cam):
    while True:
        with cam["lock"]:
            frame = cam["frame"]

        if frame is None:
            time.sleep(0.01)
            continue

        stream_frame = cv2.resize(frame, (STREAM_WIDTH, STREAM_HEIGHT), interpolation=cv2.INTER_NEAREST)
        ret, buffer = cv2.imencode(".jpg", stream_frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )

# ------------------------
# Flask routes
# ------------------------
@app.route("/camera_count")
def camera_count():
    return jsonify(len(cams))

@app.route("/video/<int:cam_idx>")
def video(cam_idx):
    cam = cam_map.get(cam_idx)
    if not cam:
        abort(404)
    return Response(gen_frames(cam), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/detections/<int:cam_idx>")
def get_detections(cam_idx):
    cam = cam_map.get(cam_idx)
    if not cam:
        abort(404)
    with cam["lock"]:
        return jsonify(cam["detections"])

# ------------------------
# Main
# ------------------------
if __name__ == "__main__":
    print(f"Starting Flask server with {len(cams)} cameras...")
    app.run(host="0.0.0.0", port=5000, threaded=True)