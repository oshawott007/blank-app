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











# import streamlit as st
# import logging
# import threading
# import time
# import cv2
# import math
# import numpy as np
# from pymongo import MongoClient
# from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
# from bson import ObjectId
# from fire_detection import fire_model, classnames
# from occupancy_detection import occupancy_detection_loop
# from no_access_rooms import no_access_detection_loop
# import cvzone
# from queue import Queue

# # Configure logging for debugging
# logging.basicConfig(level=logging.DEBUG)
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
#     try:
#         result = cameras_collection.insert_one(camera)
#         camera['_id'] = result.inserted_id
#         return camera
#     except Exception as e:
#         st.error(f"Failed to add camera to MongoDB: {str(e)}")
#         logger.error(f"MongoDB insert error: {str(e)}")
#         return None

# def get_cameras_from_db():
#     """Retrieve all cameras from MongoDB."""
#     if client is None:
#         return []
#     try:
#         return list(cameras_collection.find())
#     except Exception as e:
#         st.error(f"Failed to retrieve cameras: {str(e)}")
#         logger.error(f"MongoDB retrieve error: {str(e)}")
#         return []

# def remove_camera_from_db(camera_id):
#     """Remove a camera from MongoDB by its ID."""
#     if client is None:
#         st.error("MongoDB not connected. Cannot remove camera.")
#         return
#     try:
#         cameras_collection.delete_one({"_id": ObjectId(camera_id)})
#     except Exception as e:
#         st.error(f"Failed to remove camera: {str(e)}")
#         logger.error(f"MongoDB delete error: {str(e)}")

# # Utility Functions
# def add_camera(name, address):
#     """Add a camera to MongoDB and start its stream."""
#     if not name or not address:
#         st.error("Camera name and address are required.")
#         return
#     if any(cam['name'] == name for cam in st.session_state.cameras):
#         st.error("Camera name must be unique.")
#         return
#     if not (address.startswith("rtsp://") or address.startswith("http://") or address.startswith("https://")):
#         st.error("Invalid URL format. Use rtsp:// or http(s)://")
#         return
#     camera = add_camera_to_db(name, address)
#     if camera:
#         st.session_state.cameras.append(camera)
#         camera_id = str(camera['_id'])
#         st.session_state[f"stream_active_{camera_id}"] = True
#         st.session_state[f"frame_queue_{camera_id}"] = Queue(maxsize=10)
#         st.session_state[f"fire_active_{camera_id}"] = False
#         st.session_state[f"occ_active_{camera_id}"] = False
#         st.session_state[f"no_access_active_{camera_id}"] = False
#         start_stream(camera['address'], camera_id)
#         st.success(f"Added camera: {name}")
#         logger.info(f"Added camera {name} with address {address}")

# def remove_camera(index):
#     """Remove a camera from MongoDB and stop its stream."""
#     if 0 <= index < len(st.session_state.cameras):
#         camera = st.session_state.cameras[index]
#         camera_id = str(camera['_id'])
#         if st.session_state.get(f"stream_active_{camera_id}", False):
#             st.session_state[f"stream_active_{camera_id}"] = False
#             logger.info(f"Stopped stream for camera {camera['name']}")
#         remove_camera_from_db(camera['_id'])
#         st.session_state.cameras.pop(index)
#         st.session_state.confirm_remove = None
#         st.success(f"Removed camera: {camera['name']}")
#         logger.info(f"Removed camera {camera['name']}")

# # Video Streaming Functions
# def capture_frame(address, camera_id, camera_name):
#     """Capture and process frames from a camera stream."""
#     logger.debug(f"Attempting to open stream for {camera_name} at {address}")
    
#     # Set OpenCV parameters for better RTSP handling
#     cap = cv2.VideoCapture(address)
#     cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
#     cap.set(cv2.CAP_PROP_FPS, 20)
#     cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    
#     if not cap.isOpened():
#         st.session_state[f"stream_error_{camera_id}"] = f"Failed to connect to stream at {address}"
#         logger.error(f"Failed to open stream for {camera_name} at {address}")
#         return
    
#     logger.debug(f"Stream opened successfully for {camera_name}")
#     frame_queue = st.session_state.get(f"frame_queue_{camera_id}")
    
#     while st.session_state.get(f"stream_active_{camera_id}", False):
#         ret, frame = cap.read()
#         if not ret:
#             st.session_state[f"stream_error_{camera_id}"] = f"Connection lost for {camera_name}"
#             logger.error(f"Failed to capture frame for {camera_name}")
#             time.sleep(2)  # Wait before retrying
#             continue
        
#         try:
#             frame = cv2.resize(frame, (640, 480))
#             frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
#             if frame_queue:
#                 if frame_queue.full():
#                     frame_queue.get()  # Discard oldest frame
#                 frame_queue.put(frame.copy())
            
#             st.session_state[f"frame_{camera_id}"] = frame
#         except Exception as e:
#             logger.error(f"Error processing frame for {camera_name}: {str(e)}")
        
#         time.sleep(0.033)  # ~30 FPS
    
#     cap.release()
#     logger.debug(f"Stream closed for {camera_name}")

# def start_stream(address, camera_id):
#     """Start video stream in a separate thread."""
#     if not st.session_state.get(f"stream_active_{camera_id}", False):
#         st.session_state[f"stream_active_{camera_id}"] = True
#         st.session_state[f"stream_error_{camera_id}"] = None
#         st.session_state[f"frame_{camera_id}"] = None
        
#         camera_name = next((cam['name'] for cam in st.session_state.cameras 
#                           if str(cam['_id']) == camera_id), "Unknown Camera")
        
#         threading.Thread(
#             target=capture_frame, 
#             args=(address, camera_id, camera_name),
#             daemon=True
#         ).start()
#         logger.info(f"Started stream thread for {camera_name} at {address}")

# # ML Model Operations
# def process_fire_detection(frame, camera_id):
#     """Process a single frame with fire detection model."""
#     try:
#         result = fire_model(frame, stream=True)
#         fire_detected = False
        
#         for info in result:
#             boxes = info.boxes
#             for box in boxes:
#                 confidence = box.conf[0]
#                 confidence = math.ceil(confidence * 100)
#                 Class = int(box.cls[0])
#                 if confidence > 80:
#                     x1, y1, x2, y2 = box.xyxy[0]
#                     x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
#                     cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 5)
#                     cvzone.putTextRect(frame, f'{classnames[Class]} {confidence}%', 
#                                      [x1 + 8, y1 + 100], scale=1.5, thickness=2)
#                     fire_detected = True
#                     cv2.putText(frame, "ALERT!", (50, 150), 
#                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
#         st.session_state[f"fire_frame_{camera_id}"] = frame if fire_detected else None
#         return fire_detected
#     except Exception as e:
#         logger.error(f"Fire detection processing error: {str(e)}")
#         return False

# def run_fire_detection(camera_id, camera_name):
#     """Run fire detection on a camera stream."""
#     try:
#         st.session_state[f"fire_active_{camera_id}"] = True
#         logger.info(f"Starting fire detection for {camera_name}")
#         frame_queue = st.session_state.get(f"frame_queue_{camera_id}")
        
#         if frame_queue is None:
#             raise Exception("Frame queue not initialized")
            
#         while (st.session_state.get(f"stream_active_{camera_id}", False) and 
#                st.session_state.get(f"fire_active_{camera_id}", False)):
#             if not frame_queue.empty():
#                 frame = frame_queue.get()
#                 process_fire_detection(frame, camera_id)
#             time.sleep(0.033)
            
#         logger.info(f"Fire detection stopped for {camera_name}")
#     except Exception as e:
#         st.error(f"Fire detection error for {camera_name}: {str(e)}")
#         logger.error(f"Fire detection error for {camera_name}: {str(e)}")
#     finally:
#         st.session_state[f"fire_active_{camera_id}"] = False

# def run_occupancy_detection(camera_id, camera_name):
#     """Run occupancy detection on a camera stream."""
#     try:
#         st.session_state[f"occ_active_{camera_id}"] = True
#         logger.info(f"Starting occupancy detection for {camera_name}")
#         frame_queue = st.session_state.get(f"frame_queue_{camera_id}")
        
#         if frame_queue is None:
#             raise Exception("Frame queue not initialized")
            
#         while (st.session_state.get(f"stream_active_{camera_id}", False) and 
#                st.session_state.get(f"occ_active_{camera_id}", False)):
#             if not frame_queue.empty():
#                 frame = frame_queue.get()
#                 processed_frame, count = occupancy_detection_loop(frame)
#                 st.session_state[f"occ_frame_{camera_id}"] = processed_frame
#                 st.session_state[f"occ_count_{camera_id}"] = count
#             time.sleep(0.033)
            
#         logger.info(f"Occupancy detection stopped for {camera_name}")
#     except Exception as e:
#         st.error(f"Occupancy detection error for {camera_name}: {str(e)}")
#         logger.error(f"Occupancy detection error for {camera_name}: {str(e)}")
#     finally:
#         st.session_state[f"occ_active_{camera_id}"] = False

# def run_no_access_detection(camera_id, camera_name):
#     """Run no-access room detection on a camera stream."""
#     try:
#         st.session_state[f"no_access_active_{camera_id}"] = True
#         logger.info(f"Starting no-access detection for {camera_name}")
#         frame_queue = st.session_state.get(f"frame_queue_{camera_id}")
        
#         if frame_queue is None:
#             raise Exception("Frame queue not initialized")
            
#         while (st.session_state.get(f"stream_active_{camera_id}", False) and 
#                st.session_state.get(f"no_access_active_{camera_id}", False)):
#             if not frame_queue.empty():
#                 frame = frame_queue.get()
#                 processed_frame, alert = no_access_detection_loop(frame)
#                 st.session_state[f"no_access_frame_{camera_id}"] = processed_frame
#                 st.session_state[f"no_access_alert_{camera_id}"] = alert
#             time.sleep(0.033)
            
#         logger.info(f"No-access detection stopped for {camera_name}")
#     except Exception as e:
#         st.error(f"No-access detection error for {camera_name}: {str(e)}")
#         logger.error(f"No-access detection error for {camera_name}: {str(e)}")
#     finally:
#         st.session_state[f"no_access_active_{camera_id}"] = False

# # Initialize session state
# if 'cameras' not in st.session_state:
#     st.session_state.cameras = get_cameras_from_db()
#     for cam in st.session_state.cameras:
#         camera_id = str(cam['_id'])
#         st.session_state[f"stream_active_{camera_id}"] = True
#         st.session_state[f"frame_queue_{camera_id}"] = Queue(maxsize=10)
#         st.session_state[f"fire_active_{camera_id}"] = False
#         st.session_state[f"occ_active_{camera_id}"] = False
#         st.session_state[f"no_access_active_{camera_id}"] = False
#         start_stream(cam['address'], camera_id)
# if 'confirm_remove' not in st.session_state:
#     st.session_state.confirm_remove = None

# # Main App
# st.title("📷 V.I.G.I.LLL - Video Intelligence for General Identification and Logging")

# # Camera Management
# st.header("📹 Camera Management")
# st.write("Add, remove, and manage surveillance cameras. Provide a valid RTSP or HTTP stream URL to view live footage.")

# with st.expander("➕ Add New Camera", expanded=True):
#     with st.form("add_camera_form"):
#         name = st.text_input("Camera Name", help="A unique identifier for the camera")
#         address = st.text_input("Camera Address", help="RTSP or HTTP stream URL (e.g., rtsp://your-camera-ip:554/stream)")
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

# # Camera List
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
# st.header("📹 Live Footage and Operations")
# if not st.session_state.cameras:
#     st.info("No live footage available. Add cameras to view live feeds.")
# else:
#     for cam in st.session_state.cameras:
#         camera_id = str(cam['_id'])
        
#         # Camera Feed Section
#         st.subheader(f"📷 {cam['name']}")
        
#         # Live feed display
#         live_placeholder = st.empty()
#         if st.session_state.get(f"stream_active_{camera_id}", False):
#             error = st.session_state.get(f"stream_error_{camera_id}")
#             frame = st.session_state.get(f"frame_{camera_id}")
            
#             if error:
#                 live_placeholder.error(error)
#                 # Attempt to reconnect
#                 if st.button("Retry Connection", key=f"retry_{camera_id}"):
#                     st.session_state[f"stream_error_{camera_id}"] = None
#                     start_stream(cam['address'], camera_id)
#             elif frame is not None:
#                 live_placeholder.image(frame, caption=f"Live Feed: {cam['name']}", use_column_width=True)
#             else:
#                 live_placeholder.info("Connecting to stream...")
        
#         # Operation Controls
#         st.subheader("Operations")
        
#         # Toggle buttons for each operation
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             fire_active = st.session_state.get(f"fire_active_{camera_id}", False)
#             if st.button("🔴 Stop Fire Detection" if fire_active else "🟢 Start Fire Detection", 
#                         key=f"fire_toggle_{camera_id}"):
#                 if fire_active:
#                     st.session_state[f"fire_active_{camera_id}"] = False
#                 else:
#                     threading.Thread(
#                         target=run_fire_detection, 
#                         args=(camera_id, cam['name']), 
#                         daemon=True
#                     ).start()
        
#         with col2:
#             occ_active = st.session_state.get(f"occ_active_{camera_id}", False)
#             if st.button("🔴 Stop Occupancy Detection" if occ_active else "🟢 Start Occupancy Detection", 
#                         key=f"occ_toggle_{camera_id}"):
#                 if occ_active:
#                     st.session_state[f"occ_active_{camera_id}"] = False
#                 else:
#                     threading.Thread(
#                         target=run_occupancy_detection, 
#                         args=(camera_id, cam['name']), 
#                         daemon=True
#                     ).start()
        
#         with col3:
#             no_access_active = st.session_state.get(f"no_access_active_{camera_id}", False)
#             if st.button("🔴 Stop No-Access Detection" if no_access_active else "🟢 Start No-Access Detection", 
#                         key=f"no_access_toggle_{camera_id}"):
#                 if no_access_active:
#                     st.session_state[f"no_access_active_{camera_id}"] = False
#                 else:
#                     threading.Thread(
#                         target=run_no_access_detection, 
#                         args=(camera_id, cam['name']), 
#                         daemon=True
#                     ).start()
        
#         # Status indicators
#         status_cols = st.columns(3)
#         with status_cols[0]:
#             st.write(f"Fire Detection: {'🟢 Running' if st.session_state.get(f'fire_active_{camera_id}', False) else '🔴 Stopped'}")
#         with status_cols[1]:
#             st.write(f"Occupancy Detection: {'🟢 Running' if st.session_state.get(f'occ_active_{camera_id}', False) else '🔴 Stopped'}")
#         with status_cols[2]:
#             st.write(f"No-Access Detection: {'🟢 Running' if st.session_state.get(f'no_access_active_{camera_id}', False) else '🔴 Stopped'}")
        
#         st.markdown("---")  # Separator between cameras



import streamlit as st
import logging
import threading
import time
import cv2
import numpy as np
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from bson import ObjectId
from fire_detection import fire_model, classnames
from occupancy_detection import occupancy_detection_loop
from no_access_rooms import no_access_detection_loop
import cvzone
from queue import Queue
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple, Callable
import concurrent.futures

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("vigil")

# Constants
MAX_QUEUE_SIZE = 5
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS_LIMIT = 30
FRAME_INTERVAL = 1.0 / FPS_LIMIT

# MongoDB configuration
MONGO_URI = "mongodb+srv://infernapeamber:g9kASflhhSQ26GMF@cluster0.mjoloub.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "vigil"
CAMERAS_COLLECTION = "cameras"

# Detection types
DETECTION_TYPES = ["fire", "occupancy", "no_access"]

@dataclass
class Camera:
    """Camera data model"""
    id: str
    name: str
    address: str
    active: bool = False
    error: Optional[str] = None
    
    def get_id(self) -> str:
        return self.id

class MongoDBManager:
    """MongoDB connection and operations manager"""
    
    def __init__(self, uri: str, db_name: str, collection_name: str):
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self.connected = False
    
    def connect(self) -> Tuple[bool, Optional[str]]:
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000
            )
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            self.connected = True
            return True, None
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            self.connected = False
            return False, str(e)
        except Exception as e:
            logger.error(f"Unexpected MongoDB error: {str(e)}")
            self.connected = False
            return False, str(e)
    
    def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self.connected = False
    
    def add_camera(self, name: str, address: str) -> Optional[Dict]:
        """Add a camera to the database"""
        if not self.connected:
            return None
        
        try:
            camera = {"name": name, "address": address}
            result = self.collection.insert_one(camera)
            camera['_id'] = result.inserted_id
            return camera
        except Exception as e:
            logger.error(f"Failed to add camera: {str(e)}")
            return None
    
    def get_all_cameras(self) -> List[Dict]:
        """Get all cameras from the database"""
        if not self.connected:
            return []
        
        try:
            return list(self.collection.find())
        except Exception as e:
            logger.error(f"Failed to retrieve cameras: {str(e)}")
            return []
    
    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera from the database"""
        if not self.connected:
            return False
        
        try:
            result = self.collection.delete_one({"_id": ObjectId(camera_id)})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to remove camera: {str(e)}")
            return False

class StreamManager:
    """Manages camera streams and processing"""
    
    def __init__(self):
        self.frame_queues: Dict[str, Queue] = {}
        self.result_queues: Dict[str, Dict[str, Queue]] = {}
        self.status: Dict[str, Dict[str, bool]] = {}
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self.futures: Dict[str, Dict[str, Any]] = {}
    
    def initialize_camera(self, camera: Camera):
        """Initialize streaming resources for a camera"""
        camera_id = camera.get_id()
        
        # Initialize frame queue
        if camera_id not in self.frame_queues:
            self.frame_queues[camera_id] = Queue(maxsize=MAX_QUEUE_SIZE)
        
        # Initialize result queues for each detection type
        if camera_id not in self.result_queues:
            self.result_queues[camera_id] = {
                det_type: Queue(maxsize=MAX_QUEUE_SIZE) for det_type in DETECTION_TYPES
            }
        
        # Initialize status flags
        if camera_id not in self.status:
            self.status[camera_id] = {
                "stream": False,
                "fire": False,
                "occupancy": False,
                "no_access": False
            }
        
        # Initialize futures dictionary
        if camera_id not in self.futures:
            self.futures[camera_id] = {}
    
    def start_stream(self, camera: Camera):
        """Start camera stream"""
        camera_id = camera.get_id()
        
        if self.status[camera_id]["stream"]:
            return
        
        self.status[camera_id]["stream"] = True
        self.futures[camera_id]["stream"] = self.executor.submit(
            self._stream_worker, camera
        )
    
    def stop_stream(self, camera_id: str):
        """Stop camera stream"""
        if not self.status.get(camera_id, {}).get("stream", False):
            return
        
        self.status[camera_id]["stream"] = False
        
        # Also stop all detection processes
        for det_type in DETECTION_TYPES:
            self.stop_detection(camera_id, det_type)
    
    def start_detection(self, camera: Camera, detection_type: str):
        """Start a detection process"""
        camera_id = camera.get_id()
        
        if not self.status[camera_id]["stream"]:
            logger.warning(f"Cannot start {detection_type} detection without active stream")
            return False
        
        if self.status[camera_id].get(detection_type, False):
            return True  # Already running
        
        detection_functions = {
            "fire": self._fire_detection_worker,
            "occupancy": self._occupancy_detection_worker,
            "no_access": self._no_access_detection_worker
        }
        
        if detection_type in detection_functions:
            self.status[camera_id][detection_type] = True
            self.futures[camera_id][detection_type] = self.executor.submit(
                detection_functions[detection_type], camera
            )
            return True
        return False
    
    def stop_detection(self, camera_id: str, detection_type: str):
        """Stop a detection process"""
        if not self.status.get(camera_id, {}).get(detection_type, False):
            return
        
        self.status[camera_id][detection_type] = False
    
    def get_latest_frame(self, camera_id: str) -> Optional[np.ndarray]:
        """Get the latest frame from a camera"""
        queue = self.frame_queues.get(camera_id)
        if not queue or queue.empty():
            return None
        
        # Get the most recent frame (without removing from queue)
        frames = []
        try:
            while not queue.empty():
                frames.append(queue.get_nowait())
            
            # Put frames back except the oldest ones if we took too many
            for frame in frames[:-1]:
                queue.put(frame)
            
            # Return the most recent frame
            return frames[-1] if frames else None
        except Exception as e:
            logger.error(f"Error getting latest frame: {str(e)}")
            # Put back any frames we took out
            for frame in frames:
                try:
                    queue.put(frame)
                except:
                    pass
            return None
    
    def get_detection_result(self, camera_id: str, detection_type: str) -> Optional[Dict]:
        """Get the latest detection result"""
        queue = self.result_queues.get(camera_id, {}).get(detection_type)
        if not queue or queue.empty():
            return None
        
        # Similar to get_latest_frame, but for results
        results = []
        try:
            while not queue.empty():
                results.append(queue.get_nowait())
            
            # Put results back except the oldest ones
            for result in results[:-1]:
                queue.put(result)
            
            # Return the most recent result
            return results[-1] if results else None
        except Exception as e:
            logger.error(f"Error getting latest detection result: {str(e)}")
            for result in results:
                try:
                    queue.put(result)
                except:
                    pass
            return None
    
    def is_active(self, camera_id: str, operation: str) -> bool:
        """Check if an operation is active for a camera"""
        return self.status.get(camera_id, {}).get(operation, False)
    
    def _stream_worker(self, camera: Camera):
        """Worker function for camera streaming"""
        camera_id = camera.get_id()
        camera_name = camera.name
        address = camera.address
        
        logger.info(f"Starting stream for camera {camera_name} ({address})")
        
        # Configure OpenCV capture with optimized parameters
        cap = cv2.VideoCapture(address)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FPS, FPS_LIMIT)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        
        if not cap.isOpened():
            logger.error(f"Failed to open stream for {camera_name}")
            camera.error = f"Failed to connect to stream at {address}"
            camera.active = False
            return
        
        camera.active = True
        camera.error = None
        
        frame_queue = self.frame_queues[camera_id]
        last_frame_time = time.time()
        
        try:
            while self.status[camera_id]["stream"]:
                # Throttle frame rate
                current_time = time.time()
                elapsed = current_time - last_frame_time
                if elapsed < FRAME_INTERVAL:
                    time.sleep(max(0, FRAME_INTERVAL - elapsed))
                
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Failed to capture frame for {camera_name}")
                    time.sleep(1)  # Wait before retrying
                    continue
                
                # Process the frame
                try:
                    frame = cv2.resize(frame, (FRAME_WIDTH, FRAME_HEIGHT))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Update the frame queue
                    if frame_queue.full():
                        frame_queue.get()  # Remove oldest frame
                    frame_queue.put(frame.copy())
                    
                    last_frame_time = time.time()
                    
                except Exception as e:
                    logger.error(f"Error processing frame for {camera_name}: {str(e)}")
        except Exception as e:
            logger.error(f"Stream worker error for {camera_name}: {str(e)}")
        finally:
            cap.release()
            logger.info(f"Stream stopped for {camera_name}")
            camera.active = False
    
    def _fire_detection_worker(self, camera: Camera):
        """Worker function for fire detection"""
        camera_id = camera.get_id()
        camera_name = camera.name
        
        logger.info(f"Starting fire detection for {camera_name}")
        
        frame_queue = self.frame_queues[camera_id]
        result_queue = self.result_queues[camera_id]["fire"]
        
        try:
            while self.status[camera_id]["stream"] and self.status[camera_id]["fire"]:
                # Get a frame to process
                if frame_queue.empty():
                    time.sleep(0.01)
                    continue
                
                frame = frame_queue.get()
                
                # Process the frame with fire detection
                processed_frame = frame.copy()
                fire_detected = False
                
                try:
                    result = fire_model(processed_frame, stream=True)
                    
                    for info in result:
                        boxes = info.boxes
                        for box in boxes:
                            confidence = int(box.conf[0] * 100)
                            class_id = int(box.cls[0])
                            
                            if confidence > 80:
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (0, 0, 255), 5)
                                cvzone.putTextRect(processed_frame, f'{classnames[class_id]} {confidence}%', 
                                                [x1 + 8, y1 + 100], scale=1.5, thickness=2)
                                fire_detected = True
                                cv2.putText(processed_frame, "ALERT!", (50, 150), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
                    # Update the result queue
                    if result_queue.full():
                        result_queue.get()  # Remove oldest result
                    
                    result_queue.put({
                        "frame": processed_frame,
                        "alert": fire_detected,
                        "timestamp": time.time()
                    })
                    
                except Exception as e:
                    logger.error(f"Fire detection processing error: {str(e)}")
                
                time.sleep(0.01)  # Small sleep to prevent CPU hogging
                
        except Exception as e:
            logger.error(f"Fire detection worker error for {camera_name}: {str(e)}")
        finally:
            logger.info(f"Fire detection stopped for {camera_name}")
            self.status[camera_id]["fire"] = False
    
    def _occupancy_detection_worker(self, camera: Camera):
        """Worker function for occupancy detection"""
        camera_id = camera.get_id()
        camera_name = camera.name
        
        logger.info(f"Starting occupancy detection for {camera_name}")
        
        frame_queue = self.frame_queues[camera_id]
        result_queue = self.result_queues[camera_id]["occupancy"]
        
        try:
            while self.status[camera_id]["stream"] and self.status[camera_id]["occupancy"]:
                # Get a frame to process
                if frame_queue.empty():
                    time.sleep(0.01)
                    continue
                
                frame = frame_queue.get()
                
                # Process the frame with occupancy detection
                try:
                    processed_frame, count = occupancy_detection_loop(frame.copy())
                    
                    # Update the result queue
                    if result_queue.full():
                        result_queue.get()  # Remove oldest result
                    
                    result_queue.put({
                        "frame": processed_frame,
                        "count": count,
                        "timestamp": time.time()
                    })
                    
                except Exception as e:
                    logger.error(f"Occupancy detection processing error: {str(e)}")
                
                time.sleep(0.01)  # Small sleep to prevent CPU hogging
                
        except Exception as e:
            logger.error(f"Occupancy detection worker error for {camera_name}: {str(e)}")
        finally:
            logger.info(f"Occupancy detection stopped for {camera_name}")
            self.status[camera_id]["occupancy"] = False
    
    def _no_access_detection_worker(self, camera: Camera):
        """Worker function for no-access detection"""
        camera_id = camera.get_id()
        camera_name = camera.name
        
        logger.info(f"Starting no-access detection for {camera_name}")
        
        frame_queue = self.frame_queues[camera_id]
        result_queue = self.result_queues[camera_id]["no_access"]
        
        try:
            while self.status[camera_id]["stream"] and self.status[camera_id]["no_access"]:
                # Get a frame to process
                if frame_queue.empty():
                    time.sleep(0.01)
                    continue
                
                frame = frame_queue.get()
                
                # Process the frame with no-access detection
                try:
                    processed_frame, alert = no_access_detection_loop(frame.copy())
                    
                    # Update the result queue
                    if result_queue.full():
                        result_queue.get()  # Remove oldest result
                    
                    result_queue.put({
                        "frame": processed_frame,
                        "alert": alert,
                        "timestamp": time.time()
                    })
                    
                except Exception as e:
                    logger.error(f"No-access detection processing error: {str(e)}")
                
                time.sleep(0.01)  # Small sleep to prevent CPU hogging
                
        except Exception as e:
            logger.error(f"No-access detection worker error for {camera_name}: {str(e)}")
        finally:
            logger.info(f"No-access detection stopped for {camera_name}")
            self.status[camera_id]["no_access"] = False
    
    def cleanup(self):
        """Cleanup resources"""
        # Stop all streams and detection processes
        for camera_id in list(self.status.keys()):
            self.stop_stream(camera_id)
        
        # Shutdown thread pool
        self.executor.shutdown(wait=False)

class VigilApp:
    """Main application class"""
    
    def __init__(self):
        self.db_manager = MongoDBManager(MONGO_URI, DB_NAME, CAMERAS_COLLECTION)
        self.stream_manager = StreamManager()
        self.cameras = {}
        
        # Initialize session state if needed
        if 'app_initialized' not in st.session_state:
            st.session_state.app_initialized = True
            st.session_state.confirm_remove = None
            st.session_state.selected_tab = "all"
    
    def initialize(self):
        """Initialize the application"""
        # Connect to database
        success, error_msg = self.db_manager.connect()
        if not success:
            self._show_db_error(error_msg)
            return False
        
        # Load cameras from database
        self._load_cameras()
        return True
    
    def _load_cameras(self):
        """Load cameras from database and initialize streams"""
        db_cameras = self.db_manager.get_all_cameras()
        
        for cam_data in db_cameras:
            camera_id = str(cam_data['_id'])
            camera = Camera(
                id=camera_id,
                name=cam_data['name'],
                address=cam_data['address']
            )
            self.cameras[camera_id] = camera
            
            # Initialize streaming resources
            self.stream_manager.initialize_camera(camera)
            
            # Start stream if not already started
            if not self.stream_manager.is_active(camera_id, "stream"):
                self.stream_manager.start_stream(camera)
    
    def _show_db_error(self, error_msg):
        """Display database connection error"""
        st.error("Failed to connect to MongoDB Atlas")
        st.write(f"Error: {error_msg}")
        st.write("**Troubleshooting Steps**:")
        st.write("1. Verify MongoDB Atlas credentials")
        st.write("2. Set Network Access to allow connections from your IP in MongoDB Atlas")
        st.write("3. Ensure pymongo>=4.8.0 is in requirements.txt")
        st.write("4. Check cluster status (not paused) in MongoDB Atlas")
    
    def render_header(self):
        """Render application header"""
        st.title("📷 V.I.G.I.L - Video Intelligence for General Identification and Logging")
        st.write("Intelligent CCTV monitoring system with real-time analytics")
    
    def render_camera_management(self):
        """Render camera management section"""
        st.header("📹 Camera Management")
        
        # Add camera form
        with st.expander("➕ Add New Camera", expanded=True):
            with st.form("add_camera_form"):
                name = st.text_input("Camera Name", help="A unique identifier for the camera")
                address = st.text_input("Camera Address", help="RTSP or HTTP stream URL (e.g., rtsp://your-camera-ip:554/stream)")
                submitted = st.form_submit_button("Add Camera")
                if submitted:
                    self._handle_add_camera(name, address)
        
        # Camera list
        st.header("📋 Camera List")
        if not self.cameras:
            st.info("No cameras have been added yet. Add your first camera above.")
        else:
            st.write("**Added Cameras**:")
            for i, (camera_id, camera) in enumerate(self.cameras.items()):
                col1, col2, col3 = st.columns([2, 4, 1])
                with col1:
                    st.markdown(f"**{camera.name}**")
                with col2:
                    st.code(camera.address, language="text")
                with col3:
                    if st.button("Remove", key=f"remove_{i}"):
                        st.session_state.confirm_remove = camera_id
        
        # Handle camera removal confirmation
        if st.session_state.confirm_remove:
            self._handle_remove_camera_confirmation()
    
    def _handle_add_camera(self, name, address):
        """Handle adding a new camera"""
        if not name or not address:
            st.error("Both camera name and address are required.")
            return
        
        # Validate camera name uniqueness
        if any(cam.name == name for cam in self.cameras.values()):
            st.error("Camera name must be unique.")
            return
        
        # Validate URL format
        if not (address.startswith("rtsp://") or address.startswith("http://") or address.startswith("https://")):
            st.error("Invalid URL format. Use rtsp:// or http(s)://")
            return
        
        # Add to database
        camera_data = self.db_manager.add_camera(name, address)
        if not camera_data:
            st.error("Failed to add camera to database.")
            return
        
        # Create camera object
        camera_id = str(camera_data['_id'])
        camera = Camera(
            id=camera_id,
            name=name,
            address=address
        )
        self.cameras[camera_id] = camera
        
        # Initialize streaming resources
        self.stream_manager.initialize_camera(camera)
        
        # Start stream
        self.stream_manager.start_stream(camera)
        
        st.success(f"Added camera: {name}")
        st.rerun()
    
    def _handle_remove_camera_confirmation(self):
        """Handle camera removal confirmation"""
        camera_id = st.session_state.confirm_remove
        if camera_id in self.cameras:
            camera = self.cameras[camera_id]
            
            st.warning(f"Confirm removal of camera: {camera.name}")
            st.write(f"Address: {camera.address}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Confirm Removal"):
                    # Stop stream
                    self.stream_manager.stop_stream(camera_id)
                    
                    # Remove from database
                    self.db_manager.remove_camera(camera_id)
                    
                    # Remove from local cache
                    del self.cameras[camera_id]
                    
                    st.session_state.confirm_remove = None
                    st.success(f"Removed camera: {camera.name}")
                    st.rerun()
            with col2:
                if st.button("Cancel"):
                    st.session_state.confirm_remove = None
                    st.rerun()
    
    def render_camera_tabs(self):
        """Render tabs for camera selection"""
        st.header("📹 Live Footage and Operations")
        
        if not self.cameras:
            st.info("No cameras available. Add cameras to view footage.")
            return
        
        # Create tabs for camera selection
        tabs = ["All Cameras"] + [cam.name for cam in self.cameras.values()]
        tab_keys = ["all"] + [cam.id for cam in self.cameras.values()]
        
        # Use streamlit columns as tabs
        cols = st.columns(len(tabs))
        for i, (tab, key) in enumerate(zip(tabs, tab_keys)):
            with cols[i]:
                if st.button(tab, key=f"tab_{key}", use_container_width=True, 
                           type="primary" if st.session_state.selected_tab == key else "secondary"):
                    st.session_state.selected_tab = key
                    st.rerun()
    
    def render_camera_views(self):
        """Render camera views based on selected tab"""
        selected_tab = st.session_state.selected_tab
        
        if selected_tab == "all":
            # Show all cameras
            for camera_id, camera in self.cameras.items():
                self._render_camera_view(camera)
        elif selected_tab in self.cameras:
            # Show only selected camera
            self._render_camera_view(self.cameras[selected_tab])
    
    def _render_camera_view(self, camera):
        """Render a single camera view with controls"""
        camera_id = camera.id
        
        st.subheader(f"📷 {camera.name}")
        
        # Camera status
        is_active = self.stream_manager.is_active(camera_id, "stream")
        status_color = "🟢" if is_active else "🔴"
        st.write(f"Status: {status_color} {'Online' if is_active else 'Offline'}")
        
        if camera.error:
            st.error(camera.error)
            if st.button("Retry Connection", key=f"retry_{camera_id}"):
                self.stream_manager.stop_stream(camera_id)
                time.sleep(1)
                self.stream_manager.start_stream(camera)
        
        # Camera view with detection options
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Display the camera feed
            display_placeholder = st.empty()
            
            # Get the latest frame
            frame = self.stream_manager.get_latest_frame(camera_id)
            
            if frame is not None:
                display_placeholder.image(frame, caption=f"Live Feed: {camera.name}", use_column_width=True)
            else:
                display_placeholder.info("Waiting for video stream...")
        
        with col2:
            # Detection controls
            st.write("**Video Analytics**")
            
            # Fire detection
            fire_active = self.stream_manager.is_active(camera_id, "fire")
            if st.button("🔴 Stop Fire Detection" if fire_active else "🟢 Start Fire Detection", 
                       key=f"fire_{camera_id}"):
                if fire_active:
                    self.stream_manager.stop_detection(camera_id, "fire")
                else:
                    self.stream_manager.start_detection(camera, "fire")
            
            # Occupancy detection
            occ_active = self.stream_manager.is_active(camera_id, "occupancy")
            if st.button("🔴 Stop Occupancy" if occ_active else "🟢 Start Occupancy", 
                       key=f"occ_{camera_id}"):
                if occ_active:
                    self.stream_manager.stop_detection(camera_id, "occupancy")
                else:
                    self.stream_manager.start_detection(camera, "occupancy")
            
            # No-access detection
            no_access_active = self.stream_manager.is_active(camera_id, "no_access")
            if st.button("🔴 Stop No-Access" if no_access_active else "🟢 Start No-Access", 
                       key=f"no_access_{camera_id}"):
                if no_access_active:
                    self.stream_manager.stop_detection(camera_id, "no_access")
                else:
                    self.stream_manager.start_detection(camera, "no_access")
            
            # Status indicators
            st.write("**Detection Status:**")
            for det_type, label in [
                ("fire", "Fire Detection"), 
                ("occupancy", "Occupancy"), 
                ("no_access", "No-Access")
            ]:
                is_active = self.stream_manager.is_active(camera_id, det_type)
                status = f"{'🟢 Running' if is_active else '🔴 Stopped'}"
                st.write(f"{label}: {status}")
        
        # Detection results section
        if any(self.stream_manager.is_active(camera_id, det_type) for det_type in DETECTION_TYPES):
            st.write("**Detection Results**")
            
            det_cols = st.columns(len(DETECTION_TYPES))
            
            # Fire detection results
            if self.stream_manager.is_active(camera_id, "fire"):
                with det_cols[0]:
                    st.write("**Fire Detection**")
                    result = self.stream_manager.get_detection_result(camera_id, "fire")
                    if result:
                        if result.get("alert"):
                            st.error("🔥 FIRE DETECTED! 🔥")
                        else:
                            st.success("No fire detected")
                        st.image(result["frame"], caption="Fire Detection", use_column_width=True)
            
            # Occupancy detection results
            if self.stream_manager.is_active(camera_id, "occupancy"):
                with det_cols[1]:
                    st.write("**Occupancy Detection**")
                    result = self.stream_manager.get_detection_result(camera_id, "occupancy")
                    if result:
                        st.info(f"People count: {result.get('count', 0)}")
                        st.image(result["frame"], caption="Occupancy Detection", use_column_width=True)
            
            # No-access detection results
            if self.stream_manager.is_active(camera_id, "no_access"):
                with det_cols[2]:
                    st.write("**No-Access Detection**")
                    result = self.stream_manager.get_detection_result(camera_id, "no_access")
                    if result:
                        if result.get("alert"):
                            st.error("⚠️ UNAUTHORIZED ACCESS! ⚠️")
                        else:
                            st.success("No unauthorized access")
                        st.image(result["frame"], caption="No-Access Detection", use_column_width=True)
        
        st.markdown("---")  # Separator

    def render_dashboard(self):
        """Render analytics dashboard"""
        if st.session_state.selected_tab == "all" and self.cameras:
            st.header("📊 Analytics Dashboard")
            
            # Summary metrics
            total_cameras = len(self.cameras)
            active_cameras = sum(1 for cam_id in self.cameras if self.stream_manager.is_active(cam_id, "stream"))
            total_alerts = sum(
                1 for cam_id in self.cameras 
                for det_type in ["fire", "no_access"] 
                if self._has_alert(cam_id, det_type)
            )
            total_occupancy = sum(
                self._get_occupancy_count(cam_id) 
                for cam_id in self.cameras
            )
            
            # Display metrics
            cols = st.columns(4)
            with cols[0]:
                st.metric("Total Cameras", total_cameras)
            with cols[1]:
                st.metric("Active Cameras", active_cameras)
            with cols[2]:
                st.metric("Total Alerts", total_alerts)
            with cols[3]:
                st.metric("Total Occupancy", total_occupancy)
            
            # Alert summary
            if total_alerts > 0:
                st.subheader("⚠️ Active Alerts")
                for camera_id, camera in self.cameras.items():
                    for det_type, alert_type in [("fire", "Fire"), ("no_access", "Unauthorized Access")]:
                        if self._has_alert(camera_id, det_type):
                            st.error(f"{alert_type} detected on {camera.name}")
    
    def _has_alert(self, camera_id, detection_type):
        """Check if a camera has an active alert"""
        result = self.stream_manager.get_detection_result(camera_id, detection_type)
        return result and result.get("alert", False)
    
    def _get_occupancy_count(self, camera_id):
        """Get occupancy count for a camera"""
        result = self.stream_manager.get_detection_result(camera_id, "occupancy")
        return result.get("count", 0) if result else 0
    
    def run(self):
        """Run the application"""
        self.render_header()
        
        if not self.initialize():
            return
        
        self.render_camera_management()
        self.render_camera_tabs()
        self.render_camera_views()
        self.render_dashboard()

def main():
    # Set page config
    st.set_page_config(
        page_title="V.I.G.I.L - Video Intelligence System",
        page_icon="📹",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Run the app
    app = VigilApp()
    app.run()

if __name__ == "__main__":
    main()
