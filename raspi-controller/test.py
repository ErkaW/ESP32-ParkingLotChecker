from flask import Flask, render_template # Install Flask
from flask_apscheduler import APScheduler # Install Flask-APScheduler
import RPi.GPIO as GPIO # Install RPi.GPIO
import time

app = Flask(__name__)
scheduler = APScheduler()

servo_pin = 18  # GPIO pin for controlling servo
gate_status = 0  # 0 for closed, 1 for open
servo_pos = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(servo_pin, GPIO.OUT)

def servo_open():
    global servo_pos
    for pos in range(0, 91, 1):
        pwm.ChangeDutyCycle(2 + (pos / 18))
        time.sleep(0.05)
    servo_pos = 90

def servo_close():
    global servo_pos
    for pos in range(90, -1, -1):
        pwm.ChangeDutyCycle(2 + (pos / 18))
        time.sleep(0.05)
    servo_pos = 0

def measure_distance(trig_pin, echo_pin):
    GPIO.output(trig_pin, GPIO.LOW)
    time.sleep(0.2)
    GPIO.output(trig_pin, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(trig_pin, GPIO.LOW)

    start_time = time.time()
    stop_time = time.time()

    while GPIO.input(echo_pin) == 0:
        start_time = time.time()

    while GPIO.input(echo_pin) == 1:
        stop_time = time.time()

    elapsed_time = stop_time - start_time
    distance_cm = elapsed_time * 34300 / 2
    return distance_cm

@app.route('/')
def index():
    status = 'Open' if gate_status == 1 else 'Closed'
    return render_template('index.html', status=status)

def check_distance():
    global gate_status
    distance_cm1 = measure_distance(5, 6)  # Adjust pin numbers as needed
    distance_cm2 = measure_distance(19, 26)  # Adjust pin numbers as needed

    print(f'Distance 1 (cm): {distance_cm1}')
    print(f'Distance 2 (cm): {distance_cm2}')

    if distance_cm1 <= 5 or distance_cm2 <= 5:
        if gate_status == 0:
            servo_open()
            gate_status = 1
    else:
        if gate_status == 1:
            time.sleep(0.5)
            servo_close()
            gate_status = 0

if __name__ == '__main__':
    GPIO.setup(5, GPIO.OUT)  # Ultrasonic sensor 1 trigger pin
    GPIO.setup(6, GPIO.IN)   # Ultrasonic sensor 1 echo pin
    GPIO.setup(19, GPIO.OUT)  # Ultrasonic sensor 2 trigger pin
    GPIO.setup(26, GPIO.IN)   # Ultrasonic sensor 2 echo pin

    pwm = GPIO.PWM(servo_pin, 50)
    pwm.start(0)

    scheduler.add_job(id='DistanceJob', func=check_distance, trigger='interval', seconds=1)
    scheduler.start()

    app.run(debug=True, host='0.0.0.0', port=5000)
