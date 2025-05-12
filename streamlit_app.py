import streamlit as st
import requests
from PIL import Image
import io
import time
from datetime import datetime, timedelta, date
import base64
import json
import os
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import threading
from collections import defaultdict
import uuid

# Function to load cameras from JSON file
def load_cameras():
    try:
        if os.path.exists('cameras.json'):
            with open('cameras.json', 'r') as file:
                cameras = json.load(file)
                # Initialize runtime fields for each camera
                for camera in cameras:
                    if 'last_frame' not in camera:
                        camera['last_frame'] = None
                    if 'status' not in camera:
                        camera['status'] = "Connecting..."
                    if 'detection_active' not in camera:
                        camera['detection_active'] = False
                    if 'camera_id' not in camera:
                        camera['camera_id'] = str(uuid.uuid4())
                return cameras
        else:
            return []
    except Exception as e:
        st.error(f"Error loading cameras: {str(e)}")
        return []

# Function to save cameras to JSON file
def save_cameras(cameras):
    try:
        # Create a copy without runtime data
        cameras_to_save = []
        for camera in cameras:
            cameras_to_save.append({
                'name': camera['name'],
                'url': camera['url'],
                'camera_id': camera.get('camera_id', str(uuid.uuid4())),
                'detection_active': camera.get('detection_active', False)
            })
        
        with open('cameras.json', 'w') as file:
            json.dump(cameras_to_save, file, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving cameras: {str(e)}")
        return False

# Function to load occupancy history
def load_occupancy_history():
    try:
        if os.path.exists('occupancy_history.json'):
            with open('occupancy_history.json', 'r') as file:
                history = json.load(file)
                return history
        else:
            return {}
    except Exception as e:
        st.error(f"Error loading occupancy history: {str(e)}")
        return {}

# Function to save occupancy data
def save_occupancy_data(camera_id, timestamp, count):
    try:
        # Load existing data
        history = load_occupancy_history()
        
        # Initialize camera entry if it doesn't exist
        if camera_id not in history:
            history[camera_id] = []
        
        # Add new entry
        history[camera_id].append({
            'timestamp': timestamp,
            'count': count
        })
        
        # Save updated data
        with open('occupancy_history.json', 'w') as file:
            json.dump(history, file, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving occupancy data: {str(e)}")
        return False

# Function to get a single frame from MJPEG stream
def get_mjpeg_frame(url, timeout=5):
    try:
        # Make request with short timeout
        response = requests.get(url, stream=True, timeout=timeout)
        
        if response.status_code == 200:
            # Read bytes
            bytes_data = bytes()
            for chunk in response.iter_content(chunk_size=1024):
                bytes_data += chunk
                
                # Find JPEG frame boundaries
                a = bytes_data.find(b'\xff\xd8')  # JPEG start
                b = bytes_data.find(b'\xff\xd9')  # JPEG end
                
                if a != -1 and b != -1:
                    # Extract the JPEG frame
                    jpg = bytes_data[a:b+2]
                    return jpg, None
                
                # Prevent too much data accumulation
                if len(bytes_data) > 500000:  # ~500KB
                    break
                    
            return None, "Could not find complete JPEG frame"
        else:
            return None, f"HTTP error: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return None, f"Connection error: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"

# Human detection using OpenCV HOG detector
def detect_humans(image_bytes):
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Initialize HOG detector
        hog = cv2.HOGDescriptor()
        hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        
        # Detect people
        boxes, weights = hog.detectMultiScale(img, winStride=(8,8))
        
        # Count people
        person_count = len(boxes)
        
        # Draw bounding boxes if people detected
        if person_count > 0:
            for (x, y, w, h) in boxes:
                cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Add count text
            cv2.putText(img, f'People: {person_count}', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Convert back to JPEG
        _, buffer = cv2.imencode('.jpg', img)
        jpg_bytes = buffer.tobytes()
        
        return person_count, jpg_bytes
    except Exception as e:
        st.error(f"Detection error: {str(e)}")
        return 0, image_bytes

# Function to create hourly occupancy line graph for a specific date
def create_hourly_graph(camera_id, selected_date=None):
    try:
        # Load occupancy data
        history = load_occupancy_history()
        
        if camera_id not in history or not history[camera_id]:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(history[camera_id])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter by date if specified
        if selected_date:
            df = df[df['timestamp'].dt.date == selected_date]
            if df.empty:
                return None
        else:
            # Last 24 hours only if no date specified
            last_24h = datetime.now() - timedelta(hours=24)
            df = df[df['timestamp'] >= last_24h]
        
        # Group by hour and get maximum count
        df['hour'] = df['timestamp'].dt.floor('H')
        hourly_max = df.groupby('hour')['count'].max().reset_index()
        
        # Create graph
        title = f"Hourly Maximum Occupancy - {selected_date.strftime('%Y-%m-%d')}" if selected_date else "Hourly Maximum Occupancy (Last 24 Hours)"
        
        fig = px.line(
            hourly_max, 
            x='hour', 
            y='count',
            title=title,
            labels={'hour': 'Hour of Day', 'count': 'Maximum People Count'}
        )
        
        # Customize layout
        fig.update_layout(
            xaxis=dict(
                title='Hour of Day',
                gridcolor='lightgray',
                showgrid=True
            ),
            yaxis=dict(
                title='Maximum People Count',
                gridcolor='lightgray',
                showgrid=True
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(size=12),
            margin=dict(l=40, r=40, t=50, b=40),
            hovermode='x unified'
        )
        
        # Set line color to blue
        fig.update_traces(line=dict(color='blue', width=2))
        
        return fig
    except Exception as e:
        st.error(f"Error creating hourly graph: {str(e)}")
        return None

# Function to create circular occupancy graph (24-hour clock) for a specific date
def create_circular_graph(camera_id, selected_date=None):
    try:
        # Load occupancy data
        history = load_occupancy_history()
        
        if camera_id not in history or not history[camera_id]:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(history[camera_id])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter by date if specified
        if selected_date:
            df = df[df['timestamp'].dt.date == selected_date]
            if df.empty:
                return None
        else:
            # Last 24 hours only if no date specified
            last_24h = datetime.now() - timedelta(hours=24)
            df = df[df['timestamp'] >= last_24h]
        
        if df.empty:
            return None
        
        # Create binary occupancy (0 or 1)
        df['occupied'] = df['count'].apply(lambda x: 1 if x > 0 else 0)
        
        # Extract hours and minutes for polar coordinates
        df['hour'] = df['timestamp'].dt.hour
        df['minute'] = df['timestamp'].dt.minute
        
        # Convert to angle (0 to 2π)
        df['angle'] = 2 * np.pi * (df['hour'] + df['minute']/60) / 24
        
        # Convert to cartesian coordinates
        df['x'] = np.cos(df['angle'])
        df['y'] = np.sin(df['angle'])
        
        # Create scatter plot with polar coordinates
        fig = go.Figure()
        
        # Add minute markers (thin lines from center)
        for _, row in df.iterrows():
            if row['occupied'] == 1:
                color = 'orange'  # Use orange color for occupied points
            else:
                continue  # Skip unoccupied points
            
            fig.add_trace(go.Scatter(
                x=[0, row['x']], 
                y=[0, row['y']],
                mode='lines',
                line=dict(color=color, width=1),
                hoverinfo='none',
                showlegend=False
            ))
        
        # Add circle for reference
        theta = np.linspace(0, 2*np.pi, 100)
        fig.add_trace(go.Scatter(
            x=np.cos(theta),
            y=np.sin(theta),
            mode='lines',
            line=dict(color='black', width=2),
            hoverinfo='none',
            showlegend=False
        ))
        
        # Add hour markers
        for hour in range(24):
            angle = 2 * np.pi * hour / 24
            x = 1.1 * np.cos(angle)
            y = 1.1 * np.sin(angle)
            
            # Add hour label
            fig.add_annotation(
                x=x, y=y,
                text=f"{hour}:00",
                showarrow=False,
                font=dict(size=10)
            )
            
            # Add tick mark
            x1, y1 = np.cos(angle), np.sin(angle)
            x2, y2 = 1.05 * np.cos(angle), 1.05 * np.sin(angle)
            fig.add_shape(
                type="line",
                x0=x1, y0=y1,
                x1=x2, y1=y2,
                line=dict(color="black", width=1),
            )
        
        # Add title
        title = f"Minute-by-Minute Presence - {selected_date.strftime('%Y-%m-%d')}" if selected_date else "Minute-by-Minute Presence (Last 24 Hours)"
        
        # Update layout
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-1.2, 1.2]
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                range=[-1.2, 1.2],
                scaleanchor="x",
                scaleratio=1
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=20, r=20, t=50, b=20),
            width=500,
            height=500,
            showlegend=False
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating circular graph: {str(e)}")
        return None

# Get available dates for a camera
def get_available_dates(camera_id):
    try:
        history = load_occupancy_history()
        if camera_id not in history or not history[camera_id]:
            return []
        
        df = pd.DataFrame(history[camera_id])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        return sorted(df['date'].unique())
    except Exception as e:
        st.error(f"Error getting available dates: {str(e)}")
        return []

# Initialize session state
if 'initialized' not in st.session_state:
    # Load cameras from JSON file
    st.session_state.cameras = load_cameras()
    st.session_state.last_refresh = datetime.now()
    st.session_state.initialized = True
    st.session_state.save_success = None
    st.session_state.active_history_camera = None
    st.session_state.selected_date = None

# App title
st.title("IP Camera Viewer with Occupancy Detection")

# Camera addition form
st.subheader("Add Camera")
with st.form("add_camera_form"):
    col1, col2 = st.columns(2)
    with col1:
        camera_name = st.text_input("Camera Name")
    with col2:
        camera_url = st.text_input("Camera URL")
    
    submit_button = st.form_submit_button("Add Camera")
    
    if submit_button and camera_name and camera_url:
        # Check if camera with same name already exists
        exists = False
        for cam in st.session_state.cameras:
            if cam["name"] == camera_name:
                exists = True
                break
                
        if not exists:
            new_camera = {
                "name": camera_name,
                "url": camera_url,
                "last_frame": None,
                "status": "Connecting...",
                "detection_active": False,
                "camera_id": str(uuid.uuid4())
            }
            st.session_state.cameras.append(new_camera)
            # Save to JSON file
            save_success = save_cameras(st.session_state.cameras)
            if save_success:
                st.session_state.save_success = "Camera added and saved successfully!"
            else:
                st.session_state.save_success = "Camera added but failed to save to file."
            st.experimental_rerun()
        else:
            st.error(f"Camera with name '{camera_name}' already exists!")

# Display save status if available
if st.session_state.save_success:
    st.success(st.session_state.save_success)
    st.session_state.save_success = None

# Camera table display
if st.session_state.cameras:
    st.subheader("Camera List")
    
    # Create header row for our custom table
    header_cols = st.columns([2, 4, 1])
    with header_cols[0]:
        st.markdown("**Camera Name**")
    with header_cols[1]:
        st.markdown("**Camera URL**")
    with header_cols[2]:
        st.markdown("**Action**")
    
    st.markdown("---")  # Divider
    
    # Create rows for each camera
    for i, camera in enumerate(st.session_state.cameras):
        cols = st.columns([2, 4, 1])
        with cols[0]:
            st.write(camera["name"])
        with cols[1]:
            st.write(camera["url"])
        with cols[2]:
            # Unique key for each button to avoid conflicts
            if st.button("Remove", key=f"remove_btn_{i}"):
                st.session_state.cameras.pop(i)
                # Save changes to JSON file
                save_success = save_cameras(st.session_state.cameras)
                if save_success:
                    st.session_state.save_success = "Camera removed and changes saved successfully!"
                else:
                    st.session_state.save_success = "Camera removed but failed to save changes."
                st.experimental_rerun()

# Refresh control
refresh_rate = 3  # Fixed at 3 seconds

col1, col2 = st.columns(2)
with col1:
    if st.button("Refresh All Cameras Now"):
        st.session_state.last_refresh = datetime.now()
        # We'll update frames but no rerun

with col2:
    # Show last refresh time
    st.write(f"Last updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

# Check if enough time has passed for refresh
current_time = datetime.now()
time_diff = (current_time - st.session_state.last_refresh).total_seconds()

# Update frames if refresh is due
if time_diff >= refresh_rate:
    # Update the last refresh time
    st.session_state.last_refresh = current_time
    
    # Update all camera frames
    for i, camera in enumerate(st.session_state.cameras):
        frame_data, error = get_mjpeg_frame(camera['url'])
        if frame_data:
            # If detection is active, process the frame
            if camera.get('detection_active', False):
                count, processed_frame = detect_humans(frame_data)
                st.session_state.cameras[i]["last_frame"] = processed_frame
                st.session_state.cameras[i]["person_count"] = count
                
                # Save occupancy data
                timestamp = datetime.now().isoformat()
                save_occupancy_data(camera['camera_id'], timestamp, count)
            else:
                st.session_state.cameras[i]["last_frame"] = frame_data
                
            st.session_state.cameras[i]["status"] = "Connected"
        else:
            st.session_state.cameras[i]["status"] = f"Error: {error}"

# Display cameras - two per row
if st.session_state.cameras:
    st.subheader("Camera Feeds")
    
    # Calculate number of rows needed
    num_cameras = len(st.session_state.cameras)
    num_rows = (num_cameras + 1) // 2  # Round up division
    
    for row in range(num_rows):
        cols = st.columns(2)
        
        # First camera in row
        idx = row * 2
        if idx < num_cameras:
            with cols[0]:
                camera = st.session_state.cameras[idx]
                
                # Camera title with view history button
                title_col1, title_col2 = st.columns([3, 1])
                with title_col1:
                    st.markdown(f"### {camera['name']}")
                with title_col2:
                    if st.button("View History", key=f"history_{idx}"):
                        st.session_state.active_history_camera = camera['camera_id']
                        st.session_state.selected_date = None  # Reset date selection
                        st.experimental_rerun()
                
                status = st.empty()
                frame_place = st.empty()
                
                # Show status
                if camera["status"] == "Connected":
                    status.success("Connected")
                else:
                    status.warning(camera["status"])
                
                # Display frame if available
                if camera["last_frame"] is None:
                    # Try to get first frame
                    frame_data, error = get_mjpeg_frame(camera['url'])
                    if frame_data:
                        st.session_state.cameras[idx]["last_frame"] = frame_data
                        st.session_state.cameras[idx]["status"] = "Connected"
                        image = Image.open(io.BytesIO(frame_data))
                        frame_place.image(image, use_column_width=True)
                        status.success("Connected")
                    else:
                        status.error(f"Failed to get frame: {error}")
                else:
                    # Display the cached frame
                    try:
                        image = Image.open(io.BytesIO(camera["last_frame"]))
                        frame_place.image(image, use_column_width=True)
                    except Exception as e:
                        status.error(f"Error displaying image: {str(e)}")
                
                # Occupancy detection toggle
                detection_active = camera.get('detection_active', False)
                if st.button(
                    "Stop Occupancy Detection" if detection_active else "Start Occupancy Detection", 
                    key=f"detect_btn_{idx}"
                ):
                    # Toggle detection state
                    st.session_state.cameras[idx]['detection_active'] = not detection_active
                    # Save changes to JSON file
                    save_cameras(st.session_state.cameras)
                    st.experimental_rerun()
        
        # Second camera in row
        idx = row * 2 + 1
        if idx < num_cameras:
            with cols[1]:
                camera = st.session_state.cameras[idx]
                
                # Camera title with view history button
                title_col1, title_col2 = st.columns([3, 1])
                with title_col1:
                    st.markdown(f"### {camera['name']}")
                with title_col2:
                    if st.button("View History", key=f"history_{idx}"):
                        st.session_state.active_history_camera = camera['camera_id']
                        st.session_state.selected_date = None  # Reset date selection
                        st.experimental_rerun()
                
                status = st.empty()
                frame_place = st.empty()
                
                # Show status
                if camera["status"] == "Connected":
                    status.success("Connected")
                else:
                    status.warning(camera["status"])
                
                # Display frame if available
                if camera["last_frame"] is None:
                    # Try to get first frame
                    frame_data, error = get_mjpeg_frame(camera['url'])
                    if frame_data:
                        st.session_state.cameras[idx]["last_frame"] = frame_data
                        st.session_state.cameras[idx]["status"] = "Connected"
                        image = Image.open(io.BytesIO(frame_data))
                        frame_place.image(image, use_column_width=True)
                        status.success("Connected")
                    else:
                        status.error(f"Failed to get frame: {error}")
                else:
                    # Display the cached frame
                    try:
                        image = Image.open(io.BytesIO(camera["last_frame"]))
                        frame_place.image(image, use_column_width=True)
                    except Exception as e:
                        status.error(f"Error displaying image: {str(e)}")
                
                # Occupancy detection toggle
                detection_active = camera.get('detection_active', False)
                if st.button(
                    "Stop Occupancy Detection" if detection_active else "Start Occupancy Detection", 
                    key=f"detect_btn_{idx}"
                ):
                    # Toggle detection state
                    st.session_state.cameras[idx]['detection_active'] = not detection_active
                    # Save changes to JSON file
                    save_cameras(st.session_state.cameras)
                    st.experimental_rerun()
else:
    st.info("No cameras added yet. Please add a camera using the form above.")

# Display history graphs if a camera is selected
if st.session_state.active_history_camera:
    # Find the camera name for the selected camera ID
    camera_name = "Unknown Camera"
    for cam in st.session_state.cameras:
        if cam.get('camera_id') == st.session_state.active_history_camera:
            camera_name = cam['name']
            break
    
    st.markdown("---")
    st.subheader(f"Occupancy History for {camera_name}")
    
    # Add date selector
    available_dates = get_available_dates(st.session_state.active_history_camera)
    date_options = ["Last 24 Hours"] + [d.strftime("%Y-%m-%d") for d in available_dates]
    
    date_col1, date_col2, date_col3 = st.columns([2, 1, 1])
    
    with date_col1:
        selected_date_str = st.selectbox("Select Date", date_options, index=0)
        
        if selected_date_str == "Last 24 Hours":
            st.session_state.selected_date = None
        else:
            st.session_state.selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    
    with date_col3:
        if st.button("Close History View"):
            st.session_state.active_history_camera = None
            st.experimental_rerun()
    
    # Create graphs
    col1, col2 = st.columns(2)
    
    with col1:
        circular_fig = create_circular_graph(st.session_state.active_history_camera, st.session_state.selected_date)
        if circular_fig:
            st.plotly_chart(circular_fig, use_container_width=True)
        else:
            st.info("No occupancy data available for this camera on the selected date.")
    
    with col2:
        hourly_fig = create_hourly_graph(st.session_state.active_history_camera, st.session_state.selected_date)
        if hourly_fig:
            st.plotly_chart(hourly_fig, use_container_width=True)
        else:
            st.info("No occupancy data available for this camera on the selected date.")

# Add note about persistence
st.markdown("---")
st.caption("Camera settings are saved in 'cameras.json' and occupancy data in 'occupancy_history.json'.")

# Update every few seconds but avoid complete page rerun
time.sleep(1)  # Short sleep to prevent hogging resources
