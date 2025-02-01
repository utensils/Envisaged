import pytest
import tempfile
from pathlib import Path
import subprocess
import os
import time
import sys
import logging
from threading import Thread
from queue import Queue, Empty

# Set up logging with immediate output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def stream_output(pipe, prefix):
    """Stream output from a pipe to logger"""
    try:
        for line in iter(pipe.readline, b''):
            logger.info(f"{prefix}: {line.decode().strip()}")
    except Exception as e:
        logger.error(f"Error streaming {prefix}: {e}")

def test_video_generation(caplog):
    """Test that we can generate a video from a git repository with proper monitoring"""
    caplog.set_level(logging.INFO)
    from app import process_video
    
    # Test settings - using minimal settings for faster test
    settings = {
        'title': 'Test Visualization',
        'resolution': '720p',  # Lower resolution for faster processing
        'seconds_per_day': 0.1,
        'camera_mode': 'overview',
        'time_scale': 1.5,
        'user_scale': 1.5,
        'background_color': '000000',
        'overlay_font_color': '0f5ca8',
        'dir_depth': 3,
        'max_user_speed': 500,
        'auto_skip': 0.5,
        'filename_time': 2.0,
        'hide_items': ['filenames'],
        'invert_colors': False,
        'h264_preset': 'ultrafast',  # Fastest preset for testing
        'h264_crf': 28,  # Lower quality for faster encoding
        'h264_level': '5.1',
        'fps': 30,  # Lower FPS for faster processing
        'template': 'border'
    }
    
    start_time = time.time()
    max_duration = 300  # 5 minutes timeout
    
    # Create a test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        logger.info(f"Created temporary directory at {temp_path}")
        
        # Set environment variables
        os.environ['TMPDIR'] = str(temp_path)
        os.environ['OUTPUT_DIR'] = str(temp_path / 'output')
        
        # Run video generation with a smaller test repository
        logger.info("Starting video generation...")
        try:
            # First check if gource and ffmpeg are available
            try:
                subprocess.run(['gource', '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except subprocess.CalledProcessError as e:
                logger.error("Failed to run gource or ffmpeg command")
                logger.error(f"Error output: {e.stderr.decode() if e.stderr else 'No error output'}")
                raise
            except FileNotFoundError:
                logger.error("gource or ffmpeg not found. Please ensure both are installed.")
                raise

            video_data = process_video('https://github.com/utensils/essex.git', settings, is_test=True)
        except Exception as e:
            logger.error(f"Error during video generation: {e}")
            # Log the full traceback
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        duration = time.time() - start_time
        logger.info(f"Video generation took {duration:.2f} seconds")
        
        # Check if we exceeded timeout
        assert duration < max_duration, f"Video generation took too long ({duration:.2f} seconds)"
        
        # Assert video was generated
        assert video_data is not None, "Video data is None"
        assert len(video_data) > 0, "Video data is empty"
        
        # Check video file size
        video_size = len(video_data)
        logger.info(f"Generated video size: {video_size / 1024 / 1024:.2f} MB")
        
        # Basic video file validation
        assert video_size > 1024, "Video file is too small (less than 1KB)"
        
        # Check if the video file starts with the MP4 magic number
        assert video_data.startswith(b'\x00\x00\x00') or video_data.startswith(b'\x66\x74\x79\x70'), \
            "Generated file does not appear to be a valid MP4"
