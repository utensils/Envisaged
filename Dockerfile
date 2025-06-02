# 1. Set Base Image and Working Directory
FROM python:3.9-alpine
WORKDIR /app

# 2. Install System Dependencies
RUN apk update && \
    apk add --no-cache \
        bash \
        ffmpeg \
        git \
        gource \
        imagemagick \
        xvfb \
        mesa-gl \
        wget && \
    rm -rf /var/cache/apk/*

# 3. Copy Application Files
COPY requirements.txt /app/requirements.txt
COPY envisaged.py /app/envisaged.py
# COPY ./html /app/html # Removed

# 4. Install Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Adjust File Permissions (if necessary)
RUN chmod +x envisaged.py

# 6. Set Environment Variables
ENV VISUALIZATION_DIR /visualization
ENV DISPLAY_NUM 99
ENV DISPLAY :${DISPLAY_NUM}
ENV XVFB_WHD "1280x720x24"
ENV VIDEO_RESOLUTION "1280x720"
# Target video bitrate for FFmpeg
ENV VIDEO_BITRATE "5M"
# Framerate for Gource and FFmpeg
ENV VIDEO_FRAMERATE "25"
# 'border' or 'none'
ENV TEMPLATE "none"
ENV GOURCE_SECONDS_PER_DAY "0.1"
ENV GOURCE_AUTO_SKIP_SECONDS "0.1"
# Inactivity period in seconds to hide files. 0 to disable.
ENV GOURCE_FILE_IDLE_TIME "0"
# Max number of files or 0 for unlimited
ENV GOURCE_MAX_FILES "0"
# Path to user avatar images
ENV GOURCE_USER_IMAGE_DIR "/visualization/avatars"
# Note: GOURCE_TITLE, GOURCE_LOGO, GOURCE_FONT_SIZE etc. are fetched by envisaged.py directly from environment if set.
# FFmpeg H.264 preset
ENV H264_PRESET "medium"
# FFmpeg H.264 Constant Rate Factor
ENV H264_CRF "23"
# Note: GOURCE_FILTERS & GLOBAL_FILTERS are also fetched by envisaged.py from environment if set.
# Example (do not uncomment here, set in docker run):
# ENV GOURCE_FILTERS="speeD=2.0,scale=720:-1"
# ENV GLOBAL_FILTERS="eq=contrast=1.1:brightness=0.1"

# 7. Expose Port
# EXPOSE 80 # Removed

# 8. Set Entrypoint/Command
CMD ["python", "/app/envisaged.py"]

# 9. Labels
LABEL org.opencontainers.image.title="Envisaged Gource Visualization"
LABEL org.opencontainers.image.description="Automated Gource visualization generator"
# Placeholder
LABEL org.opencontainers.image.source="https://github.com/YOUR_REPO_HERE"
# Placeholder
LABEL maintainer="Your Name <you@example.com>"
