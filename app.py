import streamlit as st
import time
from pathlib import Path

def mock_process_video():
    """Mock function to simulate video processing"""
    progress_bar = st.progress(0)
    for i in range(100):
        time.sleep(0.1)
        progress_bar.progress(i + 1)
    return "https://example.com/video.mp4"

st.set_page_config(
    page_title="Envisaged - Git History Visualizer",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Envisaged - Git History Visualizer")
st.markdown("""
Create beautiful visualizations of your git repository's development history using Gource.
Simply provide a git repository URL and customize your visualization settings below.
""")

# Main input section
col1, col2 = st.columns(2)

with col1:
    git_url = st.text_input(
        "Git Repository URL",
        placeholder="https://github.com/username/repository.git"
    )
    
    logo_url = st.text_input(
        "Logo URL (optional)",
        placeholder="https://example.com/logo.png"
    )

with col2:
    title = st.text_input(
        "Visualization Title",
        value="Software Development"
    )
    
    template = st.selectbox(
        "Template",
        options=["border", "none"],
        help="Choose 'border' for frame around visualization or 'none' for standard output"
    )

# Video Settings
st.subheader("Video Settings")
video_col1, video_col2, video_col3 = st.columns(3)

with video_col1:
    resolution = st.selectbox(
        "Resolution",
        options=["2160p", "1440p", "1080p", "720p"],
        index=2
    )
    
    fps = st.number_input(
        "Frame Rate (FPS)",
        min_value=24,
        max_value=60,
        value=60
    )

with video_col2:
    h264_preset = st.selectbox(
        "H264 Preset",
        options=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"],
        index=5
    )
    
    h264_crf = st.slider(
        "H264 CRF (Quality)",
        min_value=0,
        max_value=51,
        value=23,
        help="Lower values mean better quality. 18-28 is recommended."
    )

with video_col3:
    h264_level = st.selectbox(
        "H264 Level",
        options=["4.0", "4.1", "4.2", "5.0", "5.1", "5.2"],
        index=4
    )

# Visualization Settings
st.subheader("Visualization Settings")
vis_col1, vis_col2 = st.columns(2)

with vis_col1:
    camera_mode = st.selectbox(
        "Camera Mode",
        options=["overview", "track"]
    )
    
    seconds_per_day = st.number_input(
        "Seconds per Day",
        min_value=0.1,
        max_value=10.0,
        value=0.1,
        step=0.1
    )
    
    time_scale = st.number_input(
        "Time Scale",
        min_value=0.1,
        max_value=5.0,
        value=1.5,
        step=0.1
    )
    
    user_scale = st.number_input(
        "User Avatar Scale",
        min_value=0.1,
        max_value=5.0,
        value=1.5,
        step=0.1
    )

with vis_col2:
    background_color = st.color_picker(
        "Background Color",
        value="#000000"
    )
    
    overlay_font_color = st.color_picker(
        "Overlay Font Color",
        value="#0f5ca8"
    )
    
    dir_depth = st.slider(
        "Directory Depth",
        min_value=1,
        max_value=10,
        value=3
    )
    
    max_user_speed = st.slider(
        "Max User Speed",
        min_value=100,
        max_value=1000,
        value=500
    )

# Advanced Settings
with st.expander("Advanced Settings"):
    auto_skip = st.number_input(
        "Auto Skip Seconds",
        min_value=0.1,
        max_value=10.0,
        value=0.5,
        step=0.1
    )
    
    filename_time = st.number_input(
        "Filename Display Duration",
        min_value=2.0,
        max_value=10.0,
        value=2.0,
        step=0.1
    )
    
    hide_items = st.multiselect(
        "Hide Elements",
        options=["usernames", "mouse", "date", "filenames"],
        default=["usernames", "mouse", "date", "filenames"]
    )
    
    invert_colors = st.checkbox("Invert Colors", value=False)

# Generate Video Button
if st.button("Generate Visualization", type="primary"):
    if not git_url:
        st.error("Please provide a Git repository URL")
    else:
        with st.spinner("Generating visualization..."):
            video_url = mock_process_video()
            st.success("Visualization completed!")
            st.video(video_url)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Powered by <a href="https://github.com/acaudwell/Gource">Gource</a> | 
    Made with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True) 