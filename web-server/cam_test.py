#!/usr/bin/env python3
from flask import Flask, Response, abort, jsonify
from flask_cors import CORS
import cv2
from ultralytics import YOLO
import threading
import time
import glob
import os
import sys

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
# Load YOLO model
# ------------------------
model = YOLO("./best.pt")
try:
    model.fuse()
except AttributeError:
    pass

# ------------------------
# Detect USB cameras dynamically
# ------------------------
def detect_usb_cameras(max_test=10):
    usb_indices = []

    for dev in glob.glob("/dev/video*"):
        try:
            idx = int(dev.replace("/dev/video", ""))
            name_file = f"/sys/class/video4linux/{os.path.basename(dev)}/name"
            if os.path.exists(name_file):
                with open(name_file, "r") as f:
                    name = f.read().strip().lower()
                    if "usb" in name or "logitech" in name:
                        usb_indices.append(idx)
            if len(usb_indices) >= max_test:
                break
        except Exception:
            continue

    return usb_indices

# ------------------------
# Initialize cameras safely
# ------------------------
def init_cams(indices):
    cams = []

    for i, idx in enumerate(indices):
        cap = cv2.VideoCapture(idx, cv2.CAP_ANY)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAP_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAP_HEIGHT)

        # Quick test read
        ret, _ = cap.read()
        if not ret:
            if DEBUG:
                print(f"[DEBUG] Camera /dev/video{idx} failed initial read.")
            cap.release()
            continue

        cams.append({
            "index": i,
            "dev": f"/dev/video{idx}",
            "cap": cap,
            "frame": None,
            "detections": [],
            "frame_count": 0,
            "lock": threading.Lock()
        })

        if DEBUG:
            print(f"[DEBUG] Initialized camera {i} ({caps[-1]['dev']})")

    return cams

# ------------------------
# YOLO async detection
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
        print(f"[YOLO] Error on cam {cam['index']}: {e}")

# ------------------------
# Capture thread per camera
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

        # Run YOLO async every YOLO_SKIP frames
        if cam["frame_count"] % YOLO_SKIP == 0:
            threading.Thread(target=run_yolo, args=(cam, frame.copy()), daemon=True).start()

        with cam["lock"]:
            cam["frame"] = frame

        elapsed = time.time() - start
        time.sleep(max(0, interval - elapsed))

# ------------------------
# MJPEG streaming generator
# ------------------------
def gen_frames(cam):
    while True:
        with cam["lock"]:
            frame = cam["frame"]

        if frame is None:
            time.sleep(0.01)
            continue

        # Downscale for streaming
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
# Main entry
# ------------------------
if __name__ == "__main__":
    usb_indices = detect_usb_cameras()
    if not usb_indices:
        print("No USB cameras detected. Exiting.")
        sys.exit(1)

    cams = init_cams(usb_indices)
    if not cams:
        print("No cameras could be initialized. Exiting.")
        sys.exit(1)

    cam_map = {cam["index"]: cam for cam in cams}

    print(f"Starting Flask server with {len(cams)} cameras...")
    for cam in cams:
        threading.Thread(target=capture_thread, args=(cam,), daemon=True).start()

    app.run(host="0.0.0.0", port=5000, threaded=True)