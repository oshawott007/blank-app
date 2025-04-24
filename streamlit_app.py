import streamlit as st
import requests
from PIL import Image
from io import BytesIO

# For live feed
st.image("https://cctv.yourdomain.com/video_feed")

# Or for snapshots
def get_cctv_image():
    response = requests.get("https://cctv.yourdomain.com/snapshot.jpg", stream=True)
    return Image.open(BytesIO(response.content))

if st.button("Refresh CCTV"):
    img = get_cctv_image()
    st.image(img, caption="Latest CCTV Snapshot")
