# Author: Hitesh Ingale
# Project: Automated Face-Recognition Attendance System

import streamlit as st
import cv2
import face_recognition
import numpy as np
import pandas as pd
from datetime import datetime
import re
from database import register_user, get_all_users, mark_attendance, get_attendance_history

st.set_page_config(page_title="Smart Attendance System", page_icon="🤖", layout="wide")

# Inject Custom CSS
st.markdown("""
<style>
    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(30, 33, 48, 0.7) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Text Gradient for Headers */
    h1 {
        background: -webkit-linear-gradient(45deg, #6C63FF, #FF6584);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: fadeIn 1s ease-in-out;
        font-weight: 800;
    }
    
    /* Button Styling and Animation */
    .stButton>button {
        background: linear-gradient(45deg, #6C63FF, #FF6584);
        color: white;
        border: none;
        border-radius: 8px;
        transition: all 0.3s ease;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(108, 99, 255, 0.4);
    }
    
    /* Metric Cards Styling */
    [data-testid="stMetricValue"] {
        color: #FF6584;
        font-size: 2.5rem;
        font-weight: bold;
    }
    
    /* Fade In Animation */
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(-20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    
    /* Content wrapper animation */
    .block-container {
        animation: fadeIn 1s ease-in-out;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("📻 Navigation")
menu = st.sidebar.radio("Go to", ["📝 Register User", "📸 Live Attendance", "📊 Dashboard"])

if menu == "📝 Register User":
    st.title("📝 Register New User")
    st.markdown("Add a new member to the system by scanning their face.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### User Details")
        name = st.text_input("Enter Full Name")
        email = st.text_input("Enter Email Address")
        mobile = st.text_input("Enter 10-Digit Mobile Number")
    
    with col2:
        st.markdown("### Camera Feed")
        camera_image = st.camera_input("Take a picture to register")
    
    if camera_image is not None:
        file_bytes = np.asarray(bytearray(camera_image.read()), dtype=np.uint8)
        frame = cv2.imdecode(file_bytes, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        with col1:
            st.write("")
            if st.button("📸 Capture & Register"):
                if not name or not email or not mobile:
                    st.error("All fields (Name, Email, Mobile) are required!")
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    st.error("Invalid Email format!")
                elif not re.match(r"^\d{10}$", mobile):
                    st.error("Mobile number must be exactly 10 digits!")
                else:
                    with st.spinner("Processing face data..."):
                        face_locations = face_recognition.face_locations(frame_rgb)
                        if len(face_locations) > 0:
                            face_encoding = face_recognition.face_encodings(frame_rgb, face_locations)[0]
                            
                            # Check for duplicate face
                            known_names, known_encodings = get_all_users()
                            is_duplicate = False
                            if len(known_encodings) > 0:
                                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                                if True in matches:
                                    match_index = matches.index(True)
                                    st.error(f"🚨 This face is already registered under the name: **{known_names[match_index]}**")
                                    is_duplicate = True
                            
                            if not is_duplicate:
                                success, msg = register_user(name, email, mobile, face_encoding)
                                if success:
                                    st.success(f"🎉 User **{name}** registered successfully in database!")
                                    st.balloons()
                                else:
                                    st.error(msg)
                        else:
                            st.error("No face detected. Please try again.")

elif menu == "📸 Live Attendance":
    st.title("📸 Live Face-Recognition")
    st.markdown("Real-time face tracking and automatic attendance logging.")
    
    known_names, known_encodings = get_all_users()
    
    if len(known_names) == 0:
        st.warning("⚠️ No users registered yet. Please register users first.")
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            status_placeholder = st.empty()
            
        with col2:
            camera_image = st.camera_input("Take a picture to mark attendance")
        
        if camera_image is not None:
            file_bytes = np.asarray(bytearray(camera_image.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, 1)
            
            # Resize for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                name = "Unknown"
                
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_names[first_match_index]
                    
                    # Mark attendance in DB
                    success = mark_attendance(name)
                    if success:
                        status_placeholder.success(f"✅ Valid User: **{name}**'s today attendance submitted!")
                    else:
                        status_placeholder.info(f"ℹ️ Valid User: **{name}** (Attendance already marked for today)")
                else:
                    status_placeholder.error("🚨 Invalid User detected!")
                
                # Scale back up face locations
                top *= 4; right *= 4; bottom *= 4; left *= 4
                
                # Draw box and label
                color = (255, 99, 108) if name != "Unknown" else (0, 0, 255) # BGR colors
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                # Add a background rectangle for the text
                cv2.rectangle(frame, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            
            st.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_column_width=True)

elif menu == "📊 Dashboard":
    st.title("📊 Attendance Dashboard")
    st.markdown("Overview of the system's performance and recent attendance records.")
    
    known_names, _ = get_all_users()
    records = get_attendance_history()
    
    # Quick Stat Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="👥 Total Registered Users", value=len(known_names))
    with col2:
        today_str = datetime.now().strftime("%d-%m-%Y")
        today_records = [r for r in records if r["date"] == today_str]
        st.metric(label="✅ Today's Present", value=len(today_records))
    with col3:
        st.metric(label="📅 Total Logs", value=len(records))
    
    st.markdown("---")
    st.subheader("Recent Attendance Records")
    
    if records:
        df = pd.DataFrame(records)
        df = df[["date", "timestamp", "name", "day", "month", "year"]]
        # Streamlit styled dataframe
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No attendance records found yet.")
