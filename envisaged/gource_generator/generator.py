"""
Core Gource video generation functionality.
"""
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional

from .config import GourceConfig

logger = logging.getLogger(__name__)


class GourceGenerator:
    """Handles the generation of Gource visualization videos."""

    def __init__(self, config: GourceConfig, progress_callback: Optional[Callable[[int, str], None]] = None):
        """
        Initialize the GourceGenerator.

        Args:
            config: GourceConfig instance containing generation settings
            progress_callback: Optional callback function for progress updates
        """
        self.config = config
        self.progress_callback = progress_callback or self._default_progress_callback

    def _default_progress_callback(self, progress: int, message: str) -> None:
        """Default progress callback that logs to console."""
        logger.info(f"Progress {progress}%: {message}")

    def _update_progress(self, progress: int, message: str) -> None:
        """Update progress using the callback."""
        self.progress_callback(progress, message)

    def _run_command(self, cmd: list, check: bool = True, **kwargs) -> subprocess.CompletedProcess:
        """Run a command and handle errors."""
        try:
            return subprocess.run(cmd, check=check, **kwargs)
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            logger.error(f"Error output: {e.stderr.decode() if e.stderr else 'No error output'}")
            raise
        except FileNotFoundError:
            logger.error(f"Command not found: {cmd[0]}")
            raise

    def _clone_repository(self, git_url: str, work_dir: Path) -> Path:
        """Clone the git repository."""
        self._update_progress(25, "Cloning repository...")
        repo_dir = work_dir / 'repo'
        self._run_command(['git', 'clone', git_url, str(repo_dir)])
        return repo_dir

    def _generate_gource_log(self, repo_dir: Path, work_dir: Path) -> Path:
        """Generate the Gource log file."""
        log_path = work_dir / 'development.log'
        self._run_command([
            'gource',
            '--output-custom-log',
            str(log_path),
            str(repo_dir)
        ])
        return log_path

    def _build_gource_command(self, log_path: Path, pipe_path: Path, avatar_dir: Path) -> list:
        """Build the Gource command with all parameters."""
        return [
            'gource',
            '--seconds-per-day', str(self.config.seconds_per_day),
            '--user-scale', str(self.config.user_scale),
            '--time-scale', str(self.config.time_scale),
            '--auto-skip-seconds', str(self.config.auto_skip),
            '--title', self.config.title,
            '--background-colour', self.config.background_color,
            '--font-colour', self.config.overlay_font_color,
            '--camera-mode', self.config.camera_mode,
            '--dir-name-depth', str(self.config.dir_depth),
            '--filename-time', str(self.config.filename_time),
            '--user-image-dir', str(avatar_dir),
            '--max-user-speed', str(self.config.max_user_speed),
            '--bloom-multiplier', '1.2',
            '--key',
            '--highlight-users',
            '--file-idle-time', '0',
            '--max-file-lag', '0.1',
            f'--{self.config.resolution_dimensions}',
            '--stop-at-end',
            str(log_path),
            '-r', str(self.config.fps),
            '--output-ppm-stream', str(pipe_path)
        ]

    def _build_ffmpeg_command(self, pipe_path: Path, output_path: Path) -> list:
        """Build the FFmpeg command for video encoding."""
        return [
            'ffmpeg',
            '-y',
            '-f', 'image2pipe',
            '-vcodec', 'ppm',
            '-i', str(pipe_path),
            '-vcodec', 'libx264',
            '-preset', self.config.h264_preset,
            '-crf', str(self.config.h264_crf),
            '-level', self.config.h264_level,
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ]

    def generate_video(self, git_url: str, output_path: Optional[Path] = None) -> bytes:
        """
        Generate a Gource visualization video from a git repository.

        Args:
            git_url: URL of the git repository
            output_path: Optional path to save the video file

        Returns:
            bytes: The generated video data if output_path is None
        """
        self._update_progress(0, "Setting up environment...")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            work_dir = temp_dir_path / 'work'
            video_dir = temp_dir_path / 'video'
            pipe_dir = temp_dir_path / 'pipe'
            avatar_dir = work_dir / 'avatars'

            # Create directories
            for d in [work_dir, video_dir, pipe_dir, avatar_dir]:
                d.mkdir()

            # Clone repository and generate log
            repo_dir = self._clone_repository(git_url, work_dir)
            log_path = self._generate_gource_log(repo_dir, work_dir)

            self._update_progress(50, "Generating visualization...")

            # Set up named pipe
            pipe_path = pipe_dir / 'gource.pipe'
            if pipe_path.exists():
                pipe_path.unlink()
            os.mkfifo(pipe_path)

            # Prepare commands
            gource_cmd = self._build_gource_command(log_path, pipe_path, avatar_dir)
            output_path = output_path or (video_dir / 'output.mp4')
            ffmpeg_cmd = self._build_ffmpeg_command(pipe_path, output_path)

            # Run Gource and FFmpeg
            with subprocess.Popen(gource_cmd, stdout=subprocess.PIPE) as gource_process:
                ffmpeg_process = subprocess.Popen(
                    ffmpeg_cmd,
                    stdin=gource_process.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                gource_process.stdout.close()
                output, error = ffmpeg_process.communicate()

                if ffmpeg_process.returncode != 0:
                    raise RuntimeError(f"FFmpeg error: {error.decode()}")

            self._update_progress(100, "Video generation complete")

            # Read the generated video file
            with open(output_path, 'rb') as f:
                video_data = f.read()
            
            # If output_path was provided by the user, return None (file is saved)
            # Otherwise return the video data
            return None if output_path else video_data
