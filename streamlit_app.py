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
import cv2
import numpy as np
from PIL import Image
import io
import time
import threading

# Function to display camera stream
def display_camera_stream(camera_url, frame_placeholder, status_placeholder, stop_event):
    try:
        # Open the URL stream
        stream = requests.get(camera_url, stream=True, timeout=10)
        
        if stream.status_code == 200:
            status_placeholder.success("Connected")
            
            # Read the stream as long as the stop event is not set
            bytes_data = bytes()
            
            while not stop_event.is_set():
                # Read stream bytes
                for chunk in stream.iter_content(chunk_size=1024):
                    if stop_event.is_set():
                        break
                        
                    bytes_data += chunk
                    
                    # Find the JPEG frame boundaries
                    a = bytes_data.find(b'\xff\xd8')  # JPEG start
                    b = bytes_data.find(b'\xff\xd9')  # JPEG end
                    
                    if a != -1 and b != -1:
                        # Extract the JPEG frame
                        jpg = bytes_data[a:b+2]
                        bytes_data = bytes_data[b+2:]
                        
                        # Convert to image
                        try:
                            image = Image.open(io.BytesIO(jpg))
                            
                            # Display the image
                            frame_placeholder.image(image, use_column_width=True)
                        except Exception as e:
                            status_placeholder.error(f"Error: {e}")
                            
                        # Brief pause to not overload the system
                        time.sleep(0.01)
        else:
            status_placeholder.error(f"Failed to connect. Status code: {stream.status_code}")
            
    except requests.exceptions.RequestException as e:
        status_placeholder.error(f"Connection error: {e}")
    except Exception as e:
        status_placeholder.error(f"An error occurred: {e}")

def main():
    st.title("IP Camera Viewer")
    
    # Session state initialization for camera data
    if 'cameras' not in st.session_state:
        st.session_state.cameras = []
        st.session_state.camera_threads = []
        st.session_state.stop_events = []
    
    # Add default camera
    default_camera = {
        "name": "Default Camera",
        "url": "http://218.219.214.248:50000/nphMotionJpeg?Resolution=640x480"
    }
    
    # Add new camera form
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
            st.session_state.stop_events.append(threading.Event())
            st.experimental_rerun()
    
    # Display all cameras in rows of 2
    st.subheader("Camera Feeds")
    
    # Always ensure default camera is available
    if not st.session_state.cameras:
        st.session_state.cameras.append(default_camera)
        st.session_state.stop_events.append(threading.Event())
    
    # Create columns for camera display - 2 per row
    for i in range(0, len(st.session_state.cameras), 2):
        cols = st.columns(2)
        
        # First camera in the row
        with cols[0]:
            camera = st.session_state.cameras[i]
            st.markdown(f"### {camera['name']}")
            
            # Container for status and frame
            status_placeholder = st.empty()
            frame_placeholder = st.empty()
            
            # Button to remove camera (except default)
            if camera != default_camera:
                if st.button(f"Remove {camera['name']}", key=f"remove_{i}"):
                    # Stop thread if running
                    if i < len(st.session_state.stop_events):
                        st.session_state.stop_events[i].set()
                    
                    # Remove camera
                    st.session_state.cameras.pop(i)
                    st.session_state.stop_events.pop(i)
                    st.experimental_rerun()
            
            # Start thread for this camera if not already running
            if len(st.session_state.camera_threads) <= i or not st.session_state.camera_threads[i].is_alive():
                # Create new thread
                if i < len(st.session_state.stop_events):
                    stop_event = st.session_state.stop_events[i]
                else:
                    stop_event = threading.Event()
                    st.session_state.stop_events.append(stop_event)
                
                thread = threading.Thread(
                    target=display_camera_stream,
                    args=(camera['url'], frame_placeholder, status_placeholder, stop_event)
                )
                thread.daemon = True
                
                # Add or update thread in session state
                if len(st.session_state.camera_threads) <= i:
                    st.session_state.camera_threads.append(thread)
                else:
                    st.session_state.camera_threads[i] = thread
                
                # Start thread
                thread.start()
        
        # Second camera in the row (if available)
        if i + 1 < len(st.session_state.cameras):
            with cols[1]:
                camera = st.session_state.cameras[i + 1]
                st.markdown(f"### {camera['name']}")
                
                # Container for status and frame
                status_placeholder = st.empty()
                frame_placeholder = st.empty()
                
                # Button to remove camera (except default)
                if camera != default_camera:
                    if st.button(f"Remove {camera['name']}", key=f"remove_{i+1}"):
                        # Stop thread if running
                        if i + 1 < len(st.session_state.stop_events):
                            st.session_state.stop_events[i + 1].set()
                        
                        # Remove camera
                        st.session_state.cameras.pop(i + 1)
                        st.session_state.stop_events.pop(i + 1)
                        st.experimental_rerun()
                
                # Start thread for this camera if not already running
                if len(st.session_state.camera_threads) <= i + 1 or not st.session_state.camera_threads[i + 1].is_alive():
                    # Create new thread
                    if i + 1 < len(st.session_state.stop_events):
                        stop_event = st.session_state.stop_events[i + 1]
                    else:
                        stop_event = threading.Event()
                        st.session_state.stop_events.append(stop_event)
                    
                    thread = threading.Thread(
                        target=display_camera_stream,
                        args=(camera['url'], frame_placeholder, status_placeholder, stop_event)
                    )
                    thread.daemon = True
                    
                    # Add or update thread in session state
                    if len(st.session_state.camera_threads) <= i + 1:
                        st.session_state.camera_threads.append(thread)
                    else:
                        st.session_state.camera_threads[i + 1] = thread
                    
                    # Start thread
                    thread.start()
    
    # Add a master stop button
    if st.button("Stop All Streams"):
        for stop_event in st.session_state.stop_events:
            stop_event.set()
        st.session_state.camera_threads = []
        st.session_state.stop_events = []
        st.experimental_rerun()

if __name__ == "__main__":
    main()
