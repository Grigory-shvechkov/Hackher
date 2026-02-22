#!/usr/bin/env python3
from flask import Flask, Response, abort, jsonify
from flask_cors import CORS
import cv2
from ultralytics import YOLO
import threading
import time
import glob
import sys

# ------------------------
# Config
# ------------------------
DEBUG = len(sys.argv) > 1 and sys.argv[1].lower() == "debug"

# Capture settings
CAP_WIDTH = 1280
CAP_HEIGHT = 720

# Streaming settings
STREAM_WIDTH = 320
STREAM_HEIGHT = 240
STREAM_FPS = 10
JPEG_QUALITY = 45
YOLO_SKIP = 12  # Run YOLO every N frames

# ------------------------
# Flask setup
# ------------------------
app = Flask(__name__)
CORS(app)

# ------------------------
# Load YOLO
# ------------------------
model = YOLO("./best.pt")
try:
    model.fuse()
except AttributeError:
    pass

# ------------------------
# Detect USB cameras safely
# ------------------------
def detect_usb_cameras(max_test=5):
    """Return list of /dev/video indices that can actually be opened."""
    usb_indices = []

    for dev in glob.glob("/dev/video*"):
        try:
            idx = int(dev.replace("/dev/video", ""))
            # Quick test to see if this device can open
            cap = cv2.VideoCapture(idx, cv2.CAP_ANY)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            ret, _ = cap.read()
            cap.release()

            if ret:
                usb_indices.append(idx)
                if DEBUG:
                    print(f"[INFO] Camera /dev/video{idx} detected.")
            if len(usb_indices) >= max_test:
                break
        except Exception:
            continue

    return usb_indices

# ------------------------
# Initialize cameras
# ------------------------
def init_cams(indices):
    cams = []
    for i, idx in enumerate(indices):
        cap = cv2.VideoCapture(idx, cv2.CAP_ANY)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAP_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAP_HEIGHT)

        ret, _ = cap.read()
        if not ret:
            cap.release()
            if DEBUG:
                print(f"[DEBUG] Camera /dev/video{idx} failed initial read.")
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
# YOLO detection (async)
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
# Capture thread
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

        # Run YOLO every YOLO_SKIP frames
        if cam["frame_count"] % YOLO_SKIP == 0:
            threading.Thread(target=run_yolo, args=(cam, frame.copy()), daemon=True).start()

        with cam["lock"]:
            cam["frame"] = frame

        elapsed = time.time() - start
        time.sleep(max(0, interval - elapsed))

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


@app.route("/cameras")
def cameras_list():
    """Return the list of cameras with their index and device path."""
    return jsonify([{"index": cam["index"], "device": cam["dev"]} for cam in cams])

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
    usb_indices = detect_usb_cameras()
    if not usb_indices:
        print("No USB cameras detected. Exiting.")
        sys.exit(1)

    cams = init_cams(usb_indices)
    if not cams:
        print("No cameras could be initialized. Exiting.")
        sys.exit(1)

    cam_map = {cam["index"]: cam for cam in cams}

    print(f"Starting Flask server with {len(cams)} camera(s)...")
    for cam in cams:
        threading.Thread(target=capture_thread, args=(cam,), daemon=True).start()

    app.run(host="0.0.0.0", port=5000, threaded=True)