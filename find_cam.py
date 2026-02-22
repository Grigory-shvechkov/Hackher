import cv2

def find_cams(max_index=10):
    cams = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                cams.append(i)
            cap.release()
    return cams

out = find_cams(5)
print("Available camera indexes:", out)