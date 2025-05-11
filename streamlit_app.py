import streamlit as st
import requests
import cv2
import numpy as np
from PIL import Image
import io
import time

def main():
    st.title("IP Camera Live Feed")
    
    # Camera URL
    camera_url = "http://218.219.214.248:50000/nphMotionJpeg?Resolution=640x480"
    
    # Add a connection status indicator
    status_placeholder = st.empty()
    
    # Create a placeholder for the video frame
    frame_placeholder = st.empty()
    
    # Add a button to stop the stream
    stop_button = st.button("Stop Stream")
    
    try:
        # Open the URL stream
        stream = requests.get(camera_url, stream=True, timeout=10)
        
        if stream.status_code == 200:
            status_placeholder.success("Connected to camera stream")
            
            # Read the stream as long as the stop button is not pressed
            bytes_data = bytes()
            
            while not stop_button:
                # Read stream bytes
                for chunk in stream.iter_content(chunk_size=1024):
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
                            frame_placeholder.image(image, caption="Live Feed", use_column_width=True)
                        except Exception as e:
                            st.error(f"Error processing frame: {e}")
                            
                        # Check stop button again
                        if stop_button:
                            break
                        
                        # Brief pause to not overload the system
                        time.sleep(0.01)
                
                # If we've reached here, check the stop button
                if stop_button:
                    break
        else:
            status_placeholder.error(f"Failed to connect to camera. Status code: {stream.status_code}")
            
    except requests.exceptions.RequestException as e:
        status_placeholder.error(f"Connection error: {e}")
    except Exception as e:
        status_placeholder.error(f"An error occurred: {e}")
        
    # Display message when stream is stopped
    if stop_button:
        status_placeholder.info("Stream stopped")

if __name__ == "__main__":
    main()
