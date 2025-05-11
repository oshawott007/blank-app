# import pandas as pd
# import streamlit as st
# import logging
# import numpy as np
# import threading
# from pymongo import MongoClient
# from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
# from bson import ObjectId
# import cv2
# import time
# from fire_detection import fire_detection_loop
# from occupancy_detection import occupancy_detection_loop
# from no_access_rooms import no_access_detection_loop

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # MongoDB Atlas connection
# MONGO_URI = "mongodb+srv://infernapeamber:g9kASflhhSQ26GMF@cluster0.mjoloub.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# try:
#     client = MongoClient(
#         MONGO_URI,
#         serverSelectionTimeoutMS=5000,
#         connectTimeoutMS=30000,
#         socketTimeoutMS=30000
#     )
#     client.admin.command('ping')
#     db = client['vigil']
#     cameras_collection = db['cameras']
#     st.success("Connected to MongoDB Atlas successfully!")
# except (ServerSelectionTimeoutError, ConnectionFailure) as e:
#     st.error(f"Failed to connect to MongoDB Atlas: {str(e)}")
#     st.write("**Troubleshooting Steps**:")
#     st.write("1. Verify MongoDB Atlas credentials")
#     st.write("2. Set Network Access to allow connections from your IP in MongoDB Atlas")
#     st.write("3. Ensure pymongo>=4.8.0 is in requirements.txt")
#     st.write("4. Check cluster status (not paused) in MongoDB Atlas")
#     client = None
# except Exception as e:
#     st.error(f"Unexpected error connecting to MongoDB Atlas: {str(e)}")
#     client = None

# # Database Operations
# def add_camera_to_db(name, address):
#     """Add a camera to MongoDB."""
#     if client is None:
#         st.error("MongoDB not connected. Cannot add camera.")
#         return None
#     camera = {"name": name, "address": address}
#     cameras_collection.insert_one(camera)
#     return camera

# def get_cameras_from_db():
#     """Retrieve all cameras from MongoDB."""
#     if client is None:
#         return []
#     return list(cameras_collection.find())

# def remove_camera_from_db(camera_id):
#     """Remove a camera from MongoDB by its ID."""
#     if client is None:
#         st.error("MongoDB not connected. Cannot remove camera.")
#         return
#     cameras_collection.delete_one({"_id": ObjectId(camera_id)})

# # Utility Functions
# def add_camera(name, address):
#     """Add a camera to MongoDB and update session state."""
#     if not name or not address:
#         st.error("Camera name and address are required.")
#         return
#     if any(cam['name'] == name for cam in st.session_state.cameras):
#         st.error("Camera name must be unique.")
#         return
#     camera = add_camera_to_db(name, address)
#     if camera:
#         st.session_state.cameras.append(camera)
#         camera_id = str(camera['_id'])
#         st.session_state[f"stream_active_{camera_id}"] = True
#         start_stream(camera['address'], camera_id)
#         st.success(f"Added camera: {name}")

# def remove_camera(index):
#     """Remove a camera from MongoDB and update session state."""
#     if 0 <= index < len(st.session_state.cameras):
#         camera = st.session_state.cameras[index]
#         camera_id = str(camera['_id'])
#         if st.session_state.get(f"stream_active_{camera_id}", False):
#             st.session_state[f"stream_active_{camera_id}"] = False
#         remove_camera_from_db(camera['_id'])
#         st.session_state.cameras.pop(index)
#         st.session_state.confirm_remove = None
#         st.success(f"Removed camera: {camera['name']}")

# # Video Streaming Functions
# def capture_frame(address, camera_id):
#     """Capture frames from a camera stream and update session state."""
#     cap = cv2.VideoCapture(address)
#     if not cap.isOpened():
#         st.session_state[f"stream_error_{camera_id}"] = "Failed to connect to camera stream."
#         return
#     while st.session_state.get(f"stream_active_{camera_id}", False):
#         ret, frame = cap.read()
#         if not ret:
#             st.session_state[f"stream_error_{camera_id}"] = "Failed to capture frame."
#             break
#         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         st.session_state[f"frame_{camera_id}"] = frame
#         time.sleep(0.033)  # ~30 FPS
#     cap.release()

# def start_stream(address, camera_id):
#     """Start video stream in a separate thread."""
#     if not st.session_state.get(f"stream_active_{camera_id}", False):
#         st.session_state[f"stream_active_{camera_id}"] = True
#         st.session_state[f"stream_error_{camera_id}"] = None
#         threading.Thread(target=capture_frame, args=(address, camera_id), daemon=True).start()

# # ML Model Operations
# def run_fire_detection(address, camera_name):
#     """Run fire detection for a specific camera."""
#     try:
#         fire_detection_loop(address, camera_name)
#         st.session_state[f"fire_result_{camera_name}"] = "Fire detection completed."
#     except Exception as e:
#         st.session_state[f"fire_result_{camera_name}"] = f"Fire detection error: {str(e)}"

# def run_occupancy_detection(address, camera_name):
#     """Run occupancy detection for a specific camera."""
#     try:
#         occupancy_detection_loop(address, camera_name)
#         st.session_state[f"occ_result_{camera_name}"] = "Occupancy detection completed."
#     except Exception as e:
#         st.session_state[f"occ_result_{camera_name}"] = f"Occupancy detection error: {str(e)}"

# def run_no_access_detection(address, camera_name):
#     """Run no-access room detection for a specific camera."""
#     try:
#         no_access_detection_loop(address, camera_name)
#         st.session_state[f"no_access_result_{camera_name}"] = "No-access detection completed."
#     except Exception as e:
#         st.session_state[f"no_access_result_{camera_name}"] = f"No-access detection error: {str(e)}"

# # Initialize session state
# if 'cameras' not in st.session_state:
#     st.session_state.cameras = get_cameras_from_db()
#     for cam in st.session_state.cameras:
#         camera_id = str(cam['_id'])
#         st.session_state[f"stream_active_{camera_id}"] = True
#         start_stream(cam['address'], camera_id)
# if 'confirm_remove' not in st.session_state:
#     st.session_state.confirm_remove = None

# # Main App
# st.title("📷 V.I.G.I.LLL - Video Intelligence for General Identification and Logging")

# # Camera Management
# st.header("📹 Camera Management")
# st.write("Add, remove, and manage surveillance cameras connected to the system.")

# with st.expander("➕ Add New Camera", expanded=True):
#     with st.form("add_camera_form"):
#         name = st.text_input("Camera Name", help="A unique identifier for the camera")
#         address = st.text_input("Camera Address", help="RTSP or HTTP stream URL")
#         submitted = st.form_submit_button("Add Camera")
#         if submitted:
#             if name and address:
#                 if any(cam['name'] == name for cam in st.session_state.cameras):
#                     st.error("Camera name must be unique.")
#                 else:
#                     add_camera(name, address)
#                     st.rerun()
#             else:
#                 st.error("Both camera name and address are required.")

# # Camera Table
# st.header("📋 Camera List")
# if not st.session_state.cameras:
#     st.info("No cameras have been added yet. Add your first camera above.")
# else:
#     st.write("**Added Cameras**:")
#     for i, cam in enumerate(st.session_state.cameras):
#         col1, col2, col3 = st.columns([2, 4, 1])
#         with col1:
#             st.markdown(f"**{cam['name']}**")
#         with col2:
#             st.code(cam['address'], language="text")
#         with col3:
#             if st.button("Remove", key=f"remove_{i}"):
#                 st.session_state.confirm_remove = i

# if st.session_state.confirm_remove is not None:
#     cam = st.session_state.cameras[st.session_state.confirm_remove]
#     st.warning(f"Confirm removal of camera: {cam['name']}")
#     st.write(f"Address: {cam['address']}")
#     col1, col2 = st.columns(2)
#     with col1:
#         if st.button("Confirm Removal"):
#             remove_camera(st.session_state.confirm_remove)
#             st.rerun()
#     with col2:
#         if st.button("Cancel"):
#             st.session_state.confirm_remove = None
#             st.rerun()

# # Live Streams and ML Operations
# st.header("📹 Live Streams and ML Operations")
# if not st.session_state.cameras:
#     st.info("No live streams available. Add cameras to view live feeds.")
# else:
#     for i in range(0, len(st.session_state.cameras), 2):
#         cols = st.columns(2)
#         for j, col in enumerate(cols):
#             if i + j < len(st.session_state.cameras):
#                 cam = st.session_state.cameras[i + j]
#                 camera_id = str(cam['_id'])
#                 with col:
#                     st.subheader(f"Camera: {cam['name']}")
#                     stream_placeholder = st.empty()
#                     if st.session_state.get(f"stream_active_{camera_id}", False):
#                         frame = st.session_state.get(f"frame_{camera_id}")
#                         error = st.session_state.get(f"stream_error_{camera_id}")
#                         if error:
#                             stream_placeholder.error(error)
#                         elif frame is not None:
#                             stream_placeholder.image(frame, caption=f"Live Feed: {cam['name']}", use_column_width=True)
#                         else:
#                             stream_placeholder.info("Connecting to stream...")
                    
#                     # ML Model Operations
#                     st.markdown("**Run ML Detections**:")
#                     col_ml = st.columns(3)
#                     with col_ml[0]:
#                         if st.button("Fire Detection", key=f"fire_{i+j}"):
#                             threading.Thread(target=run_fire_detection, args=(cam['address'], cam['name']), daemon=True).start()
#                             st.info(f"Running fire detection for {cam['name']}...")
#                     with col_ml[1]:
#                         if st.button("Occupancy Detection", key=f"occ_{i+j}"):
#                             threading.Thread(target=run_occupancy_detection, args=(cam['address'], cam['name']), daemon=True).start()
#                             st.info(f"Running occupancy detection for {cam['name']}...")
#                     with col_ml[2]:
#                         if st.button("No-Access Detection", key=f"no_access_{i+j}"):
#                             threading.Thread(target=run_no_access_detection, args=(cam['address'], cam['name']), daemon=True).start()
#                             st.info(f"Running no-access detection for {cam['name']}...")

#                     # Display ML Results
#                     fire_result_key = f"fire_result_{cam['name']}"
#                     occ_result_key = f"occ_result_{cam['name']}"
#                     no_access_result_key = f"no_access_result_{cam['name']}"
#                     if fire_result_key in st.session_state:
#                         st.write(f"Fire Detection Result: {st.session_state[fire_result_key]}")
#                     if occ_result_key in st.session_state:
#                         st.write(f"Occupancy Detection Result: {st.session_state[occ_result_key]}")
#                     if no_access_result_key in st.session_state:
#                         st.write(f"No-Access Detection Result: {st.session_state[no_access_result_key]}")











import streamlit as st
import logging
import threading
import time
import cv2
import math
import numpy as np
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from bson import ObjectId
from fire_detection import fire_model, classnames
from occupancy_detection import occupancy_detection_loop
from no_access_rooms import no_access_detection_loop
import cvzone
from queue import Queue

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)
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
    try:
        result = cameras_collection.insert_one(camera)
        camera['_id'] = result.inserted_id
        return camera
    except Exception as e:
        st.error(f"Failed to add camera to MongoDB: {str(e)}")
        logger.error(f"MongoDB insert error: {str(e)}")
        return None

def get_cameras_from_db():
    """Retrieve all cameras from MongoDB."""
    if client is None:
        return []
    try:
        return list(cameras_collection.find())
    except Exception as e:
        st.error(f"Failed to retrieve cameras: {str(e)}")
        logger.error(f"MongoDB retrieve error: {str(e)}")
        return []

def remove_camera_from_db(camera_id):
    """Remove a camera from MongoDB by its ID."""
    if client is None:
        st.error("MongoDB not connected. Cannot remove camera.")
        return
    try:
        cameras_collection.delete_one({"_id": ObjectId(camera_id)})
    except Exception as e:
        st.error(f"Failed to remove camera: {str(e)}")
        logger.error(f"MongoDB delete error: {str(e)}")

# Utility Functions
def add_camera(name, address):
    """Add a camera to MongoDB and start its stream."""
    if not name or not address:
        st.error("Camera name and address are required.")
        return
    if any(cam['name'] == name for cam in st.session_state.cameras):
        st.error("Camera name must be unique.")
        return
    if not (address.startswith("rtsp://") or address.startswith("http://") or address.startswith("https://")):
        st.error("Invalid URL format. Use rtsp:// or http(s)://")
        return
    camera = add_camera_to_db(name, address)
    if camera:
        st.session_state.cameras.append(camera)
        camera_id = str(camera['_id'])
        st.session_state[f"stream_active_{camera_id}"] = True
        st.session_state[f"frame_queue_{camera_id}"] = Queue(maxsize=10)
        st.session_state[f"fire_active_{camera_id}"] = False
        st.session_state[f"occ_active_{camera_id}"] = False
        st.session_state[f"no_access_active_{camera_id}"] = False
        start_stream(camera['address'], camera_id)
        st.success(f"Added camera: {name}")
        logger.info(f"Added camera {name} with address {address}")

def remove_camera(index):
    """Remove a camera from MongoDB and stop its stream."""
    if 0 <= index < len(st.session_state.cameras):
        camera = st.session_state.cameras[index]
        camera_id = str(camera['_id'])
        if st.session_state.get(f"stream_active_{camera_id}", False):
            st.session_state[f"stream_active_{camera_id}"] = False
            logger.info(f"Stopped stream for camera {camera['name']}")
        remove_camera_from_db(camera['_id'])
        st.session_state.cameras.pop(index)
        st.session_state.confirm_remove = None
        st.success(f"Removed camera: {camera['name']}")
        logger.info(f"Removed camera {camera['name']}")

# Video Streaming Functions
def capture_frame(address, camera_id, camera_name):
    """Capture and process frames from a camera stream."""
    logger.debug(f"Attempting to open stream for {camera_name} at {address}")
    
    # Set OpenCV parameters for better RTSP handling
    cap = cv2.VideoCapture(address)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FPS, 20)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    
    if not cap.isOpened():
        st.session_state[f"stream_error_{camera_id}"] = f"Failed to connect to stream at {address}"
        logger.error(f"Failed to open stream for {camera_name} at {address}")
        return
    
    logger.debug(f"Stream opened successfully for {camera_name}")
    frame_queue = st.session_state.get(f"frame_queue_{camera_id}")
    
    while st.session_state.get(f"stream_active_{camera_id}", False):
        ret, frame = cap.read()
        if not ret:
            st.session_state[f"stream_error_{camera_id}"] = f"Connection lost for {camera_name}"
            logger.error(f"Failed to capture frame for {camera_name}")
            time.sleep(2)  # Wait before retrying
            continue
        
        try:
            frame = cv2.resize(frame, (640, 480))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            if frame_queue:
                if frame_queue.full():
                    frame_queue.get()  # Discard oldest frame
                frame_queue.put(frame.copy())
            
            st.session_state[f"frame_{camera_id}"] = frame
        except Exception as e:
            logger.error(f"Error processing frame for {camera_name}: {str(e)}")
        
        time.sleep(0.033)  # ~30 FPS
    
    cap.release()
    logger.debug(f"Stream closed for {camera_name}")

def start_stream(address, camera_id):
    """Start video stream in a separate thread."""
    if not st.session_state.get(f"stream_active_{camera_id}", False):
        st.session_state[f"stream_active_{camera_id}"] = True
        st.session_state[f"stream_error_{camera_id}"] = None
        st.session_state[f"frame_{camera_id}"] = None
        
        camera_name = next((cam['name'] for cam in st.session_state.cameras 
                          if str(cam['_id']) == camera_id), "Unknown Camera")
        
        threading.Thread(
            target=capture_frame, 
            args=(address, camera_id, camera_name),
            daemon=True
        ).start()
        logger.info(f"Started stream thread for {camera_name} at {address}")

# ML Model Operations
def process_fire_detection(frame, camera_id):
    """Process a single frame with fire detection model."""
    try:
        result = fire_model(frame, stream=True)
        fire_detected = False
        
        for info in result:
            boxes = info.boxes
            for box in boxes:
                confidence = box.conf[0]
                confidence = math.ceil(confidence * 100)
                Class = int(box.cls[0])
                if confidence > 80:
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 5)
                    cvzone.putTextRect(frame, f'{classnames[Class]} {confidence}%', 
                                     [x1 + 8, y1 + 100], scale=1.5, thickness=2)
                    fire_detected = True
                    cv2.putText(frame, "ALERT!", (50, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        st.session_state[f"fire_frame_{camera_id}"] = frame if fire_detected else None
        return fire_detected
    except Exception as e:
        logger.error(f"Fire detection processing error: {str(e)}")
        return False

def run_fire_detection(camera_id, camera_name):
    """Run fire detection on a camera stream."""
    try:
        st.session_state[f"fire_active_{camera_id}"] = True
        logger.info(f"Starting fire detection for {camera_name}")
        frame_queue = st.session_state.get(f"frame_queue_{camera_id}")
        
        if frame_queue is None:
            raise Exception("Frame queue not initialized")
            
        while (st.session_state.get(f"stream_active_{camera_id}", False) and 
               st.session_state.get(f"fire_active_{camera_id}", False)):
            if not frame_queue.empty():
                frame = frame_queue.get()
                process_fire_detection(frame, camera_id)
            time.sleep(0.033)
            
        logger.info(f"Fire detection stopped for {camera_name}")
    except Exception as e:
        st.error(f"Fire detection error for {camera_name}: {str(e)}")
        logger.error(f"Fire detection error for {camera_name}: {str(e)}")
    finally:
        st.session_state[f"fire_active_{camera_id}"] = False

def run_occupancy_detection(camera_id, camera_name):
    """Run occupancy detection on a camera stream."""
    try:
        st.session_state[f"occ_active_{camera_id}"] = True
        logger.info(f"Starting occupancy detection for {camera_name}")
        frame_queue = st.session_state.get(f"frame_queue_{camera_id}")
        
        if frame_queue is None:
            raise Exception("Frame queue not initialized")
            
        while (st.session_state.get(f"stream_active_{camera_id}", False) and 
               st.session_state.get(f"occ_active_{camera_id}", False)):
            if not frame_queue.empty():
                frame = frame_queue.get()
                processed_frame, count = occupancy_detection_loop(frame)
                st.session_state[f"occ_frame_{camera_id}"] = processed_frame
                st.session_state[f"occ_count_{camera_id}"] = count
            time.sleep(0.033)
            
        logger.info(f"Occupancy detection stopped for {camera_name}")
    except Exception as e:
        st.error(f"Occupancy detection error for {camera_name}: {str(e)}")
        logger.error(f"Occupancy detection error for {camera_name}: {str(e)}")
    finally:
        st.session_state[f"occ_active_{camera_id}"] = False

def run_no_access_detection(camera_id, camera_name):
    """Run no-access room detection on a camera stream."""
    try:
        st.session_state[f"no_access_active_{camera_id}"] = True
        logger.info(f"Starting no-access detection for {camera_name}")
        frame_queue = st.session_state.get(f"frame_queue_{camera_id}")
        
        if frame_queue is None:
            raise Exception("Frame queue not initialized")
            
        while (st.session_state.get(f"stream_active_{camera_id}", False) and 
               st.session_state.get(f"no_access_active_{camera_id}", False)):
            if not frame_queue.empty():
                frame = frame_queue.get()
                processed_frame, alert = no_access_detection_loop(frame)
                st.session_state[f"no_access_frame_{camera_id}"] = processed_frame
                st.session_state[f"no_access_alert_{camera_id}"] = alert
            time.sleep(0.033)
            
        logger.info(f"No-access detection stopped for {camera_name}")
    except Exception as e:
        st.error(f"No-access detection error for {camera_name}: {str(e)}")
        logger.error(f"No-access detection error for {camera_name}: {str(e)}")
    finally:
        st.session_state[f"no_access_active_{camera_id}"] = False

# Initialize session state
if 'cameras' not in st.session_state:
    st.session_state.cameras = get_cameras_from_db()
    for cam in st.session_state.cameras:
        camera_id = str(cam['_id'])
        st.session_state[f"stream_active_{camera_id}"] = True
        st.session_state[f"frame_queue_{camera_id}"] = Queue(maxsize=10)
        st.session_state[f"fire_active_{camera_id}"] = False
        st.session_state[f"occ_active_{camera_id}"] = False
        st.session_state[f"no_access_active_{camera_id}"] = False
        start_stream(cam['address'], camera_id)
if 'confirm_remove' not in st.session_state:
    st.session_state.confirm_remove = None

# Main App
st.title("📷 V.I.G.I.LLL - Video Intelligence for General Identification and Logging")

# Camera Management
st.header("📹 Camera Management")
st.write("Add, remove, and manage surveillance cameras. Provide a valid RTSP or HTTP stream URL to view live footage.")

with st.expander("➕ Add New Camera", expanded=True):
    with st.form("add_camera_form"):
        name = st.text_input("Camera Name", help="A unique identifier for the camera")
        address = st.text_input("Camera Address", help="RTSP or HTTP stream URL (e.g., rtsp://your-camera-ip:554/stream)")
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

# Camera List
st.header("📋 Camera List")
if not st.session_state.cameras:
    st.info("No cameras have been added yet. Add your first camera above.")
else:
    st.write("**Added Cameras**:")
    for i, cam in enumerate(st.session_state.cameras):
        col1, col2, col3 = st.columns([2, 4, 1])
        with col1:
            st.markdown(f"**{cam['name']}**")
        with col2:
            st.code(cam['address'], language="text")
        with col3:
            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.confirm_remove = i

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

# Live Streams and ML Operations
st.header("📹 Live Footage and Operations")
if not st.session_state.cameras:
    st.info("No live footage available. Add cameras to view live feeds.")
else:
    for cam in st.session_state.cameras:
        camera_id = str(cam['_id'])
        
        # Camera Feed Section
        st.subheader(f"📷 {cam['name']}")
        
        # Live feed display
        live_placeholder = st.empty()
        if st.session_state.get(f"stream_active_{camera_id}", False):
            error = st.session_state.get(f"stream_error_{camera_id}")
            frame = st.session_state.get(f"frame_{camera_id}")
            
            if error:
                live_placeholder.error(error)
                # Attempt to reconnect
                if st.button("Retry Connection", key=f"retry_{camera_id}"):
                    st.session_state[f"stream_error_{camera_id}"] = None
                    start_stream(cam['address'], camera_id)
            elif frame is not None:
                live_placeholder.image(frame, caption=f"Live Feed: {cam['name']}", use_column_width=True)
            else:
                live_placeholder.info("Connecting to stream...")
        
        # Operation Controls
        st.subheader("Operations")
        
        # Toggle buttons for each operation
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fire_active = st.session_state.get(f"fire_active_{camera_id}", False)
            if st.button("🔴 Stop Fire Detection" if fire_active else "🟢 Start Fire Detection", 
                        key=f"fire_toggle_{camera_id}"):
                if fire_active:
                    st.session_state[f"fire_active_{camera_id}"] = False
                else:
                    threading.Thread(
                        target=run_fire_detection, 
                        args=(camera_id, cam['name']), 
                        daemon=True
                    ).start()
        
        with col2:
            occ_active = st.session_state.get(f"occ_active_{camera_id}", False)
            if st.button("🔴 Stop Occupancy Detection" if occ_active else "🟢 Start Occupancy Detection", 
                        key=f"occ_toggle_{camera_id}"):
                if occ_active:
                    st.session_state[f"occ_active_{camera_id}"] = False
                else:
                    threading.Thread(
                        target=run_occupancy_detection, 
                        args=(camera_id, cam['name']), 
                        daemon=True
                    ).start()
        
        with col3:
            no_access_active = st.session_state.get(f"no_access_active_{camera_id}", False)
            if st.button("🔴 Stop No-Access Detection" if no_access_active else "🟢 Start No-Access Detection", 
                        key=f"no_access_toggle_{camera_id}"):
                if no_access_active:
                    st.session_state[f"no_access_active_{camera_id}"] = False
                else:
                    threading.Thread(
                        target=run_no_access_detection, 
                        args=(camera_id, cam['name']), 
                        daemon=True
                    ).start()
        
        # Status indicators
        status_cols = st.columns(3)
        with status_cols[0]:
            st.write(f"Fire Detection: {'🟢 Running' if st.session_state.get(f'fire_active_{camera_id}', False) else '🔴 Stopped'}")
        with status_cols[1]:
            st.write(f"Occupancy Detection: {'🟢 Running' if st.session_state.get(f'occ_active_{camera_id}', False) else '🔴 Stopped'}")
        with status_cols[2]:
            st.write(f"No-Access Detection: {'🟢 Running' if st.session_state.get(f'no_access_active_{camera_id}', False) else '🔴 Stopped'}")
        
        st.markdown("---")  # Separator between cameras
