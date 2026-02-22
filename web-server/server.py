from flask import Flask, Response, abort, jsonify
import cv2
from flask_cors import CORS
import threading
import time
from ultralytics import YOLO
import sys
import glob

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
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
JPEG_QUALITY = 75
STREAM_FPS = 30
YOLO_SKIP = 5

# ------------------------
# Load YOLO
# ------------------------
model = YOLO("./best.pt")
try:
    model.fuse()
except AttributeError:
    pass

# ------------------------
# Auto-detect working USB cameras
# ------------------------
def detect_cameras(max_test=10):
    devices = glob.glob("/dev/video*")
    working = []

    for dev in devices:
        cap = cv2.VideoCapture(dev)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                working.append(dev)
                if DEBUG:
                    print(f"[DEBUG] Camera detected: {dev}")
            cap.release()
    return working[:max_test]

CAM_DEVICES = detect_cameras()
if not CAM_DEVICES:
    print("No cameras detected. Exiting.")
    sys.exit(1)

# ------------------------
# Initialize cameras
# ------------------------
def init_cams(devices):
    cams = []
    for i, dev in enumerate(devices):
        cap = cv2.VideoCapture(dev)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        if cap.isOpened():
            cams.append({
                "index": i,
                "dev": dev,
                "cap": cap,
                "frame": None,
                "detections": [],
                "frame_count": 0,
                "lock": threading.Lock()
            })
        else:
            cap.release()
            if DEBUG:
                print(f"[DEBUG] Failed to open {dev}")
    return cams

cams = init_cams(CAM_DEVICES)
cam_map = {cam['index']: cam for cam in cams}

if DEBUG:
    print(f"[DEBUG] Cameras initialized: {[cam['dev'] for cam in cams]}")

# ------------------------
# Capture & YOLO thread
# ------------------------
def capture_thread(cam):
    interval = 1.0 / STREAM_FPS
    while True:
        ret, frame = cam['cap'].read()
        if not ret:
            time.sleep(0.05)
            continue

        cam['frame_count'] += 1

        # YOLO detection every YOLO_SKIP frames
        if cam['frame_count'] % YOLO_SKIP == 0:
            try:
                results = model.predict(frame, verbose=False)
                detections = []
                for box in results[0].boxes:
                    detections.append({
                        "class": int(box.cls[0]),
                        "confidence": float(box.conf[0]),
                        "bbox": box.xyxy[0].tolist()
                    })
                with cam['lock']:
                    cam['detections'] = detections

                if DEBUG:
                    print(f"[YOLO] Cam {cam['index']} Frame {cam['frame_count']}: {len(detections)} detections")
            except Exception as e:
                print(f"YOLO error on cam {cam['index']}: {e}")

        with cam['lock']:
            cam['frame'] = frame

        time.sleep(interval)

# Start capture threads
for cam in cams:
    t = threading.Thread(target=capture_thread, args=(cam,), daemon=True)
    t.start()
    if DEBUG:
        print(f"[DEBUG] Started capture thread for camera {cam['index']} ({cam['dev']})")

# ------------------------
# MJPEG streaming generator
# ------------------------
def gen_frames(cam):
    while True:
        with cam['lock']:
            frame = cam['frame']
        if frame is None:
            time.sleep(0.05)
            continue

        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

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
    return Response(gen_frames(cam),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/detections/<int:cam_idx>")
def get_detections(cam_idx):
    cam = cam_map.get(cam_idx)
    if not cam:
        abort(404)
    with cam['lock']:
        return jsonify(cam['detections'])

# ------------------------
# Main
# ------------------------
if __name__ == "__main__":
    print(f"Starting Flask server with {len(cams)} cameras...")
    app.run(host="0.0.0.0", port=5000, threaded=True)