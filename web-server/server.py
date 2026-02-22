from flask import Flask, Response, abort, jsonify
import cv2
from flask_cors import CORS
import threading
import time
from ultralytics import YOLO
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
CAM_COUNT = 3
FRAME_WIDTH = 640       # upscale for better detection
FRAME_HEIGHT = 480
JPEG_QUALITY = 75       # better quality for YOLO
STREAM_FPS = 30
YOLO_SKIP = 5      

# ------------------------
# Load YOLO
# ------------------------
model = YOLO("./best.pt")
try:
    model.fuse()
except AttributeError:
    pass  # some YOLO versions don't have fuse

# ------------------------
# Initialize cameras
# ------------------------
def get_cams(count: int):
    cams = []
    for i in range(count):
        cap = cv2.VideoCapture(i)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        if cap.isOpened():
            cams.append({
                "index": i,
                "cap": cap,
                "frame": None,
                "detections": [],
                "frame_count": 0,
                "lock": threading.Lock()
            })
            if DEBUG:
                print(f"[DEBUG] Camera {i} initialized")
        else:
            cap.release()
    return cams

cams = get_cams(CAM_COUNT)
cam_map = {cam['index']: cam for cam in cams}
if DEBUG:
    print(f"[DEBUG] Cameras available: {[cam['index'] for cam in cams]}")

# ------------------------
# Capture & YOLO thread per camera
# ------------------------
def capture_thread(cam):
    interval = 1.0 / STREAM_FPS
    while True:
        ret, frame = cam['cap'].read()
        if not ret:
            time.sleep(0.05)
            continue

        cam['frame_count'] += 1

        # Run YOLO every YOLO_SKIP frames
        if cam['frame_count'] % YOLO_SKIP == 0:
            try:
                results = model.predict(frame, verbose=False)
                detections = []
                for box in results[0].boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    detections.append({
                        "class": cls,
                        "confidence": conf,
                        "bbox": xyxy
                    })
                with cam['lock']:
                    cam['detections'] = detections

                if DEBUG:
                    print(f"[YOLO] Cam {cam['index']} Frame {cam['frame_count']}: {len(detections)} detections")
                    for det in detections:
                        print(f"  -> Class {det['class']} Conf {det['confidence']:.2f} BBox {det['bbox']}")

            except Exception as e:
                print(f"YOLO error on cam {cam['index']}: {e}")

        # Always update frame
        with cam['lock']:
            cam['frame'] = frame

        time.sleep(interval)

# Start threads
for cam in cams:
    t = threading.Thread(target=capture_thread, args=(cam,), daemon=True)
    t.start()
    if DEBUG:
        print(f"[DEBUG] Started capture thread for camera {cam['index']}")

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

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

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
    if DEBUG:
        print("[DEBUG] Starting Flask server in DEBUG mode...")
    else:
        print("Starting Flask server...")
    app.run(host="0.0.0.0", port=5000, threaded=True)