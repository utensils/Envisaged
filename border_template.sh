#!/usr/bin/env bash
set -euo pipefail

# Use environment variables or defaults
TMP_DIR="${TMPDIR:-./tmp}"
VIDEO_DIR="${OUTPUT_DIR:-./video}"
GOURCE_RES="1920x1080"

# Create necessary directories
mkdir -p "${TMP_DIR}/tmp"
mkdir -p "${VIDEO_DIR}"

# Create named pipe for Gource output
mkfifo "${TMP_DIR}/tmp/gource.pipe"

# Start Gource
gource --seconds-per-day ${GOURCE_SECONDS_PER_DAY} \
    --user-scale ${GOURCE_USER_SCALE} \
    --time-scale ${GOURCE_TIME_SCALE} \
    --auto-skip-seconds ${GOURCE_AUTO_SKIP_SECONDS} \
    --title "${GOURCE_TITLE}" \
    --background-colour ${GOURCE_BACKGROUND_COLOR} \
    --font-colour ${GOURCE_TEXT_COLOR} \
    --camera-mode ${GOURCE_CAMERA_MODE} \
    --hide ${GOURCE_HIDE_ITEMS} \
    --font-size ${GOURCE_FONT_SIZE} \
    --dir-name-depth ${GOURCE_DIR_DEPTH} \
    --filename-time ${GOURCE_FILENAME_TIME} \
    --user-image-dir ${GOURCE_USER_IMAGE_DIR} \
    --max-user-speed ${GOURCE_MAX_USER_SPEED} \
    --bloom-multiplier 1.2 \
    --key \
    --highlight-users \
    --file-idle-time 0 \
    --max-file-lag 0.1 \
    --${GOURCE_RES} \
    --stop-at-end \
    ./development.log \
    -r ${GOURCE_FPS} \
    -o - >"${TMP_DIR}/tmp/gource.pipe" &

# Process with FFmpeg
ffmpeg -y -r ${GOURCE_FPS} \
    -f image2pipe -probesize 100M \
    -i "${TMP_DIR}/tmp/gource.pipe" \
    -vcodec libx264 \
    -level ${H264_LEVEL} \
    -pix_fmt yuv420p \
    -crf ${H264_CRF} \
    -preset ${H264_PRESET} \
    -bf 0 \
    "${VIDEO_DIR}/output.mp4"

# Cleanup
echo "Removing temporary files."
rm -rf "${TMP_DIR}/tmp"

echo "Video generation completed. Output saved to: ${VIDEO_DIR}/output.mp4"
