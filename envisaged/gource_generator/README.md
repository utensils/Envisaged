# Gource Generator

A Python package for generating beautiful Git repository visualizations using Gource. This package provides both a command-line interface and a Python API for creating customized repository visualization videos.

## Prerequisites

- Python 3.7+
- Gource
- FFmpeg

## Installation

The package is part of the Envisaged project. Install it using:

```bash
pip install -e .
```

## Command-Line Usage

The `gource-generator` command provides a simple way to create repository visualizations:

### Basic Usage

```bash
# Generate video with default settings
gource-generator https://github.com/username/repo.git

# Specify output file
gource-generator https://github.com/username/repo.git -o visualization.mp4

# Quick visualization with custom settings
gource-generator https://github.com/username/repo.git \
    --resolution 720p \
    --seconds-per-day 0.2 \
    --fps 30
```

### Available Options

```
Arguments:
  REPO_URL  Git repository URL or local path

Options:
  -o, --output PATH               Output file path (default: <repo_name>_gource.mp4)
  --title TEXT                    Video title (default: repository name)
  --resolution [720p|1080p|1440p|2160p]
                                 Video resolution (default: 1080p)
  --seconds-per-day FLOAT        Seconds per day of development (default: 0.1)
  --camera-mode [overview|track]  Camera mode (default: overview)
  --time-scale FLOAT             Time scale factor (default: 1.5)
  --user-scale FLOAT             User avatar scale factor (default: 1.5)
  --background-color TEXT        Background color in hex (default: 000000)
  --font-color TEXT             Font color in hex (default: 0f5ca8)
  --dir-depth INTEGER           Directory name depth (default: 3)
  --max-user-speed INTEGER      Maximum user speed (default: 500)
  --auto-skip FLOAT             Auto skip duration (default: 0.5)
  --filename-time FLOAT         Filename display time (default: 2.0)
  --hide [filenames|dirnames|usernames|tree|users|files|bloom]
                               Hide specific elements
  --invert-colors              Invert colors
  --h264-preset [ultrafast|superfast|veryfast|faster|fast|medium|slow|slower|veryslow]
                               H.264 encoding preset (default: medium)
  --h264-crf INTEGER           H.264 CRF value (0-51, lower is better quality) (default: 23)
  --h264-level [4.0|4.1|4.2|5.0|5.1|5.2]
                               H.264 level (default: 5.1)
  --fps INTEGER                Frames per second (default: 60)
  --help                       Show this message and exit
```

### Example Configurations

#### High-Quality Production Video
```bash
gource-generator https://github.com/username/repo.git \
    --title "Project History" \
    --resolution 1440p \
    --seconds-per-day 0.5 \
    --camera-mode track \
    --time-scale 2.0 \
    --user-scale 2.0 \
    --background-color 111111 \
    --font-color ffffff \
    --dir-depth 4 \
    --max-user-speed 600 \
    --auto-skip 1.0 \
    --filename-time 3.0 \
    --h264-preset slow \
    --h264-crf 18 \
    --fps 60
```

#### Quick Overview
```bash
gource-generator https://github.com/username/repo.git \
    --resolution 720p \
    --seconds-per-day 0.2 \
    --camera-mode overview \
    --time-scale 3.0 \
    --h264-preset fast \
    --fps 30
```

#### Clean Visualization
```bash
gource-generator https://github.com/username/repo.git \
    --hide filenames \
    --hide dirnames \
    --dir-depth 2 \
    --camera-mode track \
    --background-color 000000 \
    --font-color ffffff
```

## Python API Usage

You can also use the package programmatically in your Python code:

```python
from envisaged.gource_generator import GourceGenerator, GourceConfig

# Create configuration
config = GourceConfig(
    title="My Project History",
    resolution="1080p",
    seconds_per_day=0.2,
    camera_mode="track",
    time_scale=1.5,
    user_scale=1.5
)

# Optional progress callback
def progress_callback(progress: int, message: str):
    print(f"Progress {progress}%: {message}")

# Create generator and generate video
generator = GourceGenerator(config, progress_callback)
generator.generate_video(
    "https://github.com/username/repo.git",
    output_path="visualization.mp4"
)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
