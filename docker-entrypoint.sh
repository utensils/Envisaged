#!/bin/bash

# Start Xvfb
echo "Starting Xvfb"
Xvfb :99 -ac -screen 0 $XVFB_WHD -nolisten tcp &
xvfb_pid="$!"
trap "echo 'Stopping Xvfb - pid: $xvfb_pid'; kill -SIGTERM $xvfb_pid" SIGINT SIGTERM

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
    export LOGO_FILTER_GRAPH=";[with_date][2:v]overlay=main_w-overlay_w-40:main_h-overlay_h-40[with_logo]"
    export FILTER_GRAPH_MAP=" -map [with_logo] "
  else
    echo "Not using a logo."
    export FILTER_GRAPH_MAP=" -map [with_date] "
  fi
else
  echo "Not using a logo."
  export FILTER_GRAPH_MAP=" -map [with_date] "
fi

# Start the httpd to serve the video.
cp /visualization/html/processing_gource.html /visualization/html/index.html
lighttpd -f http.conf -D &
httpd_pid="$!"
trap "echo 'Stopping lighthttpd - pid: $xvfb_pid'; kill -SIGTERM $httpd_pid" SIGINT SIGTERM

# Run the visualization
/visualization/create_video.sh
echo "Visualization process is complete"

# Wait for httpd process to end.
while kill -0 $httpd_pid > /dev/null 2>&1; do
    wait
done

# Exit
echo "Exiting"
exit
