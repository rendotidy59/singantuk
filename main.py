import threading
import os
import subprocess
import sys
import json
import time
import csv

# Define filenames
data_file = "data.json"
csv_file = "analysis_log.csv"

# Ensure CSV has a header if it doesn't exist
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "EAR", "MAR"])

# Function to start FACE_DETECTION.py
def run_face_detection():
    subprocess.run([sys.executable, "FACE_DETECTION.py"])

# Function to run EXPORT.py
def run_export():
    subprocess.run([sys.executable, "EXPORT.py"])

# Function to read and log JSON data
def update_analysis_log(last_log):
    try:
        if os.path.exists(data_file):
            with open(data_file, "r") as file:
                data = json.load(file)

            # Ensure data is a dictionary
            if isinstance(data, list) and len(data) > 0:
                data = data[-1]  # Get latest record if it's a list

            if not isinstance(data, dict) or "time" not in data:
                print("Error: Invalid JSON format in data.json")
                return

            analysis_time = data["time"]
            ear = data.get("ear", 0)
            mar = data.get("mar", 0)

            # Check if data has changed before logging
            if last_log.get("time") != analysis_time:
                last_log["time"] = analysis_time
                last_log["ear"] = ear
                last_log["mar"] = mar
                
                with open(csv_file, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([analysis_time, f"{ear:.2f}", f"{mar:.2f}"])
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error reading data.json. Ensure FACE_DETECTION.py is running.")

# Function to check and restart FACE_DETECTION.py if it stops
def check_face_detection():
    global face_detection_thread
    if not face_detection_thread.is_alive():
        print("Restarting FACE_DETECTION.py...")
        face_detection_thread = threading.Thread(target=run_face_detection, daemon=True)
        face_detection_thread.start()

# Function to periodically log fatigue data
def log_fatigue_data_periodically():
    last_log = {"time": None, "ear": None, "mar": None}
    while True:
        update_analysis_log(last_log)
        run_export()
        check_face_detection()
        time.sleep(10)  # Update every 10 seconds

# Main execution
if __name__ == "__main__":
    face_detection_thread = threading.Thread(target=run_face_detection, daemon=True)
    face_detection_thread.start()
    log_fatigue_data_periodically()