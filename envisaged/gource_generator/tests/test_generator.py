"""
Tests for the Gource video generator.
"""
import logging
import pytest
from pathlib import Path
from ..config import GourceConfig
from ..generator import GourceGenerator


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return GourceConfig(
        title='Test Visualization',
        resolution='720p',
        seconds_per_day=0.1,
        camera_mode='overview',
        time_scale=1.5,
        user_scale=1.5,
        background_color='000000',
        overlay_font_color='0f5ca8',
        dir_depth=3,
        max_user_speed=500,
        auto_skip=0.5,
        filename_time=2.0,
        hide_items=['filenames'],
        invert_colors=False,
        h264_preset='ultrafast',
        h264_crf=28,
        h264_level='5.1',
        fps=30
    )


def test_generator_initialization(test_config):
    """Test GourceGenerator initialization."""
    generator = GourceGenerator(test_config)
    assert generator.config == test_config
    assert callable(generator.progress_callback)


def test_progress_callback(test_config, caplog):
    """Test progress callback functionality."""
    caplog.set_level(logging.INFO)
    generator = GourceGenerator(test_config)
    generator._update_progress(50, "Test message")
    assert "Progress 50%: Test message" in caplog.text


def test_video_generation(test_config, tmp_path):
    """Test video generation process."""
    generator = GourceGenerator(test_config)
    output_path = tmp_path / "test_output.mp4"
    
    # Use a small test repository
    test_repo = "https://github.com/utensils/essex.git"
    
    try:
        generator.generate_video(test_repo, output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        pytest.skip(f"Test skipped due to environment setup: {str(e)}")


def test_config_resolution_dimensions():
    """Test resolution dimension mapping."""
    config = GourceConfig(title="Test")
    assert config.resolution_dimensions == "1920x1080"  # Default
    
    config.resolution = "720p"
    assert config.resolution_dimensions == "1280x720"
    
    config.resolution = "invalid"
    assert config.resolution_dimensions == "1920x1080"  # Fallback
