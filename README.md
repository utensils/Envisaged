# Envisaged - Dockerized Gource Visualizations

[![Build Status](https://travis-ci.org/jamesbrink/envisaged.svg?branch=master)](https://travis-ci.org/jamesbrink/envisaged) [![Docker Automated build](https://img.shields.io/docker/automated/jamesbrink/envisaged.svg)](https://hub.docker.com/r/jamesbrink/envisaged/) [![Docker Pulls](https://img.shields.io/docker/pulls/jamesbrink/envisaged.svg)](https://hub.docker.com/r/jamesbrink/envisaged/) [![Docker Stars](https://img.shields.io/docker/stars/jamesbrink/envisaged.svg)](https://hub.docker.com/r/jamesbrink/envisaged/) [![](https://images.microbadger.com/badges/image/jamesbrink/envisaged.svg)](https://microbadger.com/images/jamesbrink/envisaged "Get your own image badge on microbadger.com") [![](https://images.microbadger.com/badges/version/jamesbrink/envisaged.svg)](https://microbadger.com/images/jamesbrink/envisaged "Get your own version badge on microbadger.com")

Built on top of the official [Alpine Linux 3.7][alpine linux image] image, extending from base image [`jamesbrink/gource`][jamesbrink/gource].  

## About

Painless data visualizations from git history showing a repositories development progression over time.  
This container combines the awesome [Gource][gource] program witth the power of [FFmpeg][ffmpeg_home] and the h.264 codec to bring you high resolution (4k at 60fps) video visualizations.

This container is 100% headless, it does this by leveraging [Xvfb][xvfb] combined with the [Mesa 3d Gallium llvmpipe Driver][mesa]. Unlike other docker containers with Gource, this container does not eat up 100's of gigabtyes of disk space, nor does it require an actual GPU to run. The process runs the Gource simulation concurrently with the FFmpeg encoding process using a set of named pipes. There is a slight trade off in performance, but this makes it very easy to run in any environment such as AWS without the need to provision large amounts of storage, or run any cleanup.

## Usage Examples

Run with the default settings which will create a visualization of the Docker GitHub repository.  
Notice we are exposing port 80, the final video will be served at <http://localhost/>  

```shell
docker run --rm -p 80:80 --name envisaged jamesbrink/envisaged
```

The following example will run a visualization on the Kubernetes GitHub repository.

```shell
docker run --rm -p 80:80 --name envisaged \
       -e GIT_URL=https://github.com/kubernetes/kubernetes.git \
       -e LOGO_URL=https://raw.githubusercontent.com/kubernetes/kubernetes/master/logo/logo.png \
       -e GOURCE_TITLE="Kubernetes Development" \
       jamesbrink/envisaged
```

## Environment Variables

| Variable                   | Default Value                    | Description                                                                                                 |
| -------------------------- | -------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `GIT_URL`                  | `<docker repo on GH>`            | URL of git repository to be cloned and analyzed for visualization.                                          |
| `LOGO_URL`                 | `<docker logo>`                  | URL of logo to be overlayed in lower right hand corner of video.                                            |
| `H264_PRESET`              | ultrafast                        | h.264 encoding preset. refer to [FFmpeg's wiki][ffmpeg].                                                    |
| `H264_CRF`                 | `23`                             | The Constant Rate Factor (CRF) is the default quality for h.264 encoding. refer to [FFmpeg's wiki][ffmpeg]. |
| `H264_LEVEL`               | `5.1`                            | h.264 encoding level. Refer to [FFmpeg's wiki][ffmpeg].                                                     |
| `GOURCE_TITLE`             | `Software Development`           | Title to be displayed in the lower left hand corner of video.                                               |
| `OVERLAY_FONT_COLOR`       | `0f5ca8`                         | Font color to be used on the overlay (Date only).                                                           |
| `GOURCE_CAMERA_MODE`       | `overview`                       | Camera mode (overview, track).                                                                              |
| `GOURCE_SECONDS_PER_DAY`   | `0.1`                            | Speed of simulation in seconds per day.                                                                     |
| `GOURCE_TIME_SCALE`        | `1.5`                            | Change simulation time scale.                                                                               |
| `GOURCE_USER_SCALE`        | `1.5`                            | Change scale of user avatars.                                                                               |
| `GOURCE_AUTO_SKIP_SECONDS` | `0.5`                            | Skip to next entry if nothing happens for a number of seconds.                                              |
| `GOURCE_BACKGROUND_COLOR`  | `000000`                         | Background color in hex.                                                                                    |
| `GOURCE_TEXT_COLOR`        | `FFFFFF`                         | **Not Implemented.**                                                                                        |
| `GOURCE_HIDE_ITEMS`        | `usernames,mouse,date,filenames` | Hide one or more display elements                                                                           |
| `GOURCE_FONT_SIZE`         | `48`                             | **Not Implemented.**                                                                                        |
| `GOURCE_DIR_DEPTH`         | `3`                              | Draw names of directories down to a specific depth in the tree.                                             |
| `GOURCE_FILENAME_TIME`     | `2`                              | Duration to keep filenames on screen (>= 2.0).                                                              |
| `GOURCE_MAX_USER_SPEED`    | `500`                            | Max speed users can travel per second.                                                                      |

[alpine linux image]: https://github.com/gliderlabs/docker-alpine

[gource]: https://github.com/acaudwell/Gource

[ffmpeg_home]: https://www.ffmpeg.org/

[xvfb]: https://www.x.org/archive/X11R7.6/doc/man/man1/Xvfb.1.xhtml

[mesa]: https://www.mesa3d.org/llvmpipe.html

[ffmpeg]: https://trac.ffmpeg.org/wiki/Encode/H.264

[jamesbrink/gource]: https://github.com/jamesbrink/docker-gource
