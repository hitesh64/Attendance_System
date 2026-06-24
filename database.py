import pymongo
from datetime import datetime
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
client = pymongo.MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client["AttendanceSystemDB"]
users_col = db["Users"]
logs_col = db["Attendance_Logs"]

def register_user(name, email, mobile, face_encoding):
    """Saves user details and face encoding. Checks for duplicates."""
    # Check if email or mobile already exists
    existing = users_col.find_one({"$or": [{"email": email}, {"mobile": mobile}]})
    if existing:
        if existing.get("email") == email:
            return False, "Email already registered!"
        return False, "Mobile number already registered!"
        
    user_data = {
        "name": name,
        "email": email,
        "mobile": mobile,
        "encoding": face_encoding.tolist(),
        "registered_on": datetime.now()
    }
    users_col.insert_one(user_data)
    return True, "Success"

def get_all_users():
    """Fetches all registered users and their encodings"""
    users = list(users_col.find({}))
    known_names = []
    known_encodings = []
    for user in users:
        known_names.append(user["name"])
        known_encodings.append(np.array(user["encoding"])) # Convert back to numpy array
    return known_names, known_encodings

def mark_attendance(name):
    """Logs attendance if not already marked for the current day"""
    now = datetime.now()
    date_str = now.strftime("%d-%m-%Y")
    
    # Check if already marked today
    existing_record = logs_col.find_one({"name": name, "date": date_str})
    
    if not existing_record:
        log_data = {
            "name": name,
            "timestamp": now.strftime("%H:%M:%S"),
            "date": date_str,
            "day": now.strftime("%A"),
            "month": now.strftime("%B"),
            "year": now.strftime("%Y")
        }
        logs_col.insert_one(log_data)
        return True # Successfully marked
    return False # Already marked

def get_attendance_history():
    """Fetches all logs for the dashboard"""
    return list(logs_col.find({}, {"_id": 0}).sort("date", -1))
