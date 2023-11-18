from flask import Flask, render_template, Response
import cv2
import numpy as np
import os
import requests
#from skimage.color import rgb2hsv
from datetime import datetime

# URL video streaming
url = "http://192.168.137.211"
gate_url = "http://192.168.137.36"

# Region parking disini
spot_txt = os.path.join(os.path.dirname(__file__), "regions.txt")

# Inisialisasi variabel
spots = []

# Baca file regions.txt
with open(spot_txt, "r") as f:
    lines = f.readlines()
    for line in lines:
        id, x1, y1, x2, y2, x3, y3, x4, y4 = map(int, line.split(","))
        spots.append([id, x1, y1, x2, y2, x3, y3, x4, y4])

max_spots = len(spots)
parking_status = [False]*len(spots)     # False = kosong, True = terisi
parking_buffer = [None]*len(spots)     # Untuk menyimpan frame terakhir

# Inisialisasi Flask
app = Flask(__name__)

# Fungsi untuk menggabar rectangle regions nya
def draw_rect(frame, x1, y1, x2, y2, x3, y3, x4, y4, color):
    cv2.line(frame, (x1, y1), (x2, y2), color, 2)
    cv2.line(frame, (x2, y2), (x3, y3), color, 2)
    cv2.line(frame, (x3, y3), (x4, y4), color, 2)
    cv2.line(frame, (x4, y4), (x1, y1), color, 2)

# Fungsi untuk mengecek apakah spot parkir kosong atau tidak
def check_spot(frame, x1, y1, x2, y2, x3, y3, x4, y4):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    value = hsv[:,:,2]
    binary_mask = cv2.adaptiveThreshold(value, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    binary_mask = cv2.bitwise_not(binary_mask)
    binary_mask = cv2.medianBlur(binary_mask, 5)

    countours = cv2.findContours(binary_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    cv2.drawContours(binary_mask, countours, -1, (255, 255, 255), 2)

    binarymsk = binary_mask[y1:y3, x1:x3]

    # detcting the mean of the binary mask
    mean_value = np.mean(binarymsk)
    if mean_value > 50:
        return True
    else:
        return False

# Fungsi untuk menampilkan video streaming
def gen_frames():
    cap = cv2.VideoCapture(url + ":81/stream")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error capturing video")
            break
        
        for i, spot in enumerate(spots):
            id, x1, y1, x2, y2, x3, y3, x4, y4 = spot
            occupied_spot = check_spot(frame, x1, y1, x2, y2, x3, y3, x4, y4)
            parking_buffer[i] = occupied_spot
            
        # Update parking_status individually for each spot
        for i in range(len(spots)):
            parking_status[i] = parking_buffer[i]

        for i, spot in enumerate(spots):
            id, x1, y1, x2, y2, x3, y3, x4, y4 = spot
            if parking_status[i]:
                draw_rect(frame, x1, y1, x2, y2, x3, y3, x4, y4, (0, 0, 255))  # Merah
            else:
                draw_rect(frame, x1, y1, x2, y2, x3, y3, x4, y4, (0, 255, 0))  # Hijau
        # Mengambil waktu saat ini
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")

        # Menghitung jumlah spot parkir yang kosong dan terisi
        free_spots = parking_status.count(False)
        occupied_spots = parking_status.count(True)

        # Overlay text
        cv2.putText(frame, "Free Spots: {}".format(free_spots), (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(frame, "Occupied Spots: {}".format(occupied_spots), (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, "Last Update: {}".format(current_time), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Overlay gate status
        gate_status = requests.get(gate_url).text
        cv2.putText(frame, "Gate Status: {}".format(gate_status), (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # Encode frame ke JPEG
        ret, frame_encoded = cv2.imencode(".jpg", frame)
        if ret:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_encoded.tobytes() + b'\r\n')

# Fungsi untuk menampilkan halaman index.html
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
