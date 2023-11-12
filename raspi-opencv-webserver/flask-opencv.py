from flask import Flask, send_file, render_template, Response
import cv2
import numpy as np
import time 

# Link to the IP Camera
url_cam = r"http://192.168.135.212/stream"

# Link to parking spot coordinates
url_txt = r"batas.txt"

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def gen():
    cap = cv2.VideoCapture(url_cam) # IP Camera
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: failed to capture image")
            break
        else:
            with open(url_yaml, 'r') as stream:
                parking_data = yaml.load(stream)
            parking_contours = []
            parking_bounding_rects = []
            parking_mask = []
            for park in parking_data:
                points = np.array(park['points'])
                rect = cv2.boundingRect(points)
                points_shifted = points.copy()
                points_shifted[:,0] = points[:,0] - rect[0] # shift contour to region of interest

                parking_contours.append(points)
                parking_bounding_rects.append(rect)
                parking_mask.append(cv2.fillPoly(np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8), [points_shifted], (255,255,255)))
            parking_mask = np.array(parking_mask)

            # Detect motorcycle in parking spot
            parking_status = [False]*len(parking_data)

            for ind, park in enumerate(parking_data):
                crop_img = frame[parking_bounding_rects[ind][1]:parking_bounding_rects[ind][1]+parking_bounding_rects[ind][3], parking_bounding_rects[ind][0]:parking_bounding_rects[ind][0]+parking_bounding_rects[ind][2]]
                crop_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
                crop_img = cv2.GaussianBlur(crop_img, (5, 5), 0)
                _, crop_img = cv2.threshold(crop_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                crop_img = cv2.bitwise_and(crop_img, crop_img, mask=parking_mask[ind])
                total_pix = cv2.countNonZero(crop_img)
                if parking_status[ind] == False:
                    if total_pix > 0.2*np.prod(crop_img.shape):
                        parking_status[ind] = True
                else:
                    if total_pix < 0.05*np.prod(crop_img.shape):
                        parking_status[ind] = False
            for ind, park in enumerate(parking_data):
                points = np.array(park['points'])
                if parking_status[ind]:
                    color = (0,255,0)
                else:
                    color = (0,0,255)
                cv2.drawContours(frame, [points], contourIdx=-1,
                                color=color, thickness=2, lineType=cv2.LINE_8)
                moments = cv2.moments(points)
                centroid = (int(moments['m10']/moments['m00']) - 3, int(moments['m01']/moments['m00']) + 3)
                cv2.putText(frame, str(park['id']), (centroid[0]+1, centroid[1]+1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
                cv2.putText(frame, str(park['id']), (centroid[0]+1, centroid[1]+1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1)
            ret, jpeg = cv2.imencode('.jpg', frame)
            frame = jpeg.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    cap.release()   

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)
