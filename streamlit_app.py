import pandas as pd
import streamlit as st
from datetime import datetime
import asyncio
import requests
import time, json, os
import logging
import numpy as np
import threading
from matplotlib import pyplot as plt
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from bson import ObjectId
import cv2
from fire_detection import fire_detection_loop, save_chat_data
from occupancy_detection import occupancy_detection_loop, load_occupancy_data
from no_access_rooms import no_access_detection_loop, load_no_access_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Atlas connection
MONGO_URI = "mongodb+srv://infernapeamber:g9kASflhhSQ26GMF@cluster0.mjoloub.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    client.admin.command('ping')
    db = client['vigil']
    cameras_collection = db['cameras']
    fire_settings_collection = db['fire_settings']
    occupancy_settings_collection = db['occupancy_settings']
    tailgating_settings_collection = db['tailgating_settings']
    no_access_settings_collection = db['no_access_settings']
    st.success("Connected to MongoDB Atlas successfully!")
except (ServerSelectionTimeoutError, ConnectionFailure) as e:
    st.error(f"Failed to connect to MongoDB Atlas: {str(e)}")
    st.write("**Troubleshooting Steps**:")
    st.write("1. Verify MongoDB Atlas credentials")
    st.write("2. Set Network Access to allow connections from your IP in MongoDB Atlas")
    st.write("3. Ensure pymongo>=4.8.0 is in requirements.txt")
    st.write("4. Check cluster status (not paused) in MongoDB Atlas")
    client = None
except Exception as e:
    st.error(f"Unexpected error connecting to MongoDB Atlas: {str(e)}")
    client = None

# Database Operations
def add_camera_to_db(name, address):
    """Add a camera to MongoDB."""
    if client is None:
        st.error("MongoDB not connected. Cannot add camera.")
        return None
    camera = {"name": name, "address": address}
    cameras_collection.insert_one(camera)
    return camera

def get_cameras_from_db():
    """Retrieve all cameras from MongoDB."""
    if client is None:
        return []
    return list(cameras_collection.find())

def remove_camera_from_db(camera_id):
    """Remove a camera from MongoDB by its ID."""
    if client is None:
        st.error("MongoDB not connected. Cannot remove camera.")
        return
    cameras_collection.delete_one({"_id": ObjectId(camera_id)})

def save_selected_cameras(collection, selected_cameras):
    """Save selected cameras for a specific module."""
    if client is None:
        st.error("MongoDB not connected. Cannot save camera selections.")
        return
    collection.replace_one({}, {"selected_cameras": selected_cameras}, upsert=True)

def get_selected_cameras(collection):
    """Retrieve selected cameras for a specific module."""
    if client is None:
        return []
    doc = collection.find_one()
    return doc.get("selected_cameras", []) if doc else []

# Utility Functions
def add_camera(name, address):
    """Add a camera to MongoDB and update session state."""
    if not name or not address:
        st.error("Camera name and address are required.")
        return
    if any(cam['name'] == name for cam in st.session_state.cameras):
        st.error("Camera name must be unique.")
        return
    camera = add_camera_to_db(name, address)
    if camera:
        st.session_state.cameras.append(camera)
        st.session_state[f"stream_active_{camera['_id']}"] = False
        st.success(f"Added camera: {name}")

def remove_camera(index):
    """Remove a camera from MongoDB and update session state."""
    if 0 <= index < len(st.session_state.cameras):
        camera = st.session_state.cameras[index]
        camera_id = str(camera['_id'])
        if st.session_state.get(f"stream_active_{camera_id}", False):
            st.session_state[f"stream_active_{camera_id}"] = False
        remove_camera_from_db(camera['_id'])
        st.session_state.cameras.pop(index)
        st.session_state.confirm_remove = None
        st.success(f"Removed camera: {camera['name']}")

# Video Streaming Functions
def capture_frame(address, camera_id):
    """Capture frames from a camera stream and update session state."""
    cap = cv2.VideoCapture(address)
    if not cap.isOpened():
        st.session_state[f"stream_error_{camera_id}"] = "Failed to connect to camera stream."
        return
    while st.session_state.get(f"stream_active_{camera_id}", False):
        ret, frame = cap.read()
        if not ret:
            st.session_state[f"stream_error_{camera_id}"] = "Failed to capture frame."
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        st.session_state[f"frame_{camera_id}"] = frame
        time.sleep(0.033)  # ~30 FPS
    cap.release()

def start_stream(address, camera_id):
    """Start video stream in a separate thread."""
    if not st.session_state.get(f"stream_active_{camera_id}", False):
        st.session_state[f"stream_active_{camera_id}"] = True
        st.session_state[f"stream_error_{camera_id}"] = None
        threading.Thread(target=capture_frame, args=(address, camera_id), daemon=True).start()

def stop_stream(camera_id):
    """Stop video stream."""
    st.session_state[f"stream_active_{camera_id}"] = False
    st.session_state[f"frame_{camera_id}"] = None
    st.session_state[f"stream_error_{camera_id}"] = None

# ML Model Operations
def run_fire_detection(address, camera_name):
    """Run fire detection for a specific camera."""
    try:
        fire_detection_loop(address, camera_name)
        st.session_state[f"fire_result_{camera_name}"] = "Fire detection completed."
    except Exception as e:
        st.session_state[f"fire_result_{camera_name}"] = f"Fire detection error: {str(e)}"

def run_occupancy_detection(address, camera_name):
    """Run occupancy detection for a specific camera."""
    try:
        occupancy_detection_loop(address, camera_name)
        st.session_state[f"occ_result_{camera_name}"] = "Occupancy detection completed."
    except Exception as e:
        st.session_state[f"occ_result_{camera_name}"] = f"Occupancy detection error: {str(e)}"

def run_no_access_detection(address, camera_name):
    """Run no-access room detection for a specific camera."""
    try:
        no_access_detection_loop(address, camera_name)
        st.session_state[f"no_access_result_{camera_name}"] = "No-access detection completed."
    except Exception as e:
        st.session_state[f"no_access_result_{camera_name}"] = f"No-access detection error: {str(e)}"

# Initialize session state
if 'cameras' not in st.session_state:
    st.session_state.cameras = get_cameras_from_db()
if 'confirm_remove' not in st.session_state:
    st.session_state.confirm_remove = None
if 'processing_active' not in st.session_state:
    st.session_state.processing_active = False
if 'fire_selected_cameras' not in st.session_state:
    st.session_state.fire_selected_cameras = get_selected_cameras(fire_settings_collection)
if 'occ_selected_cameras' not in st.session_state:
    st.session_state.occ_selected_cameras = get_selected_cameras(occupancy_settings_collection)
if 'tailgating_selected_cameras' not in st.session_state:
    st.session_state.tailgating_selected_cameras = get_selected_cameras(tailgating_settings_collection)
if 'no_access_selected_cameras' not in st.session_state:
    st.session_state.no_access_selected_cameras = get_selected_cameras(no_access_settings_collection)
if 'fire_detection_active' not in st.session_state:
    st.session_state.fire_detection_active = False
if 'telegram_status' not in st.session_state:
    st.session_state.telegram_status = []
if 'occ_detection_active' not in st.session_state:
    st.session_state.occ_detection_active = False
if 'occ_current_count' not in st.session_state:
    st.session_state.occ_current_count = 0
if 'occ_max_count' not in st.session_state:
    st.session_state.occ_max_count = 0
if 'occ_hourly_counts' not in st.session_state:
    st.session_state.occ_hourly_counts = [0] * 24
if 'occ_minute_counts' not in st.session_state:
    st.session_state.occ_minute_counts = [0] * 1440
if 'occ_last_update_hour' not in st.session_state:
    st.session_state.occ_last_update_hour = datetime.now().hour
if 'occ_last_update_minute' not in st.session_state:
    st.session_state.occ_last_update_minute = -1
if 'no_access_detection_active' not in st.session_state:
    st.session_state.no_access_detection_active = False

# Main App
st.title("📷 V.I.G.I.LLL - Video Intelligence for General Identification and Logging")

# Sidebar navigation
page = st.sidebar.radio(
    "Navigation",
    ["Camera Management", "Fire Detection", "Occupancy Dashboard", "Tailgating", "No-Access Rooms"],
    key="navigation"
)

# Page 1: Camera Management
if page == "Camera Management":
    st.header("📹 Camera Management")
    st.write("Add, remove, and manage surveillance cameras connected to the system.")

    with st.expander("➕ Add New Camera", expanded=True):
        with st.form("add_camera_form"):
            name = st.text_input("Camera Name", help="A unique identifier for the camera")
            address = st.text_input("Camera Address", help="RTSP or HTTP stream URL")
            submitted = st.form_submit_button("Add Camera")
            if submitted:
                if name and address:
                    if any(cam['name'] == name for cam in st.session_state.cameras):
                        st.error("Camera name must be unique.")
                    else:
                        add_camera(name, address)
                        st.rerun()
                else:
                    st.error("Both camera name and address are required.")

    st.header("📋 Camera List")
    if not st.session_state.cameras:
        st.info("No cameras have been added yet. Add your first camera above.")
    else:
        for i, cam in enumerate(st.session_state.cameras):
            camera_id = str(cam['_id'])
            st.subheader(f"Camera: {cam['name']}")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Address**: {cam['address']}")
            with col2:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.confirm_remove = i

            # Live Footage
            stream_placeholder = st.empty()
            col_stream = st.columns([1, 1])
            with col_stream[0]:
                if st.button("Start Stream", key=f"start_stream_{i}"):
                    start_stream(cam['address'], camera_id)
            with col_stream[1]:
                if st.button("Stop Stream", key=f"stop_stream_{i}"):
                    stop_stream(camera_id)

            if st.session_state.get(f"stream_active_{camera_id}", False):
                frame = st.session_state.get(f"frame_{camera_id}")
                error = st.session_state.get(f"stream_error_{camera_id}")
                if error:
                    stream_placeholder.error(error)
                elif frame is not None:
                    stream_placeholder.image(frame, caption=f"Live Feed: {cam['name']}", use_column_width=True)
                else:
                    stream_placeholder.info("Connecting to stream...")

            # ML Model Operations
            st.markdown("**Run ML Detections**:")
            col_ml = st.columns(3)
            with col_ml[0]:
                if st.button("Fire Detection", key=f"fire_{i}"):
                    threading.Thread(target=run_fire_detection, args=(cam['address'], cam['name']), daemon=True).start()
                    st.info(f"Running fire detection for {cam['name']}...")
            with col_ml[1]:
                if st.button("Occupancy Detection", key=f"occ_{i}"):
                    threading.Thread(target=run_occupancy_detection, args=(cam['address'], cam['name']), daemon=True).start()
                    st.info(f"Running occupancy detection for {cam['name']}...")
            with col_ml[2]:
                if st.button("No-Access Detection", key=f"no_access_{i}"):
                    threading.Thread(target=run_no_access_detection, args=(cam['address'], cam['name']), daemon=True).start()
                    st.info(f"Running no-access detection for {cam['name']}...")

            # Display ML Results
            fire_result_key = f"fire_result_{cam['name']}"
            occ_result_key = f"occ_result_{cam['name']}"
            no_access_result_key = f"no_access_result_{cam['name']}"
            if fire_result_key in st.session_state:
                st.write(f"Fire Detection Result: {st.session_state[fire_result_key]}")
            if occ_result_key in st.session_state:
                st.write(f"Occupancy Detection Result: {st.session_state[occ_result_key]}")
            if no_access_result_key in st.session_state:
                st.write(f"No-Access Detection Result: {st.session_state[no_access_result_key]}")

            st.markdown("---")

    if st.session_state.confirm_remove is not None:
        cam = st.session_state.cameras[st.session_state.confirm_remove]
        st.warning(f"Confirm removal of camera: {cam['name']}")
        st.write(f"Address: {cam['address']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Removal"):
                remove_camera(st.session_state.confirm_remove)
                st.rerun()
        with col2:
            if st.button("Cancel"):
                st.session_state.confirm_remove = None
                st.rerun()
