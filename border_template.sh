#!/bin/bash

# Predefined resolutions and settings.
if [[ "${VIDEO_RESOLUTION}" == "2160p" ]]; then
	GOURCE_RES="3500x1940"
	OVERLAY_RES="1920x1080"
	GOURCE_PAD="3520:1960:3520:1960:#313133"
	KEY_CROP="320:1860:0:0"
	KEY_PAD="320:1960:0:0:#202021"
	DATE_CROP="3520:200:640:0"
	DATE_PAD="3840:200:320:200:#202021"
	OUTPUT_RES="3840:2160"
	echo "Using 2160p settings. Output will be 3840x2160 at 60fps."
elif [[ "${VIDEO_RESOLUTION}" == "1440p" ]]; then
	GOURCE_RES="2333x1293"
	OVERLAY_RES="1920x1080"
	GOURCE_PAD="2346:1306:2346:1306:#313133"
	KEY_CROP="214:1240:0:0"
	KEY_PAD="214:1306:0:0:#202021"
	DATE_CROP="2346:134:426:0"
	DATE_PAD="2560:134:214:134:#202021"
	OUTPUT_RES="2560:1440"
	echo "Using 1440p settings. Output will be 2560x1440 at 60fps."
elif [[ "${VIDEO_RESOLUTION}" == "1080p" ]]; then
	GOURCE_RES="1750x970"
	OVERLAY_RES="1920x1080"
	GOURCE_PAD="1760:980:1760:980:#313133"
	KEY_CROP="160:930:0:0"
	KEY_PAD="160:980:0:0:#202021"
	DATE_CROP="1760:100:320:0"
	DATE_PAD="1920:100:160:100:#202021"
	OUTPUT_RES="1920:1080"
	echo "Using 1080p settings. Output will be 1920x1080 at 60fps."
elif [[ "${VIDEO_RESOLUTION}" == "720p" ]]; then
	GOURCE_RES="1116x646"
	OVERLAY_RES="1920x1080"
	GOURCE_PAD="1128:653:1128:653:#313133"
	KEY_CROP="102:590:0:0"
	KEY_PAD="102:590:0:0:#202021,scale=152:653"
	DATE_CROP="1128:67:152:0"
	DATE_PAD="1280:67:152:0:#202021"
	OUTPUT_RES="1280:720"
	echo "Using 720p settings. Output will be 1280x720 at 60fps."
fi

if [[ "${INVERT_COLORS}" == "true" ]]; then
	GOURCE_FILTERS="${GOURCE_FILTERS},lutrgb=r=negval:g=negval:b=negval"
fi

# Create our temp directory
mkdir -p ./tmp

# Create our named pipes.
mkfifo ./tmp/gource.pipe
mkfifo ./tmp/overlay.pipe

# Start Gource for visualization.
echo "Starting Gource for ${GIT_URL}, using title: ${GOURCE_TITLE}"
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
	--max-user-speed ${GOURCE_MAX_USER_SPEED} \
	--bloom-multiplier 1.2 \
	--${GOURCE_RES} \
	--stop-at-end \
	./development.log \
	-r 60 \
	-o - >./tmp/gource.pipe &

# Start Gource for the overlay elements.
echo "Starting Gource for overlay components"
gource --seconds-per-day ${GOURCE_SECONDS_PER_DAY} \
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
	--${OVERLAY_RES} \
	--stop-at-end \
	--dir-name-depth 3 \
	--filename-time 2 \
	--max-user-speed 500 \
	./development.log \
	-r 60 \
	-o - >./tmp/overlay.pipe &

# Start ffmpeg to merge the two video outputs.
echo "Combining videos."
mkdir -p ./video
ffmpeg -y -r 60 -f image2pipe -probesize 100M -i ./tmp/gource.pipe \
	-y -r 60 -f image2pipe -probesize 100M -i ./tmp/overlay.pipe \
	${LOGO} \
	-filter_complex "[0:v]pad=${GOURCE_PAD}${GOURCE_FILTERS}[center];\
                         [1:v]scale=${OUTPUT_RES}[key_scale];\
                         [1:v]scale=${OUTPUT_RES}[date_scale];\
                         [key_scale]crop=${KEY_CROP},pad=${KEY_PAD}[key];\
                         [date_scale]crop=${DATE_CROP},pad=${DATE_PAD}[date];\
                         [key][center]hstack[with_key];\
                         [date][with_key]vstack[with_date]${LOGO_FILTER_GRAPH}${GLOBAL_FILTERS}" ${FILTER_GRAPH_MAP} \
	-vcodec libx264 -level ${H264_LEVEL} -pix_fmt yuv420p -crf ${H264_CRF} -preset ${H264_PRESET} -bf 0 ./video/output.mp4

# Remove our temporary files.
echo "Removing temporary files."
rm -rf ./tmp

# Update html and link new video.
filesize="$(du -sh /visualization/video/output.mp4 | cut -f 1)"
printf "$(cat /visualization/html/completed.html)" $filesize >/visualization/html/index.html
ln -sf /visualization/video/output.mp4 /visualization/html/output.mp4
