import streamlit as st
import time
from pathlib import Path

def process_video(git_url, settings, is_test=False):
    """Process video using Gource and FFmpeg directly"""
    import tempfile
    import subprocess
    import os
    import time
    import logging
    from pathlib import Path
    from threading import Thread
    
    logger = logging.getLogger(__name__)
    
    # Store original working directory
    original_cwd = os.getcwd()
    
    try:
        # Create temp directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            # Initialize progress bar
            progress_bar = None
            if not is_test:
                progress_bar = st.progress(0)
                st.text('Setting up environment...')
            else:
                logger.info('Setting up environment...')
            
            # Create necessary subdirectories
            work_dir = temp_dir_path / 'work'
            video_dir = temp_dir_path / 'video'
            pipe_dir = temp_dir_path / 'pipe'
            avatar_dir = work_dir / 'avatars'
            for d in [work_dir, video_dir, pipe_dir, avatar_dir]:
                d.mkdir()
            
            # Set up resolution
            resolution_map = {
                '2160p': '3840x2160',
                '1440p': '2560x1440',
                '1080p': '1920x1080',
                '720p': '1280x720'
            }
            gource_res = resolution_map.get(settings['resolution'], '1920x1080')
            
            if not is_test:
                progress_bar.progress(25)
                st.text('Cloning repository...')
            else:
                logger.info('Cloning repository...')
            
            # Clone the repository
            os.chdir(work_dir)
            subprocess.run(['git', 'clone', git_url, 'repo'], check=True)
            
            # Generate git log for Gource
            repo_dir = work_dir / 'repo'
            os.chdir(repo_dir)
            # Use gource's native git log format
            gource_log_cmd = ['gource', '--output-custom-log', str(work_dir / 'development.log'), str(repo_dir)]
            subprocess.run(gource_log_cmd, check=True)
            
            if not is_test:
                progress_bar.progress(50)
                st.text('Generating visualization...')
            else:
                logger.info('Generating visualization...')
            
            # Create named pipe for Gource output
            pipe_path = pipe_dir / 'gource.pipe'
            if pipe_path.exists():
                pipe_path.unlink()
            os.mkfifo(pipe_path)
            
            # Build Gource command
            gource_cmd = [
                'gource',
                '--seconds-per-day', str(settings['seconds_per_day']),
                '--user-scale', str(settings['user_scale']),
                '--time-scale', str(settings['time_scale']),
                '--auto-skip-seconds', str(settings['auto_skip']),
                '--title', settings['title'],
                '--background-colour', settings['background_color'],
                '--font-colour', settings['overlay_font_color'],
                '--camera-mode', settings['camera_mode'],
                '--dir-name-depth', str(settings['dir_depth']),
                '--filename-time', str(settings['filename_time']),
                '--user-image-dir', str(avatar_dir),
                '--max-user-speed', str(settings['max_user_speed']),
                '--bloom-multiplier', '1.2',
                '--key',
                '--highlight-users',
                '--file-idle-time', '0',
                '--max-file-lag', '0.1',
                f'--{gource_res}',
                '--stop-at-end',
                str(work_dir / 'development.log'),
                '-r', str(settings['fps']),
                '-o', str(pipe_path)
            ]
            
            # Add hide options
            for item in settings['hide_items']:
                gource_cmd.extend(['--hide', item])
            
            # Build FFmpeg command
            output_path = video_dir / 'output.mp4'
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file if it exists
                '-r', str(settings['fps']),
                '-f', 'image2pipe',
                '-probesize', '100M',
                '-i', str(pipe_path),
                '-vcodec', 'libx264',
                '-level', settings['h264_level'],
                '-pix_fmt', 'yuv420p',
                '-crf', str(settings['h264_crf']),
                '-preset', settings['h264_preset'],
                '-bf', '0',
                str(output_path)
            ]

            # Print commands for debugging
            if not is_test:
                st.text(f"Gource command: {' '.join(gource_cmd)}")
                st.text(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
            else:
                logger.info(f"Gource command: {' '.join(gource_cmd)}")
                logger.info(f"FFmpeg command: {' '.join(ffmpeg_cmd)}")
            
            # Start Gource process with non-blocking output
            gource_process = subprocess.Popen(
                gource_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True
            )
            

            
            # Start FFmpeg process with non-blocking output
            ffmpeg_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=1,
                universal_newlines=True
            )
            
            # Create threads to monitor output
            def stream_output(process, prefix):
                for line in process.stderr:
                    if not is_test:
                        st.text(f"{prefix}: {line.strip()}")
                    else:
                        logger.info(f"{prefix}: {line.strip()}")
            
            gource_thread = Thread(target=stream_output, args=(gource_process, "Gource"))
            ffmpeg_thread = Thread(target=stream_output, args=(ffmpeg_process, "FFmpeg"))
            
            gource_thread.daemon = True
            ffmpeg_thread.daemon = True
            
            gource_thread.start()
            ffmpeg_thread.start()
            
            # Monitor processes with timeout
            start_time = time.time()
            max_duration = 300  # 5 minutes timeout
            check_interval = 1.0  # Check status every second
            last_progress = 0
            
            if not is_test:
                st.text("Starting video generation...")
            else:
                logger.info("Starting video generation...")
            
            while True:
                current_time = time.time()
                elapsed = current_time - start_time
                
                if elapsed > max_duration:
                    if not is_test:
                        st.error(f"Timeout after {max_duration} seconds")
                    else:
                        logger.error(f"Timeout after {max_duration} seconds")
                    gource_process.terminate()
                    ffmpeg_process.terminate()
                    raise TimeoutError(f"Video generation timed out after {max_duration} seconds")
                
                # Check process status
                gource_status = gource_process.poll()
                ffmpeg_status = ffmpeg_process.poll()
                
                # Update progress
                progress = min(75, int(50 + (elapsed / max_duration) * 25))
                if progress != last_progress:
                    if not is_test:
                        progress_bar.progress(progress)
                        st.text(f"Progress: {progress}% (elapsed: {elapsed:.1f}s)")
                    else:
                        logger.info(f"Progress: {progress}% (elapsed: {elapsed:.1f}s)")
                    last_progress = progress
                
                # Check for process completion or errors
                if gource_status is not None:
                    if gource_status != 0:
                        if not is_test:
                            st.error(f"Gource failed with exit code {gource_status}")
                        else:
                            logger.error(f"Gource failed with exit code {gource_status}")
                        raise RuntimeError(f"Gource process failed with exit code {gource_status}")
                    else:
                        if not is_test:
                            st.text("Gource completed successfully")
                        else:
                            logger.info("Gource completed successfully")
                
                if ffmpeg_status is not None:
                    if ffmpeg_status != 0:
                        if not is_test:
                            st.error(f"FFmpeg failed with exit code {ffmpeg_status}")
                        else:
                            logger.error(f"FFmpeg failed with exit code {ffmpeg_status}")
                        raise RuntimeError(f"FFmpeg process failed with exit code {ffmpeg_status}")
                    else:
                        if not is_test:
                            st.text("FFmpeg completed successfully")
                        else:
                            logger.info("FFmpeg completed successfully")
                
                # Break if both processes are done successfully
                if gource_status == 0 and ffmpeg_status == 0:
                    break
                
                # Check if either process failed
                if (gource_status is not None and gource_status != 0) or \
                   (ffmpeg_status is not None and ffmpeg_status != 0):
                    raise RuntimeError("One or both processes failed")
                
                time.sleep(check_interval)
            
            # Check for errors
            if gource_process.returncode != 0:
                stderr = gource_process.stderr.read().decode()
                if not is_test:
                    st.error(f'Error in Gource: {stderr}')
                else:
                    logger.error(f'Error in Gource: {stderr}')
                return None
            
            if ffmpeg_process.returncode != 0:
                stderr = ffmpeg_process.stderr.read().decode()
                if not is_test:
                    st.error(f'Error in FFmpeg: {stderr}')
                else:
                    logger.error(f'Error in FFmpeg: {stderr}')
                return None
            
            # Read the generated video
            if output_path.exists():
                with open(output_path, 'rb') as f:
                    video_bytes = f.read()
                if not is_test:
                    progress_bar.progress(100)
                return video_bytes
            else:
                if not is_test:
                    st.error('Video file was not generated')
                else:
                    logger.error('Video file was not generated')
                return None
                
    except Exception as e:
        if not is_test:
            st.error(f'Error generating video: {str(e)}')
        else:
            logger.error(f'Error generating video: {str(e)}')
        return None
        
    finally:
        # Always restore the original working directory
        os.chdir(original_cwd)

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
    
    # Border template is now the default implementation
    template = "border"

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
            'fps': fps,
            'template': template
        }
        
        with st.spinner("Generating visualization..."):
            video_data = process_video(git_url, settings)
            if video_data:
                st.success("Visualization completed!")
                st.video(video_data)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Powered by <a href="https://github.com/acaudwell/Gource">Gource</a> | 
    Made with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True) 