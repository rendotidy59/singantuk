import cv2
import mediapipe as mp
import numpy as np
from scipy.spatial import distance
from datetime import datetime
import json
import RPi.GPIO as GPIO
import time

# Setup GPIO
LED_PIN = 4  # GPIO4
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)

# Initialize MediaPipe FaceMesh
mp_face_mesh = mp.solutions.face_mesh

# EAR calculation
def eye_aspect_ratio(eye_landmarks):
    A = distance.euclidean(eye_landmarks[1], eye_landmarks[5])
    B = distance.euclidean(eye_landmarks[2], eye_landmarks[4])
    C = distance.euclidean(eye_landmarks[0], eye_landmarks[3])
    return (A + B) / (2.0 * C)

# MAR calculation
def mouth_aspect_ratio(mouth_landmarks):
    A = distance.euclidean(mouth_landmarks[13], mouth_landmarks[19])
    B = distance.euclidean(mouth_landmarks[14], mouth_landmarks[18])
    C = distance.euclidean(mouth_landmarks[15], mouth_landmarks[17])
    D = distance.euclidean(mouth_landmarks[12], mouth_landmarks[16])
    return round((A + B + C) / (3.0 * D), 4) if D != 0 else 0.0

# Indices
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
MOUTH = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 308, 78, 95, 88, 178, 87, 14, 317, 402]

# Thresholds
EAR_THRESHOLD = 0.25
MAR_THRESHOLD = 1.08
ALERT_FRAMES = 60  # 2 seconds at 30 FPS

# Initialize variables
closed_frames = 0
mouth_open_frames = 0  
cap = cv2.VideoCapture(0)

with mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5) as face_mesh:
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(frame_rgb)

            GPIO.output(LED_PIN, GPIO.LOW)  # Default OFF

            if results.multi_face_landmarks:
                face_landmarks = results.multi_face_landmarks[0]
                h, w, _ = frame.shape

                left_eye = [(int(face_landmarks.landmark[i].x * w), int(face_landmarks.landmark[i].y * h)) for i in LEFT_EYE]
                right_eye = [(int(face_landmarks.landmark[i].x * w), int(face_landmarks.landmark[i].y * h)) for i in RIGHT_EYE]
                mouth = [(int(face_landmarks.landmark[i].x * w), int(face_landmarks.landmark[i].y * h)) for i in MOUTH]

                avg_ear = (eye_aspect_ratio(left_eye) + eye_aspect_ratio(right_eye)) / 2.0
                avg_mar = mouth_aspect_ratio(mouth)
                timestamp = datetime.now().strftime('%H:%M:%S')

                alert_triggered = False

                # Drowsiness detection
                if avg_ear < EAR_THRESHOLD:
                    closed_frames += 1
                else:
                    closed_frames = 0

                if closed_frames >= ALERT_FRAMES:
                    cv2.putText(frame, "ANDA NGANTUK!", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                    alert_triggered = True

                # Yawn detection
                if avg_mar > MAR_THRESHOLD:
                    mouth_open_frames += 1
                else:
                    mouth_open_frames = 0

                if mouth_open_frames >= ALERT_FRAMES:
                    cv2.putText(frame, "ANDA MENGUAP!", (50, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                    alert_triggered = True

                if alert_triggered:
                    GPIO.output(LED_PIN, GPIO.HIGH)

                # Display EAR, MAR, and Time
                cv2.putText(frame, f'Time: {timestamp}', (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f'EAR: {avg_ear:.2f}', (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
                cv2.putText(frame, f'MAR: {avg_mar:.2f}', (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                # Save JSON
                latest_data = {"time": timestamp, "ear": avg_ear, "mar": avg_mar}
                with open("data.json", "w") as file:
                    json.dump(latest_data, file, indent=4)

            cv2.imshow('Frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        GPIO.cleanup()
