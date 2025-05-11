
# import streamlit as st
# import requests
# from PIL import Image
# import io
# import time
# from datetime import datetime

# # Function to get a single frame from MJPEG stream
# def get_mjpeg_frame(url, timeout=5):
#     try:
#         # Make request with short timeout
#         response = requests.get(url, stream=True, timeout=timeout)
        
#         if response.status_code == 200:
#             # Read bytes
#             bytes_data = bytes()
#             for chunk in response.iter_content(chunk_size=1024):
#                 bytes_data += chunk
                
#                 # Find JPEG frame boundaries
#                 a = bytes_data.find(b'\xff\xd8')  # JPEG start
#                 b = bytes_data.find(b'\xff\xd9')  # JPEG end
                
#                 if a != -1 and b != -1:
#                     # Extract the JPEG frame
#                     jpg = bytes_data[a:b+2]
#                     return jpg, None
                
#                 # Prevent too much data accumulation
#                 if len(bytes_data) > 500000:  # ~500KB
#                     break
                    
#             return None, "Could not find complete JPEG frame"
#         else:
#             return None, f"HTTP error: {response.status_code}"
#     except requests.exceptions.RequestException as e:
#         return None, f"Connection error: {str(e)}"
#     except Exception as e:
#         return None, f"Error: {str(e)}"

# # Initialize session state for camera info
# if 'cameras' not in st.session_state:
#     st.session_state.cameras = []  # Start with empty camera list

# # App title
# st.title("IP Camera Viewer")

# # Camera addition form
# st.subheader("Add Camera")
# with st.form("add_camera_form"):
#     col1, col2 = st.columns(2)
#     with col1:
#         camera_name = st.text_input("Camera Name")
#     with col2:
#         camera_url = st.text_input("Camera URL")
    
#     submit_button = st.form_submit_button("Add Camera")
    
#     if submit_button and camera_name and camera_url:
#         new_camera = {
#             "name": camera_name,
#             "url": camera_url
#         }
#         st.session_state.cameras.append(new_camera)
#         st.experimental_rerun()

# # Camera table display
# if st.session_state.cameras:
#     st.subheader("Camera List")
    
#     # Create header row for our custom table
#     header_cols = st.columns([2, 4, 1])
#     with header_cols[0]:
#         st.markdown("**Camera Name**")
#     with header_cols[1]:
#         st.markdown("**Camera URL**")
#     with header_cols[2]:
#         st.markdown("**Action**")
    
#     st.markdown("---")  # Divider
    
#     # Create rows for each camera
#     for i, camera in enumerate(st.session_state.cameras):
#         cols = st.columns([2, 4, 1])
#         with cols[0]:
#             st.write(camera["name"])
#         with cols[1]:
#             st.write(camera["url"])
#         with cols[2]:
#             # Unique key for each button to avoid conflicts
#             if st.button("Remove", key=f"remove_btn_{i}"):
#                 st.session_state.cameras.pop(i)
#                 st.experimental_rerun()

# # Auto-refresh mechanism
# if 'auto_refresh' not in st.session_state:
#     st.session_state.auto_refresh = True  # Enable auto-refresh by default

# # Fixed refresh rate (3 seconds)
# refresh_rate = 3

# # Manual refresh button alongside auto-refresh toggle
# col1, col2 = st.columns(2)
# with col1:
#     if st.button("Manual Refresh"):
#         st.write(f"Manually refreshed at {datetime.now().strftime('%H:%M:%S')}")

# with col2:
#     auto_refresh = st.toggle("Auto-refresh", value=st.session_state.auto_refresh)
#     st.session_state.auto_refresh = auto_refresh

# # If auto-refresh is on, show timestamp
# if auto_refresh:
#     st.empty().text(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")

# # Display cameras - two per row
# if st.session_state.cameras:
#     st.subheader("Camera Feeds")
    
#     # Calculate number of rows needed
#     num_cameras = len(st.session_state.cameras)
#     num_rows = (num_cameras + 1) // 2  # Round up division
    
#     for row in range(num_rows):
#         cols = st.columns(2)
        
#         # First camera in row
#         idx = row * 2
#         if idx < num_cameras:
#             with cols[0]:
#                 camera = st.session_state.cameras[idx]
#                 st.markdown(f"### {camera['name']}")
#                 status = st.empty()
#                 frame_place = st.empty()
                
#                 # Get and display frame
#                 frame_data, error = get_mjpeg_frame(camera['url'])
#                 if frame_data:
#                     try:
#                         image = Image.open(io.BytesIO(frame_data))
#                         frame_place.image(image, use_column_width=True)
#                         status.success("Connected")
#                     except Exception as e:
#                         status.error(f"Error displaying image: {str(e)}")
#                 else:
#                     status.error(f"Failed to get frame: {error}")
        
#         # Second camera in row
#         idx = row * 2 + 1
#         if idx < num_cameras:
#             with cols[1]:
#                 camera = st.session_state.cameras[idx]
#                 st.markdown(f"### {camera['name']}")
#                 status = st.empty()
#                 frame_place = st.empty()
                
#                 # Get and display frame
#                 frame_data, error = get_mjpeg_frame(camera['url'])
#                 if frame_data:
#                     try:
#                         image = Image.open(io.BytesIO(frame_data))
#                         frame_place.image(image, use_column_width=True)
#                         status.success("Connected")
#                     except Exception as e:
#                         status.error(f"Error displaying image: {str(e)}")
#                 else:
#                     status.error(f"Failed to get frame: {error}")
# else:
#     st.info("No cameras added yet. Please add a camera using the form above.")

# # Set up auto-refresh if enabled
# if auto_refresh:
#     # This will cause the app to rerun after the specified interval
#     time.sleep(refresh_rate)
#     st.experimental_rerun()


import streamlit as st
import requests
from PIL import Image
import io
import time
from datetime import datetime
import base64

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

# Function to convert image bytes to base64 for embedding in HTML
def image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# Create HTML with auto-refresh for the image
def create_auto_refresh_html(img_base64, camera_name, refresh_rate=3):
    html = f"""
    <div style="text-align: center;">
        <h3>{camera_name}</h3>
        <img src="data:image/jpeg;base64,{img_base64}" style="max-width: 100%;">
        <script>
            // This script will refresh just the image, not the whole page
            setInterval(function() {{
                var timestamp = new Date().getTime();
                document.querySelector('img').src = 
                    "data:image/jpeg;base64,{img_base64}?" + timestamp;
            }}, {refresh_rate * 1000});
        </script>
    </div>
    """
    return html

# Initialize session state for camera info
if 'cameras' not in st.session_state:
    st.session_state.cameras = []  # Start with empty camera list

# Initialize last refresh time if not present
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

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
                "status": "Connecting..."
            }
            st.session_state.cameras.append(new_camera)
        else:
            st.error(f"Camera with name '{camera_name}' already exists!")

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
                st.markdown(f"### {camera['name']}")
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
        
        # Second camera in row
        idx = row * 2 + 1
        if idx < num_cameras:
            with cols[1]:
                camera = st.session_state.cameras[idx]
                st.markdown(f"### {camera['name']}")
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
else:
    st.info("No cameras added yet. Please add a camera using the form above.")

# Update every few seconds but avoid complete page rerun
time.sleep(1)  # Short sleep to prevent hogging resources
