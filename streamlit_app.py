# import streamlit as st
# import requests
# import cv2
# import numpy as np
# from PIL import Image
# import io
# import time

# def main():
#     st.title("IP Camera Live Feed")
    
#     # Camera URL
#     camera_url = "http://218.219.214.248:50000/nphMotionJpeg?Resolution=640x480"
    
#     # Add a connection status indicator
#     status_placeholder = st.empty()
    
#     # Create a placeholder for the video frame
#     frame_placeholder = st.empty()
    
#     # Add a button to stop the stream
#     stop_button = st.button("Stop Stream")
    
#     try:
#         # Open the URL stream
#         stream = requests.get(camera_url, stream=True, timeout=10)
        
#         if stream.status_code == 200:
#             status_placeholder.success("Connected to camera stream")
            
#             # Read the stream as long as the stop button is not pressed
#             bytes_data = bytes()
            
#             while not stop_button:
#                 # Read stream bytes
#                 for chunk in stream.iter_content(chunk_size=1024):
#                     bytes_data += chunk
                    
#                     # Find the JPEG frame boundaries
#                     a = bytes_data.find(b'\xff\xd8')  # JPEG start
#                     b = bytes_data.find(b'\xff\xd9')  # JPEG end
                    
#                     if a != -1 and b != -1:
#                         # Extract the JPEG frame
#                         jpg = bytes_data[a:b+2]
#                         bytes_data = bytes_data[b+2:]
                        
#                         # Convert to image
#                         try:
#                             image = Image.open(io.BytesIO(jpg))
                            
#                             # Display the image
#                             frame_placeholder.image(image, caption="Live Feed", use_column_width=True)
#                         except Exception as e:
#                             st.error(f"Error processing frame: {e}")
                            
#                         # Check stop button again
#                         if stop_button:
#                             break
                        
#                         # Brief pause to not overload the system
#                         time.sleep(0.01)
                
#                 # If we've reached here, check the stop button
#                 if stop_button:
#                     break
#         else:
#             status_placeholder.error(f"Failed to connect to camera. Status code: {stream.status_code}")
            
#     except requests.exceptions.RequestException as e:
#         status_placeholder.error(f"Connection error: {e}")
#     except Exception as e:
#         status_placeholder.error(f"An error occurred: {e}")
        
#     # Display message when stream is stopped
#     if stop_button:
#         status_placeholder.info("Stream stopped")

# if __name__ == "__main__":
#     main()


import streamlit as st
import requests
from PIL import Image
import io
import time
from datetime import datetime

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

# Initialize session state for camera info
if 'cameras' not in st.session_state:
    st.session_state.cameras = [{
        "name": "Default Camera", 
        "url": "http://218.219.214.248:50000/nphMotionJpeg?Resolution=640x480"
    }]

# App title
st.title("IP Camera Viewer")

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
        new_camera = {
            "name": camera_name,
            "url": camera_url
        }
        st.session_state.cameras.append(new_camera)
        st.experimental_rerun()

# Display refresh rate slider
refresh_rate = st.slider("Refresh Rate (seconds)", min_value=1, max_value=10, value=3)
st.write(f"Frames will refresh every {refresh_rate} seconds")

# Auto-refresh mechanism
if st.button("Start Auto-refresh") or ('auto_refresh' in st.session_state and st.session_state.auto_refresh):
    st.session_state.auto_refresh = True
    st.write("Auto-refresh is ON. Click 'Stop Auto-refresh' to disable.")
    # Add current timestamp to force refresh on each rerun
    st.empty().text(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")
    auto_refresh = True
else:
    auto_refresh = False

if st.button("Stop Auto-refresh"):
    st.session_state.auto_refresh = False
    st.write("Auto-refresh stopped.")
    auto_refresh = False

# Manual refresh button
if st.button("Manual Refresh"):
    st.write(f"Manually refreshed at {datetime.now().strftime('%H:%M:%S')}")

# Option to remove cameras
if len(st.session_state.cameras) > 1:  # Keep at least one camera
    st.subheader("Remove Camera")
    camera_names = [cam["name"] for cam in st.session_state.cameras]
    camera_to_remove = st.selectbox("Select camera to remove", camera_names)
    
    if st.button("Remove Selected Camera"):
        for i, cam in enumerate(st.session_state.cameras):
            if cam["name"] == camera_to_remove:
                st.session_state.cameras.pop(i)
                st.experimental_rerun()
                break

# Display cameras - two per row
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
            st.markdown(f"### {camera['name']}")
            status = st.empty()
            frame_place = st.empty()
            
            # Get and display frame
            frame_data, error = get_mjpeg_frame(camera['url'])
            if frame_data:
                try:
                    image = Image.open(io.BytesIO(frame_data))
                    frame_place.image(image, use_column_width=True)
                    status.success("Connected")
                except Exception as e:
                    status.error(f"Error displaying image: {str(e)}")
            else:
                status.error(f"Failed to get frame: {error}")
    
    # Second camera in row
    idx = row * 2 + 1
    if idx < num_cameras:
        with cols[1]:
            camera = st.session_state.cameras[idx]
            st.markdown(f"### {camera['name']}")
            status = st.empty()
            frame_place = st.empty()
            
            # Get and display frame
            frame_data, error = get_mjpeg_frame(camera['url'])
            if frame_data:
                try:
                    image = Image.open(io.BytesIO(frame_data))
                    frame_place.image(image, use_column_width=True)
                    status.success("Connected")
                except Exception as e:
                    status.error(f"Error displaying image: {str(e)}")
            else:
                status.error(f"Failed to get frame: {error}")

# Set up auto-refresh if enabled
if auto_refresh:
    st.write(f"Next refresh in {refresh_rate} seconds...")
    # This will cause the app to rerun after the specified interval
    time.sleep(refresh_rate)
    st.experimental_rerun()
