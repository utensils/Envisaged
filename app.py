import streamlit as st
import time
from pathlib import Path
from envisaged.gource_generator import GourceGenerator, GourceConfig

def process_video(git_url, settings, is_test=False):
    """Process video using GourceGenerator."""
    import logging
    
    logger = logging.getLogger(__name__)

    # Convert settings dict to GourceConfig
    config = GourceConfig(
        title=settings['title'],
        resolution=settings['resolution'],
        seconds_per_day=settings['seconds_per_day'],
        camera_mode=settings['camera_mode'],
        time_scale=settings['time_scale'],
        user_scale=settings['user_scale'],
        background_color=settings['background_color'],
        overlay_font_color=settings['overlay_font_color'],
        dir_depth=settings['dir_depth'],
        max_user_speed=settings['max_user_speed'],
        auto_skip=settings['auto_skip'],
        filename_time=settings['filename_time'],
        hide_items=settings.get('hide_items', []),
        invert_colors=settings.get('invert_colors', False),
        h264_preset=settings['h264_preset'],
        h264_crf=settings['h264_crf'],
        h264_level=settings['h264_level'],
        fps=settings['fps']
    )

    # Create progress callback
    def progress_callback(progress: int, message: str):
        if not is_test:
            progress_bar = st.progress(progress)
            st.text(message)
        else:
            logger.info(f"Progress {progress}%: {message}")

    try:
        generator = GourceGenerator(config, progress_callback)
        return generator.generate_video(git_url)
    except Exception as e:
        logger.error(f"Error during video generation: {str(e)}")
        raise

# Set page configuration
st.set_page_config(
    page_title="Envisaged - Git History Visualizer",
    page_icon="🎬",
    layout="wide"
)

st.title("Envisaged - Git History Visualizer 🎬")
st.write("Create beautiful Git repository visualizations using Gource")

# Main input section
col1, col2 = st.columns(2)

with col1:
    git_url = st.text_input(
        "Git Repository URL",
        placeholder="https://github.com/username/repository.git"
    )

with col2:
    title = st.text_input(
        "Visualization Title",
        value="Software Development"
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
        "Hide Items",
        ["filenames", "dirnames", "usernames", "tree", "users", "files", "bloom"],
        default=[]
    )
    
    invert_colors = st.checkbox("Invert Colors")

submitted = st.button("Generate Video")

if submitted:
    if not git_url:
        st.error("Please enter a Git repository URL")
    else:
        try:
            # Collect all settings
            settings = {
                'title': title,
                'resolution': resolution,
                'seconds_per_day': seconds_per_day,
                'camera_mode': camera_mode,
                'time_scale': time_scale,
                'user_scale': user_scale,
                'background_color': background_color.lstrip('#'),
                'overlay_font_color': overlay_font_color.lstrip('#'),
                'dir_depth': dir_depth,
                'max_user_speed': max_user_speed,
                'auto_skip': auto_skip,
                'filename_time': filename_time,
                'hide_items': hide_items,
                'invert_colors': invert_colors,
                'h264_preset': h264_preset,
                'h264_crf': h264_crf,
                'h264_level': h264_level,
                'fps': fps
            }
            
            video_data = process_video(git_url, settings)
            
            # Display video
            st.video(video_data)
            
            # Download button
            st.download_button(
                label="Download Video",
                data=video_data,
                file_name=f"{settings['title']}_gource.mp4",
                mime="video/mp4"
            )
            
        except Exception as e:
            st.error(f"Error generating video: {str(e)}")

# Footer
st.markdown("""
<div style='text-align: center'>
    <p>Powered by <a href="https://github.com/acaudwell/Gource">Gource</a> | 
    Made with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)
