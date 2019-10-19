#!/bin/bash

# Predefined resolutions and settings.
if [[ "${VIDEO_RESOLUTION}" == "2160p" ]]; then
	GOURCE_RES="3840x2160"
	echo "Using 2160p settings. Output will be 3840x2160 at 60fps."
elif [[ "${VIDEO_RESOLUTION}" == "1440p" ]]; then
	GOURCE_RES="2560x1440"
	echo "Using 1440p settings. Output will be 2560x1440 at 60fps."
elif [[ "${VIDEO_RESOLUTION}" == "1080p" ]]; then
	GOURCE_RES="1920x1080"
	echo "Using 1080p settings. Output will be 1920x1080 at 60fps."
elif [[ "${VIDEO_RESOLUTION}" == "720p" ]]; then
	GOURCE_RES="1280x720"
	echo "Using 720p settings. Output will be 1280x720 at 60fps."
fi

if [[ "${INVERT_COLORS}" == "true" ]]; then
	if [[ "${GOURCE_FILTERS}" == "" ]]; then
		GOURCE_FILTERS="lutrgb=r=negval:g=negval:b=negval"
	else
		GOURCE_FILTERS="${GOURCE_FILTERS},lutrgb=r=negval:g=negval:b=negval,"
	fi
fi

# Create our temp directory
mkdir -p ./tmp

# Create our named pipes.
mkfifo ./tmp/gource.pipe

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
	--user-image-dir ${GOURCE_USER_IMAGE_DIR} \
	--max-user-speed ${GOURCE_MAX_USER_SPEED} \
	--bloom-multiplier 1.2 \
	--${GOURCE_RES} \
	--stop-at-end \
	./development.log \
	-r 60 \
	-o - >./tmp/gource.pipe &

# Start ffmpeg to merge the two video outputs.
mkdir -p ./video
if [[ "${LOGO_FILTER_GRAPH}" != "" ]]; then
	if [[ "${GOURCE_FILTERS}" != "" ]]; then
		ffmpeg -y -r 60 -f image2pipe -probesize 100M -i ./tmp/gource.pipe \
			${LOGO} \
			-filter_complex "[0:v]${GOURCE_FILTERS}[filtered];[filtered]${LOGO_FILTER_GRAPH}${GLOBAL_FILTERS}" ${FILTER_GRAPH_MAP} \
			-vcodec libx264 -level ${H264_LEVEL} -pix_fmt yuv420p -crf ${H264_CRF} -preset ${H264_PRESET} -bf 0 ./video/output.mp4
	else
		ffmpeg -y -r 60 -f image2pipe -probesize 100M -i ./tmp/gource.pipe \
			${LOGO} \
			-filter_complex "[0:v]${LOGO_FILTER_GRAPH}${GLOBAL_FILTERS}" ${FILTER_GRAPH_MAP} \
			-vcodec libx264 -level ${H264_LEVEL} -pix_fmt yuv420p -crf ${H264_CRF} -preset ${H264_PRESET} -bf 0 ./video/output.mp4
	fi
elif [[ "${GOURCE_FILTERS}" != "" ]]; then
	ffmpeg -y -r 60 -f image2pipe -probesize 100M -i ./tmp/gource.pipe \
		-filter_complex "${GOURCE_FILTERS}${GLOBAL_FILTERS}" ${FILTER_GRAPH_MAP} \
		-vcodec libx264 -level ${H264_LEVEL} -pix_fmt yuv420p -crf ${H264_CRF} -preset ${H264_PRESET} -bf 0 ./video/output.mp4
else
	ffmpeg -y -r 60 -f image2pipe -probesize 100M -i ./tmp/gource.pipe \
		-vcodec libx264 -level ${H264_LEVEL} -pix_fmt yuv420p -crf ${H264_CRF} -preset ${H264_PRESET} -bf 0 ./video/output.mp4
fi

# Remove our temporary files.
echo "Removing temporary files."
rm -rf ./tmp

# Update html and link new video.
filesize="$(du -sh /visualization/video/output.mp4 | cut -f 1)"
printf "$(cat /visualization/html/completed.html)" $filesize >/visualization/html/index.html
ln -sf /visualization/video/output.mp4 /visualization/html/output.mp4
