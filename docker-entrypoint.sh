#!/bin/bash

# Start Xvfb
echo "Starting Xvfb"
Xvfb :99 -ac -screen 0 $XVFB_WHD -nolisten tcp &
xvfb_pid="$!"

# possible race condition waiting for Xvfb.
sleep 5

# Clone our git repo for the visualization.
git clone ${GIT_URL} git_repo

# Generate a gource log file.
gource --output-custom-log development.log git_repo

# Set proper env variables if we have a logo.
if [ "${LOGO_URL}" != "" ]; then
	wget -O ./logo.image ${LOGO_URL}
	convert -geometry x160 ./logo.image ./logo.image
	if [ "$?" = 0 ]; then
		echo "Using logo from: ${LOGO_URL}"
		export LOGO=" -i ./logo.image "
		if [[ "${TEMPLATE}" == "border" ]]; then
			export LOGO_FILTER_GRAPH=";[with_date][2:v]overlay=main_w-overlay_w-40:main_h-overlay_h-40[with_logo]"
			export FILTER_GRAPH_MAP=" -map [with_logo] "
		else
			export LOGO_FILTER_GRAPH="[1:v]overlay=main_w-overlay_w-40:main_h-overlay_h-40[with_logo]"
			export FILTER_GRAPH_MAP=" -map [with_logo] "
		fi
	else
		if [[ "${TEMPLATE}" == "border" ]]; then
			echo "Not using a logo."
			export FILTER_GRAPH_MAP=" -map [with_date] "
		else
			export FILTER_GRAPH_MAP=""
		fi
	fi
else
	if [[ "${TEMPLATE}" == "border" ]]; then
		echo "Not using a logo."
		export FILTER_GRAPH_MAP=" -map [with_date] "
	else
		export FILTER_GRAPH_MAP=""
	fi
fi

# Start the httpd to serve the video.
cp /visualization/html/processing_gource.html /visualization/html/index.html
lighttpd -f http.conf -D &
httpd_pid="$!"
trap "echo 'Stopping proccesses PIDs: ($xvfb_pid, $http_pid)'; kill -SIGTERM $xvfb_pid $httpd_pid" SIGINT SIGTERM

# Run the visualization
if [[ "${TEMPLATE}" == "border" ]]; then
	/visualization/border_template.sh
else
	/visualization/no_template.sh
fi

echo "Visualization process is complete"

# Wait for httpd process to end.
while kill -0 $httpd_pid >/dev/null 2>&1; do
	wait
done

# Exit
echo "Exiting"
exit
