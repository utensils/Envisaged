#!/bin/bash

# Create our temp directory

mkdir -p ./tmp
# Create our named pipes.
mkfifo ./tmp/gource.pipe
mkfifo ./tmp/overlay.pipe


# Start Gource for visualization.
echo "Starting Gource for ${GIT_URL}, using title: ${GOURCE_TITLE}"
gource  --seconds-per-day ${GOURCE_SECONDS_PER_DAY} \
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
        --max-user-speed ${GOURCE_MAX_USER_SPEED} \
        --bloom-multiplier 1.2 \
        -3500x1940 \
        --stop-at-end \
        ./development.log \
        -r 60 \
        -o - > ./tmp/gource.pipe &


# Start Gource for the overlay elements.
echo "Starting Gource for overlay components"
gource  --seconds-per-day ${GOURCE_SECONDS_PER_DAY} \
        --user-scale ${GOURCE_USER_SCALE} \
        --time-scale ${GOURCE_TIME_SCALE} \
        --auto-skip-seconds ${GOURCE_AUTO_SKIP_SECONDS} \
        --key \
        --transparent \
        --background-colour 202021 \
        --font-colour ${OVERLAY_FONT_COLOR} \
        --camera-mode overview \
        --hide bloom,dirnames,files,filenames,mouse,root,tree,users,usernames \
        --font-size 60 \
        --1920x1080 \
        --stop-at-end \
        --dir-name-depth 3 \
        --filename-time 2 \
        --max-user-speed 500 \
        ./development.log \
        -r 60 \
        -o - > ./tmp/overlay.pipe &


# Start ffmpeg to merge the two video outputs.
echo "Combining videos."
mkdir -p ./video
ffmpeg  -y -r 60 -f image2pipe  -probesize 100M -i ./tmp/gource.pipe \
        -y -r 60 -f image2pipe  -probesize 100M -i ./tmp/overlay.pipe \
        ${LOGO} \
        -filter_complex "[0:v]pad=3520:1960:3520:1960:#313133[center];\
                         [1:v]scale=3840:2160[key_scale];\
                         [1:v]scale=3840:2160[date_scale];\
                         [key_scale]crop=320:1860:0:0,pad=320:1960:0:0:#202021[key];\
                         [date_scale]crop=3520:200:640:0,pad=3840:200:320:200:#202021[date];\
                         [key][center]hstack[with_key];\
                         [date][with_key]vstack[with_date]${LOGO_FILTER_GRAPH}" ${FILTER_GRAPH_MAP} \
        -vcodec libx264 -level ${H264_LEVEL} -pix_fmt yuv420p -crf ${H264_CRF}  -preset ${H264_PRESET} -bf 0  ./video/4k.compressed.mp4


# Remove our temporary files.
echo "Removing temporary files."
rm -rf ./tmp

# Update html and link new video.
cp /visualization/html/completed.html /visualization/html/index.html
ln -sf /visualization/video/4k.compressed.mp4 /visualization/html/4k.compressed.mp4
