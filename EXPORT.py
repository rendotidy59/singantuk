import json
import csv
import os

# Define filenames
json_filename = "data.json"
csv_filename = "fatigue_data.csv"

# Function to load data from JSON
def load_json_data():
    if not os.path.exists(json_filename):
        print("JSON file not found!")
        return None
    
    with open(json_filename, "r") as file:
        try:
            data = json.load(file)
            return data if isinstance(data, dict) else None  # Ensure it's a dictionary
        except json.JSONDecodeError:
            print("Error reading JSON file!")
            return None

# Function to export data to CSV (keeps history)
def export_to_csv(data):
    file_exists = os.path.isfile(csv_filename)
    with open(csv_filename, mode="a", newline="") as file:
        writer = csv.writer(file)
        
        # Write header only if the file is new
        if not file_exists:
            writer.writerow(["Time", "EAR", "MAR", "Yawn Count"])
        
        # Write latest data
        writer.writerow([data["time"], round(data["ear"], 4), round(data["mar"], 4), data.get("yawn_count", 0)])
    print(f"Data successfully exported to {csv_filename}")

# Load JSON and export to CSV
data = load_json_data()
if data:
    export_to_csv(data)
else:
    print("No valid data to export!")

