#!/usr/bin/env bash
set -euo pipefail

# Configuration
OUTPUT_DIR="output"
RESOLUTION="1920x1080"
FRAMERATE="60"
VIDEO_NAME="gource.mp4"

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Run Gource with modern settings
docker run --rm \
    -v "$(pwd):/workspace" \
    -v "${OUTPUT_DIR}:/output" \
    gource-viz \
    --seconds-per-day 0.1 \
    --auto-skip-seconds 0.1 \
    --title "Repository Visualization" \
    --key \
    --highlight-users \
    --hide filenames \
    --file-idle-time 0 \
    --max-file-lag 0.1 \
    --bloom-multiplier 0.8 \
    --background-colour 000000 \
    --viewport "${RESOLUTION}" \
    -o - | \
ffmpeg -y -r ${FRAMERATE} \
    -f image2pipe -vcodec ppm \
    -i - \
    -vcodec libx264 \
    -preset medium \
    -pix_fmt yuv420p \
    -crf 18 \
    -movflags +faststart \
    "${OUTPUT_DIR}/${VIDEO_NAME}"

echo "Visualization complete! Output saved to ${OUTPUT_DIR}/${VIDEO_NAME}"
