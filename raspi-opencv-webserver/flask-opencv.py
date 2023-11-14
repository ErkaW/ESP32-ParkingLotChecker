from flask import Flask, render_template, Response
import cv2
import numpy as np
import os
import matplotlib.pyplot as plt
from skimage.filters import threshold_otsu
from skimage.color import rgb2hsv

# Link to the IP Camera
url_cam = "http://192.168.223.97"

# Link to parking spot coordinates
spot_txt = os.path.join(os.path.dirname(__file__), "regions.txt")

spots = []
occupied = []

with open(spot_txt, "r") as f:
    lines = f.readlines()
    for line in lines:
        id, x1, y1, x2, y2, x3, y3, x4, y4 = map(int, line.split(","))
        spots.append([id, x1, y1, x2, y2, x3, y3, x4, y4])

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def draw_rect(frame, x1, y1, x2, y2, x3, y3, x4, y4, color):
    cv2.line(frame, (x1, y1), (x2, y2), color, 2)
    cv2.line(frame, (x2, y2), (x3, y3), color, 2)
    cv2.line(frame, (x3, y3), (x4, y4), color, 2)
    cv2.line(frame, (x4, y4), (x1, y1), color, 2)

def check_spot(frame, x1, y1, x2, y2, x3, y3, x4, y4):
    #thresh = threshold_otsu(frame)
    #sampleot = frame > thresh

    #fr = frame[y1:y3, x1:x3]

    sampleh = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    value = sampleh[..., 2]
    bitand = cv2.bitwise_and(sampleh[..., 1], sampleh[..., 2])
    threshold = 100
    _, binary_mask = cv2.threshold(value, threshold, 255, cv2.THRESH_BINARY)
    binary_mask = cv2.adaptiveThreshold(value, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Process each contour as needed
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
    
    cv2.imshow("Result", frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    #sampleh[...,2] = cv2.bitwise_and(sampleh[..., 1], sampleh[..., 2])
    #h, s, v1 = cv2.split(sampleh)
    #bitand_gray = cv2.cvtColor(sampleh[...,2], cv2.COLOR_BGR2GRAY)
    #bitand_blur = cv2.GaussianBlur(sampleh, (3,3), 0)

    #sobelx = cv2.Sobel(bitand_blur, cv2.CV_64F, 1, 0, ksize=5)
    #sobely = cv2.Sobel(bitand_blur, cv2.CV_64F, 0, 1, ksize=5)
    #sobelxy = cv2.Sobel(bitand_blur, cv2.CV_64F, 1, 1, ksize=5)

    #cv2.imshow("sobelx", sobelx)
    #cv2.waitKey(0)
    #cv2.imshow("sobely", sobely)
    #cv2.waitKey(0)
    #cv2.imshow("sobelxy", sobelxy)
    #cv2.waitKey(0)


    #edges = cv2.Canny(bitand_blur, 100, 200)
    #cv2.imshow("edges", edges)
    #cv2.imshow("gray-image", v1)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    
    
    #fig, ax = plt.subplots(1, 4, figsize=(15, 5))
    #ax[0].imshow(sampleh[..., 0], cmap='hsv')
    #ax[0].set_title('Hue') 
    #ax[1].imshow(sampleh[..., 1], cmap='hsv')
    #ax[1].set_title('Saturation')
    #ax[2].imshow(sampleh[..., 2], cmap='hsv')
    #ax[2].set_title('Value')
    #ax[3].imshow(bitand, cmap='hsv')
    #ax[3].set_title('Bitwise AND')
    #plt.show()

    
    #bitand = plt.subplots(1, 1, figsize=(15, 5))
    #bitand.imshow(bitand, cmap='hsv')
    #plt.imshow(bitand, cmap='hsv')
    #plt.show()

    #if sampleh.mean() < 0.5:
    #    return True
    #else:
    #    return False
    #if sampleh[..., 2].mean() < 0.2:
    #    return True
    #else:
    #    return False

def gen():
    cap = cv2.VideoCapture(url_cam + ":81/stream")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error connecting to camera")
            break

        for i, spot in enumerate(spots):
            id, x1, y1, x2, y2, x3, y3, x4, y4 = spot
            occupied_spot = check_spot(frame, x1, y1, x2, y2, x3, y3, x4, y4)
            if occupied_spot:
                occupied.append(id)

        for i, spot in enumerate(spots):
            id, x1, y1, x2, y2, x3, y3, x4, y4 = spot
            if id in occupied:
                draw_rect(frame, x1, y1, x2, y2, x3, y3, x4, y4, (0, 0, 255))
            else:
                draw_rect(frame, x1, y1, x2, y2, x3, y3, x4, y4, (0, 255, 0))

        ret, frame_encoded = cv2.imencode(".jpg", frame)
        if ret:
            yield (b'--frame\r\n'
                   b'Contentqqq-Type: image/jpeg\r\n\r\n' + frame_encoded.tobytes() + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
