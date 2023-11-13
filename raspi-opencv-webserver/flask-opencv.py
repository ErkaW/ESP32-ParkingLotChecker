from flask import Flask, send_file, render_template, Response
import cv2
import numpy as np
import time
import os
from shapely.geometry import box
from shapely.geometry import Polygon as shapely_poly

# Link to the IP Camera
url_cam = "http://192.168.135.212/stream"

# Link to parking spot coordinates
spot_txt = "region.txt"

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def gen():
    cap = cv2.VideoCapture(url_cam)  # Capture video from the IP camera
    while True:
        spots = []  # Clear the spots list for each frame
        ret, frame = cap.read()
        if not ret:
            print("Error connecting to camera")
            break

        with open(spot_txt, "r") as f:
            lines = f.readlines()
            for line in lines:
                x1, y1, x2, y2 = line.split(",")
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                spots.append((x1, y1, x2, y2))
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        ret, frame_encoded = cv2.imencode(".jpg", frame)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_encoded.tobytes() + b'\r\n')

    cap.release()  # Release the video capture when done

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
