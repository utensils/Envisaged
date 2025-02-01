"""
Command-line interface for the Gource video generator.
"""
import click
import logging
from pathlib import Path
from .config import GourceConfig
from .generator import GourceGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def progress_callback(progress: int, message: str):
    """Simple progress callback for CLI."""
    logger.info(f"Progress {progress}%: {message}")


@click.command()
@click.argument('repo_url')
@click.option('--output', '-o', type=click.Path(), help='Output file path (default: output.mp4)')
@click.option('--title', help='Video title (default: repository name)')
@click.option('--resolution', type=click.Choice(['720p', '1080p', '1440p', '2160p']), default='1080p',
              help='Video resolution')
@click.option('--seconds-per-day', type=float, default=0.1, help='Seconds per day of development')
@click.option('--camera-mode', type=click.Choice(['overview', 'track']), default='overview',
              help='Camera mode')
@click.option('--time-scale', type=float, default=1.5, help='Time scale factor')
@click.option('--user-scale', type=float, default=1.5, help='User avatar scale factor')
@click.option('--background-color', default='000000', help='Background color (hex)')
@click.option('--font-color', default='0f5ca8', help='Font color (hex)')
@click.option('--dir-depth', type=int, default=3, help='Directory name depth')
@click.option('--max-user-speed', type=int, default=500, help='Maximum user speed')
@click.option('--auto-skip', type=float, default=0.5, help='Auto skip duration')
@click.option('--filename-time', type=float, default=2.0, help='Filename display time')
@click.option('--hide', multiple=True, type=click.Choice(['filenames', 'dirnames', 'usernames', 'tree', 'users', 'files', 'bloom']),
              help='Hide specific elements (can be used multiple times)')
@click.option('--invert-colors', is_flag=True, help='Invert colors')
@click.option('--h264-preset', type=click.Choice(['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']),
              default='medium', help='H.264 encoding preset')
@click.option('--h264-crf', type=int, default=23, help='H.264 CRF value (0-51, lower is better quality)')
@click.option('--h264-level', type=click.Choice(['4.0', '4.1', '4.2', '5.0', '5.1', '5.2']),
              default='5.1', help='H.264 level')
@click.option('--fps', type=int, default=60, help='Frames per second')
def main(repo_url, output, **kwargs):
    """Generate a Gource visualization video from a git repository.
    
    REPO_URL should be a valid git repository URL or local path.
    """
    try:
        # Set default title if not provided
        if not kwargs.get('title'):
            kwargs['title'] = repo_url.split('/')[-1].replace('.git', '')

        # Set default output path if not provided
        output_path = Path(output) if output else Path(f"{kwargs['title']}_gource.mp4")

        # Create config from CLI arguments
        config = GourceConfig(
            title=kwargs['title'],
            resolution=kwargs['resolution'],
            seconds_per_day=kwargs['seconds_per_day'],
            camera_mode=kwargs['camera_mode'],
            time_scale=kwargs['time_scale'],
            user_scale=kwargs['user_scale'],
            background_color=kwargs['background_color'].lstrip('#'),
            overlay_font_color=kwargs['font_color'].lstrip('#'),
            dir_depth=kwargs['dir_depth'],
            max_user_speed=kwargs['max_user_speed'],
            auto_skip=kwargs['auto_skip'],
            filename_time=kwargs['filename_time'],
            hide_items=list(kwargs['hide']),
            invert_colors=kwargs['invert_colors'],
            h264_preset=kwargs['h264_preset'],
            h264_crf=kwargs['h264_crf'],
            h264_level=kwargs['h264_level'],
            fps=kwargs['fps']
        )

        # Create generator and generate video
        generator = GourceGenerator(config, progress_callback)
        generator.generate_video(repo_url, output_path=output_path)

        logger.info(f"Video saved to: {output_path}")

    except Exception as e:
        logger.error(f"Error generating video: {str(e)}")
        raise click.ClickException(str(e))


if __name__ == '__main__':
    main()
