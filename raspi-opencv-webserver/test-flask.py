from flask import Flask, send_file, render_template, Response
import cv2
import numpy as np
import time

# Link to the IP Camera
url = r"http://192.168.23.97:81/stream"

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def gen():
    cap = cv2.VideoCapture(url) # IP Camera
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: failed to capture image")
            break
        else:
            cv2.imwrite('frame.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + open('frame.jpg', 'rb').read() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True, port=5000)