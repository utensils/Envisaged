"""
Configuration class for Gource video generation.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GourceConfig:
    """Configuration for Gource video generation."""
    title: str
    resolution: str = '1080p'
    seconds_per_day: float = 0.1
    camera_mode: str = 'overview'
    time_scale: float = 1.5
    user_scale: float = 1.5
    background_color: str = '000000'
    overlay_font_color: str = '0f5ca8'
    dir_depth: int = 3
    max_user_speed: int = 500
    auto_skip: float = 0.5
    filename_time: float = 2.0
    hide_items: List[str] = None
    invert_colors: bool = False
    h264_preset: str = 'medium'
    h264_crf: int = 23
    h264_level: str = '5.1'
    fps: int = 60

    def __post_init__(self):
        """Initialize default values and validate configuration."""
        if self.hide_items is None:
            self.hide_items = []

    @property
    def resolution_dimensions(self) -> str:
        """Get the resolution dimensions based on the selected resolution."""
        resolution_map = {
            '2160p': '3840x2160',
            '1440p': '2560x1440',
            '1080p': '1920x1080',
            '720p': '1280x720'
        }
        return resolution_map.get(self.resolution, '1920x1080')
