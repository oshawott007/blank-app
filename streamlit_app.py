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
#     st.session_state.cameras = [{
#         "name": "Default Camera", 
#         "url": "http://218.219.214.248:50000/nphMotionJpeg?Resolution=640x480"
#     }]

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

# # Display refresh rate slider
# refresh_rate = st.slider("Refresh Rate (seconds)", min_value=1, max_value=10, value=3)
# st.write(f"Frames will refresh every {refresh_rate} seconds")

# # Auto-refresh mechanism
# if st.button("Start Auto-refresh") or ('auto_refresh' in st.session_state and st.session_state.auto_refresh):
#     st.session_state.auto_refresh = True
#     st.write("Auto-refresh is ON. Click 'Stop Auto-refresh' to disable.")
#     # Add current timestamp to force refresh on each rerun
#     st.empty().text(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")
#     auto_refresh = True
# else:
#     auto_refresh = False

# if st.button("Stop Auto-refresh"):
#     st.session_state.auto_refresh = False
#     st.write("Auto-refresh stopped.")
#     auto_refresh = False

# # Manual refresh button
# if st.button("Manual Refresh"):
#     st.write(f"Manually refreshed at {datetime.now().strftime('%H:%M:%S')}")

# # Option to remove cameras
# if len(st.session_state.cameras) > 1:  # Keep at least one camera
#     st.subheader("Remove Camera")
#     camera_names = [cam["name"] for cam in st.session_state.cameras]
#     camera_to_remove = st.selectbox("Select camera to remove", camera_names)
    
#     if st.button("Remove Selected Camera"):
#         for i, cam in enumerate(st.session_state.cameras):
#             if cam["name"] == camera_to_remove:
#                 st.session_state.cameras.pop(i)
#                 st.experimental_rerun()
#                 break

# # Display cameras - two per row
# st.subheader("Camera Feeds")

# # Calculate number of rows needed
# num_cameras = len(st.session_state.cameras)
# num_rows = (num_cameras + 1) // 2  # Round up division

# for row in range(num_rows):
#     cols = st.columns(2)
    
#     # First camera in row
#     idx = row * 2
#     if idx < num_cameras:
#         with cols[0]:
#             camera = st.session_state.cameras[idx]
#             st.markdown(f"### {camera['name']}")
#             status = st.empty()
#             frame_place = st.empty()
            
#             # Get and display frame
#             frame_data, error = get_mjpeg_frame(camera['url'])
#             if frame_data:
#                 try:
#                     image = Image.open(io.BytesIO(frame_data))
#                     frame_place.image(image, use_column_width=True)
#                     status.success("Connected")
#                 except Exception as e:
#                     status.error(f"Error displaying image: {str(e)}")
#             else:
#                 status.error(f"Failed to get frame: {error}")
    
#     # Second camera in row
#     idx = row * 2 + 1
#     if idx < num_cameras:
#         with cols[1]:
#             camera = st.session_state.cameras[idx]
#             st.markdown(f"### {camera['name']}")
#             status = st.empty()
#             frame_place = st.empty()
            
#             # Get and display frame
#             frame_data, error = get_mjpeg_frame(camera['url'])
#             if frame_data:
#                 try:
#                     image = Image.open(io.BytesIO(frame_data))
#                     frame_place.image(image, use_column_width=True)
#                     status.success("Connected")
#                 except Exception as e:
#                     status.error(f"Error displaying image: {str(e)}")
#             else:
#                 status.error(f"Failed to get frame: {error}")

# # Set up auto-refresh if enabled
# if auto_refresh:
#     st.write(f"Next refresh in {refresh_rate} seconds...")
#     # This will cause the app to rerun after the specified interval
#     time.sleep(refresh_rate)
#     st.experimental_rerun()






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
    st.session_state.cameras = []  # Start with empty camera list

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

# Auto-refresh mechanism
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True  # Enable auto-refresh by default

# Fixed refresh rate (3 seconds)
refresh_rate = 3

# Manual refresh button alongside auto-refresh toggle
col1, col2 = st.columns(2)
with col1:
    if st.button("Manual Refresh"):
        st.write(f"Manually refreshed at {datetime.now().strftime('%H:%M:%S')}")

with col2:
    auto_refresh = st.toggle("Auto-refresh", value=st.session_state.auto_refresh)
    st.session_state.auto_refresh = auto_refresh

# If auto-refresh is on, show timestamp
if auto_refresh:
    st.empty().text(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")

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
else:
    st.info("No cameras added yet. Please add a camera using the form above.")

# Set up auto-refresh if enabled
if auto_refresh:
    # This will cause the app to rerun after the specified interval
    time.sleep(refresh_rate)
    st.experimental_rerun()
