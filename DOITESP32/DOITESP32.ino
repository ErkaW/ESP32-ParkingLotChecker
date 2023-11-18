#include <WiFi.h>
#include <ESPAsyncWebServer.h>
#include <Servo.h>

const char* ssid = "CyanFlare";
const char* password = "op09lop11";

AsyncWebServer server(80);
Servo myservo;

int gateStatus = 0; // 0 for closed, 1 for open
int servoPos = 0;

const int trigPin = 5; // Ultrasonic sensor
const int echoPin = 18;
const float SOUND_SPEED = 0.034;
const float CM_TO_INCH = 0.393701;

void setup() {
  Serial.begin(115200);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  myservo.attach(13);
  servoClose();

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi");

  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request) {
    if (gateStatus == 0) {
      request->send(200, "text/plain", "0");
    } else {
      request->send(200, "text/plain", "1");
    }
  });
  server.begin();
}

void loop() {
  // No need for server.handleClient() in the loop with AsyncWebServer.
  // Instead, the server handles requests asynchronously.

  float distanceCm = measureDistance(trigPin, echoPin);

  Serial.print("Distance (cm): ");
  Serial.println(distanceCm);

  if (distanceCm <= 7) {
    if (gateStatus == 0) {
      servoOpen();
      gateStatus = 1;
    }
  } else {
    if (gateStatus == 1) {
      delay(500);
      servoClose();
      gateStatus = 0;
    }
  }
  delay(1000);
}

float measureDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  return duration * SOUND_SPEED / 2;
}

void servoOpen() {
  for (servoPos = 0; servoPos <= 90; servoPos += 1) {
    myservo.write(servoPos);
    delay(15);
  }
}

void servoClose() {
  for (servoPos = 90; servoPos >= 0; servoPos -= 1) {
    myservo.write(servoPos);
    delay(15);
  }
}