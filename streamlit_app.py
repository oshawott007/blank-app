import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import time
import numpy as np

# App configuration
st.set_page_config(page_title="Live CCTV Feed", layout="wide")
st.title("Live CCTV Monitoring")

# Configuration section in sidebar
with st.sidebar:
    st.header("Configuration")
    # Replace with your Cloudflare tunnel URL
    feed_url = st.text_input(
        "CCTV Feed URL", 
        "https://cctv.yourdomain.com/video_feed",
        help="URL for your MJPEG stream or snapshot endpoint"
    )
    refresh_rate = st.slider("Refresh rate (seconds)", 0.1, 5.0, 0.5, 0.1)
    show_fps = st.checkbox("Show FPS counter", True)

# Main display area
frame_placeholder = st.empty()
fps_placeholder = st.empty()
status_text = st.empty()

# Initialize FPS calculation
prev_time = time.time()
frame_count = 0
current_fps = 0

# Function to fetch frame from CCTV feed
def get_frame(url):
    try:
        response = requests.get(url, stream=True, timeout=5)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        return None
    except Exception as e:
        st.warning(f"Error fetching frame: {str(e)}")
        return None

# Main loop for displaying video
while True:
    start_time = time.time()
    
    # Get frame from CCTV feed
    frame = get_frame(feed_url)
    
    if frame is not None:
        # Display the frame
        frame_placeholder.image(frame, use_column_width=True)
        status_text.success("Connected to CCTV feed")
    else:
        status_text.error("Unable to fetch frame from CCTV")
    
    # Calculate and display FPS
    frame_count += 1
    if time.time() - prev_time >= 1.0:  # Update FPS every second
        current_fps = frame_count / (time.time() - prev_time)
        frame_count = 0
        prev_time = time.time()
    
    if show_fps:
        fps_placeholder.metric("FPS", f"{current_fps:.1f}")
    
    # Control refresh rate
    elapsed_time = time.time() - start_time
    time.sleep(max(0, refresh_rate - elapsed_time))
