import os
import subprocess
import argparse
import logging
import time
import shutil # For rmtree

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# APP_HTML_DIR removed

DEFAULT_VIDEO_RESOLUTION = "1280x720"
DEFAULT_VIDEO_FRAMERATE = "25"
DEFAULT_VIDEO_BITRATE = "5M" # Default to 5 Mbps

# GOURCE_LOG_FILE is always in CWD relative to where envisaged.py is run
GOURCE_LOG_FILE = "development.log"
# TMP_DIR is always in CWD for pipes
TMP_DIR = "./tmp"


def fetch_env_variables():
    """Fetches environment variables and returns them as a dictionary."""
    vis_dir = os.environ.get("VISUALIZATION_DIR", "/visualization")

    config_vars = {
        "VISUALIZATION_DIR": vis_dir,
        "VIDEO_DIR": os.path.join(vis_dir, "video"),
        # "HTML_DIR": os.path.join(vis_dir, "html"), # Removed
        "GIT_REPO_DIR": os.path.join(vis_dir, "git_repo"), # For single repo
        "GIT_REPOS_DIR": os.path.join(vis_dir, "git_repos"), # For multiple repos
        "AVATAR_DIR": os.path.join(vis_dir, "avatars"), # Default path for avatars if GOURCE_USER_IMAGE_DIR not set

        "GIT_URL": os.environ.get("GIT_URL"),
        "LOGO_URL": os.environ.get("LOGO_URL"),
        "VIDEO_RESOLUTION": os.environ.get("VIDEO_RESOLUTION", DEFAULT_VIDEO_RESOLUTION),
        "VIDEO_FRAMERATE": os.environ.get("VIDEO_FRAMERATE", DEFAULT_VIDEO_FRAMERATE),
        "VIDEO_BITRATE": os.environ.get("VIDEO_BITRATE", DEFAULT_VIDEO_BITRATE),
        "GOURCE_USER_SCALE": os.environ.get("GOURCE_USER_SCALE", "1.0"),
        "GOURCE_CAMERA_MODE": os.environ.get("GOURCE_CAMERA_MODE"),
        "GOURCE_SECONDS_PER_DAY": os.environ.get("GOURCE_SECONDS_PER_DAY", "0.1"),
        "GOURCE_AUTO_SKIP_SECONDS": os.environ.get("GOURCE_AUTO_SKIP_SECONDS", "0.1"),
        "GOURCE_FILE_IDLE_TIME": os.environ.get("GOURCE_FILE_IDLE_TIME", "0"),
        "GOURCE_MAX_FILES": os.environ.get("GOURCE_MAX_FILES", "0"),
        "GOURCE_TITLE": os.environ.get("GOURCE_TITLE"),
        "GOURCE_FONT_SIZE": os.environ.get("GOURCE_FONT_SIZE", "20"),
        "GOURCE_FONT_COLOUR": os.environ.get("GOURCE_FONT_COLOUR", "FFFFFF"),
        "GOURCE_HIDE_ITEMS": os.environ.get("GOURCE_HIDE_ITEMS"),
        "GOURCE_BACKGROUND_COLOUR": os.environ.get("GOURCE_BACKGROUND_COLOUR", "000000"),
        "GOURCE_LOGO": os.environ.get("GOURCE_LOGO"),
        "GOURCE_START_DATE": os.environ.get("GOURCE_START_DATE"),
        "GOURCE_STOP_DATE": os.environ.get("GOURCE_STOP_DATE"),
        "GOURCE_ELASTICITY": os.environ.get("GOURCE_ELASTICITY", "0.0"),
        "GOURCE_USER_FRICTION": os.environ.get("GOURCE_USER_FRICTION", "0.2"),
        "GOURCE_PADDING": os.environ.get("GOURCE_PADDING", "1.0"),
        "GOURCE_USER_IMAGE_DIR": os.environ.get("GOURCE_USER_IMAGE_DIR", os.path.join(vis_dir, "avatars")), # Actual used path for avatars
        "H264_PRESET": os.environ.get("H264_PRESET", "medium"),
        "H264_CRF": os.environ.get("H264_CRF", "23"),
        "TEMPLATE": os.environ.get("TEMPLATE", "none"),
        "TEMPLATE_FILE": os.environ.get("TEMPLATE_FILE"),
    }
    video_res_parts = config_vars["VIDEO_RESOLUTION"].split('x')
    config_vars["XVFB_WHD"] = os.environ.get("XVFB_WHD", f"{video_res_parts[0]}x{video_res_parts[1]}x24")

    logging.info("--- Configuration ---")
    for key, value in config_vars.items():
        logging.info(f"{key}: {value if value is not None else 'Not set (using default or Gource/FFmpeg default)'}")
    logging.info("---------------------")
    return config_vars

xvfb_process = None

def start_xvfb(config_vars):
    """Starts Xvfb."""
    global xvfb_process
    whd_parts = config_vars["XVFB_WHD"].split('x')
    if len(whd_parts) == 2:
        xvfb_whd = f"{config_vars['XVFB_WHD']}x24"
    elif len(whd_parts) == 3:
        xvfb_whd = config_vars["XVFB_WHD"]
    else:
        logging.error(f"Invalid XVFB_WHD format: {config_vars['XVFB_WHD']}. Using default 1280x720x24")
        xvfb_whd = "1280x720x24"

    display = os.environ.get("DISPLAY", ":99")
    command = ["Xvfb", display, "-ac", "-screen", "0", xvfb_whd, "-nolisten", "tcp"]
    logging.info(f"Starting Xvfb with command: {' '.join(command)}")
    try:
        xvfb_process = subprocess.Popen(command)
        logging.info(f"Xvfb started with PID: {xvfb_process.pid}")
        time.sleep(2)
    except FileNotFoundError:
        logging.error("Xvfb command not found. Please ensure Xvfb is installed and in your PATH.")
        raise
    except Exception as e:
        logging.error(f"Failed to start Xvfb: {e}")
        raise

def stop_xvfb():
    """Stops Xvfb if it's running."""
    global xvfb_process
    if xvfb_process:
        logging.info(f"Stopping Xvfb (PID: {xvfb_process.pid})...")
        try:
            xvfb_process.terminate()
            xvfb_process.wait(timeout=5)
            logging.info("Xvfb terminated.")
        except subprocess.TimeoutExpired:
            logging.warning("Xvfb did not terminate gracefully, killing...")
            xvfb_process.kill()
            xvfb_process.wait()
            logging.info("Xvfb killed.")
        except Exception as e:
            logging.error(f"Error stopping Xvfb: {e}")
        xvfb_process = None

def run_command(command, cwd=None, check=True, env=None):
    """Helper function to run a shell command."""
    logging.info(f"Running command: {' '.join(command)} {'in ' + cwd if cwd else ''}")
    try:
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        result = subprocess.run(command, capture_output=True, text=True, check=check, cwd=cwd, env=process_env)
        if result.stdout:
            logging.info(f"Command stdout: {result.stdout.strip()}")
        if result.stderr:
            logging.info(f"Command stderr: {result.stderr.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        logging.error(f"Stdout: {e.stdout}")
        logging.error(f"Stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        logging.error(f"Command not found: {command[0]}. Please ensure it is installed and in PATH.")
        raise

def handle_logo(config_vars):
    """
    Downloads and processes a logo if LOGO_URL is provided.
    Returns a dictionary with FFmpeg options for the logo.
    """
    logo_options = {
        "logo_input_option": "",
        "logo_filter_graph_segment": "",
        "filter_graph_map_option": "-map [final_video]",
    }
    logo_path = "./logo.image"

    if config_vars.get("LOGO_URL"):
        logging.info(f"Processing logo from URL: {config_vars['LOGO_URL']}")
        try:
            run_command(["wget", "-O", logo_path, config_vars["LOGO_URL"]])
            run_command(["convert", logo_path, "-geometry", "x160", logo_path])

            if os.path.exists(logo_path) and os.path.getsize(logo_path) > 0:
                logging.info(f"Logo downloaded and resized to {logo_path}")
                logo_options["logo_input_option"] = f"-i {logo_path}"

                template_type = config_vars.get("TEMPLATE", "none")
                if template_type == 'border':
                    logo_options["logo_filter_graph_segment"] = \
                        "[1:v] scale=w=-1:h=ih*0.1 [logo_scaled];" \
                        "[final_video][logo_scaled] overlay=W-w-10:10 [video_with_logo_overlay]"
                    logo_options["filter_graph_map_option"] = "-map [video_with_logo_overlay]"
                else:
                    logo_options["logo_filter_graph_segment"] = \
                        "[1:v] scale=w=-1:h=ih*0.08 [logo_scaled];" \
                        "[final_video][logo_scaled] overlay=W-w-10:H-h-10 [video_with_logo_overlay]"
                    logo_options["filter_graph_map_option"] = "-map [video_with_logo_overlay]"
            else:
                logging.warning("Logo download or processing failed. Continuing without logo overlay.")
                logo_options["logo_input_option"] = ""
                logo_options["logo_filter_graph_segment"] = ""
                if config_vars.get("TEMPLATE", "none") == 'border':
                    logo_options["filter_graph_map_option"] = "-map [with_date]"
                else:
                    logo_options["filter_graph_map_option"] = "-map [final_video]"

        except Exception as e:
            logging.error(f"Error processing logo: {e}. Continuing without logo overlay.")
            logo_options["logo_input_option"] = ""
            logo_options["logo_filter_graph_segment"] = ""
            if config_vars.get("TEMPLATE", "none") == 'border':
                logo_options["filter_graph_map_option"] = "-map [with_date]"
            else:
                logo_options["filter_graph_map_option"] = "-map [final_video]"
    else:
        logging.info("No LOGO_URL provided. Skipping logo processing.")
        if config_vars.get("TEMPLATE", "none") == 'border':
            logo_options["filter_graph_map_option"] = "-map [with_date]"

    logging.info(f"Logo options: {logo_options}")
    return logo_options

def create_named_pipes(pipe_names):
    """Creates named pipes in the TMP_DIR."""
    os.makedirs(TMP_DIR, exist_ok=True)
    for pipe_name in pipe_names:
        pipe_path = os.path.join(TMP_DIR, pipe_name)
        if os.path.exists(pipe_path):
            os.remove(pipe_path)
        try:
            os.mkfifo(pipe_path)
            logging.info(f"Created named pipe: {pipe_path}")
        except OSError as e:
            logging.error(f"Failed to create named pipe {pipe_path}: {e}")
            raise

def prepare_gource_log(config_vars):
    """
    Prepares the Gource custom log file (development.log).
    Uses GIT_REPO_DIR and GIT_REPOS_DIR from config_vars.
    """
    os.makedirs(config_vars["GIT_REPOS_DIR"], exist_ok=True)
    os.makedirs(config_vars["GIT_REPO_DIR"], exist_ok=True)

    log_files_to_merge = []
    processed_repo_paths = set()

    if os.path.exists(config_vars["GIT_REPOS_DIR"]) and any(entry.is_dir() for entry in os.scandir(config_vars["GIT_REPOS_DIR"])):
        logging.info(f"Multiple repository mode: processing subdirectories in {config_vars['GIT_REPOS_DIR']}")
        for item in os.scandir(config_vars["GIT_REPOS_DIR"]):
            if item.is_dir():
                repo_path = os.path.realpath(item.path)
                if repo_path in processed_repo_paths:
                    logging.info(f"Skipping already processed repository path: {repo_path}")
                    continue

                repo_name = item.name
                repo_log_file_path_in_cwd = f"{repo_name}.log"
                logging.info(f"Processing repository: {repo_name} at {repo_path}")

                gource_cmd = ["gource", "--output-custom-log", repo_log_file_path_in_cwd, repo_path]
                if config_vars.get("GOURCE_START_DATE"): gource_cmd.extend(["--start-date", config_vars["GOURCE_START_DATE"]])
                if config_vars.get("GOURCE_STOP_DATE"): gource_cmd.extend(["--stop-date", config_vars["GOURCE_STOP_DATE"]])

                run_command(gource_cmd)

                temp_log_path = repo_log_file_path_in_cwd + ".tmp"
                with open(repo_log_file_path_in_cwd, "r") as infile, open(temp_log_path, "w") as outfile:
                    for line in infile:
                        if "|" in line and not line.startswith("gource"):
                            parts = line.split("|", 1)
                            outfile.write(f"{parts[0]}|/{repo_name}|{parts[1]}")
                        else:
                            outfile.write(line)
                os.replace(temp_log_path, repo_log_file_path_in_cwd)
                logging.info(f"Prepended '{repo_name}' to paths in {repo_log_file_path_in_cwd}")
                log_files_to_merge.append(repo_log_file_path_in_cwd)
                processed_repo_paths.add(repo_path)

        if log_files_to_merge:
            logging.info(f"Merging log files: {log_files_to_merge}")
            all_log_lines = []
            for log_file_path_in_cwd in log_files_to_merge: # Corrected variable name
                with open(log_file_path_in_cwd, "r") as f:
                    all_log_lines.extend(f.readlines())
                os.remove(log_file_path_in_cwd)

            all_log_lines.sort(key=lambda line: int(line.split("|")[0]) if "|" in line and line.split("|")[0].isdigit() else 0)

            with open(GOURCE_LOG_FILE, "w") as outfile:
                outfile.writelines(all_log_lines)
            logging.info(f"Successfully merged {len(log_files_to_merge)} log files into {GOURCE_LOG_FILE}")
            return

    repo_to_log = None
    if config_vars.get("GIT_URL"):
        git_repo_path = config_vars["GIT_REPO_DIR"]
        is_dot_git_present = os.path.exists(os.path.join(git_repo_path, ".git"))
        dir_contents = os.listdir(git_repo_path) if os.path.exists(git_repo_path) else []
        is_effectively_empty = not dir_contents or \
                               (len(dir_contents) == 1 and dir_contents[0] == ".git" and \
                                (not os.listdir(os.path.join(git_repo_path, ".git")) if os.path.isdir(os.path.join(git_repo_path, ".git")) else True))

        if is_effectively_empty or not is_dot_git_present:
            if not is_effectively_empty:
                 logging.info(f"Cleaning directory {git_repo_path} before cloning...")
                 for item_name in dir_contents:
                     full_item_path = os.path.join(git_repo_path, item_name)
                     if os.path.isfile(full_item_path) or os.path.islink(full_item_path):
                         os.remove(full_item_path)
                     elif os.path.isdir(full_item_path):
                         shutil.rmtree(full_item_path)

            logging.info(f"Cloning from {config_vars['GIT_URL']} into {git_repo_path}...")
            run_command(["git", "clone", "--depth", "1", "--no-single-branch", config_vars["GIT_URL"], "."], cwd=git_repo_path)
            logging.info(f"Successfully cloned {config_vars['GIT_URL']} into {git_repo_path}")
            repo_to_log = git_repo_path
        else:
            logging.info(f"Using existing repository in {git_repo_path} (populated by GIT_URL or mount)")
            repo_to_log = git_repo_path
    elif os.path.exists(config_vars["GIT_REPO_DIR"]) and any(os.scandir(config_vars["GIT_REPO_DIR"])):
         logging.info(f"Using existing repository in {config_vars['GIT_REPO_DIR']} (assumed to be a mounted volume or pre-populated).")
         repo_to_log = config_vars["GIT_REPO_DIR"]

    if repo_to_log:
        gource_cmd = ["gource", "--output-custom-log", GOURCE_LOG_FILE, repo_to_log]
        if config_vars.get("GOURCE_START_DATE"): gource_cmd.extend(["--start-date", config_vars["GOURCE_START_DATE"]])
        if config_vars.get("GOURCE_STOP_DATE"): gource_cmd.extend(["--stop-date", config_vars["GOURCE_STOP_DATE"]])

        run_command(gource_cmd)
        logging.info(f"Gource log generated for single repository at {GOURCE_LOG_FILE}")
    else:
        logging.warning(f"No valid repository found in {config_vars['GIT_REPOS_DIR']} or {config_vars['GIT_REPO_DIR']}, and no GIT_URL provided.")
        if os.path.exists(GOURCE_LOG_FILE):
            logging.info(f"Using existing Gource log file: {GOURCE_LOG_FILE} (possibly mounted).")
        else:
            logging.error(f"{GOURCE_LOG_FILE} not found and could not be generated. Video generation will likely fail.")
            with open(GOURCE_LOG_FILE, 'w') as f: pass
            logging.info(f"Created empty {GOURCE_LOG_FILE} to satisfy Gource/FFmpeg input requirement.")

def get_gource_base_command(config_vars, output_target, resolution_str=None):
    """Constructs the base Gource command list with common options."""
    cmd = ["gource", GOURCE_LOG_FILE]

    if output_target == "pipe": cmd.extend(["-o", "-"])
    elif output_target: cmd.extend(["-o", output_target])
    if resolution_str: cmd.extend([f"--{resolution_str}"])

    if config_vars.get("GOURCE_CAMERA_MODE"): cmd.extend(["--camera-mode", config_vars["GOURCE_CAMERA_MODE"]])
    if config_vars.get("GOURCE_SECONDS_PER_DAY"): cmd.extend(["--seconds-per-day", config_vars["GOURCE_SECONDS_PER_DAY"]])
    if config_vars.get("GOURCE_AUTO_SKIP_SECONDS"): cmd.extend(["--auto-skip-seconds", config_vars["GOURCE_AUTO_SKIP_SECONDS"]])
    if config_vars.get("GOURCE_FILE_IDLE_TIME"): cmd.extend(["--file-idle-time", config_vars["GOURCE_FILE_IDLE_TIME"]])
    if config_vars.get("GOURCE_MAX_FILES"): cmd.extend(["--max-files", config_vars["GOURCE_MAX_FILES"]])
    if config_vars.get("GOURCE_TITLE"): cmd.extend(["--title", config_vars["GOURCE_TITLE"]])
    if config_vars.get("GOURCE_FONT_SIZE"): cmd.extend(["--font-size", config_vars["GOURCE_FONT_SIZE"]])
    if config_vars.get("GOURCE_FONT_COLOUR"): cmd.extend(["--font-colour", config_vars["GOURCE_FONT_COLOUR"]])
    if config_vars.get("GOURCE_HIDE_ITEMS"): cmd.extend(["--hide", config_vars["GOURCE_HIDE_ITEMS"]])
    if config_vars.get("GOURCE_BACKGROUND_COLOUR"): cmd.extend(["--background-colour", config_vars["GOURCE_BACKGROUND_COLOUR"]])
    if config_vars.get("GOURCE_LOGO") and not config_vars.get("LOGO_URL"): cmd.extend(["--logo", config_vars["GOURCE_LOGO"]])
    if config_vars.get("GOURCE_START_DATE"): cmd.extend(["--start-date", config_vars["GOURCE_START_DATE"]])
    if config_vars.get("GOURCE_STOP_DATE"): cmd.extend(["--stop-date", config_vars["GOURCE_STOP_DATE"]])
    if config_vars.get("GOURCE_ELASTICITY"): cmd.extend(["--elasticity", config_vars["GOURCE_ELASTICITY"]])
    if config_vars.get("GOURCE_USER_FRICTION"): cmd.extend(["--user-friction", config_vars["GOURCE_USER_FRICTION"]])
    if config_vars.get("GOURCE_USER_SCALE"): cmd.extend(["--user-scale", config_vars["GOURCE_USER_SCALE"]])
    if config_vars.get("GOURCE_PADDING"): cmd.extend(["--padding", config_vars["GOURCE_PADDING"]])
    if config_vars.get("GOURCE_USER_IMAGE_DIR") and os.path.exists(config_vars["GOURCE_USER_IMAGE_DIR"]):
        cmd.extend(["--user-image-dir", config_vars["GOURCE_USER_IMAGE_DIR"]])

    if os.environ.get("GOURCE_ARGS"):
        cmd.extend(os.environ.get("GOURCE_ARGS").split())
    return cmd

def execute_none_template(config_vars, logo_options, common_env):
    """Executes the 'none' template (direct Gource to FFmpeg)."""
    logging.info("Executing 'none' template.")
    pipe_names = ["gource.pipe"]
    create_named_pipes(pipe_names)
    gource_pipe_path = os.path.join(TMP_DIR, pipe_names[0])

    gource_res_str = f"--{config_vars['VIDEO_RESOLUTION']}"
    gource_cmd = get_gource_base_command(config_vars, "-", resolution_str=gource_res_str)

    logging.info(f"Starting Gource for 'none' template: {' '.join(gource_cmd)}")
    gource_process = subprocess.Popen(gource_cmd, stdout=open(gource_pipe_path, "wb"), env=common_env)

    ffmpeg_input_options = ["-r", config_vars["VIDEO_FRAMERATE"], "-f", "image2pipe", "-vcodec", "ppm", "-i", gource_pipe_path]
    if logo_options.get("logo_input_option"):
        ffmpeg_input_options.extend(logo_options["logo_input_option"].split())

    output_video_path = os.path.join(config_vars["VIDEO_DIR"], "output.mp4")

    filter_complex_parts = []
    current_input_label = "[0:v]"

    if config_vars.get("GOURCE_FILTERS"):
        filter_complex_parts.append(f"{current_input_label} {config_vars['GOURCE_FILTERS']} [filtered_gource]")
        current_input_label = "[filtered_gource]"

    filter_complex_parts.append(f"{current_input_label} format=yuv420p [final_video]")

    if logo_options.get("logo_filter_graph_segment"):
        filter_complex_parts.append(logo_options["logo_filter_graph_segment"])

    if config_vars.get("GLOBAL_FILTERS"):
        pre_global_stream_label = logo_options["filter_graph_map_option"].split(" ")[1]
        filter_complex_parts.append(f"{pre_global_stream_label} {config_vars['GLOBAL_FILTERS']} [final_output_video]")
        ffmpeg_map_option = ["-map", "[final_output_video]"]
    else:
        ffmpeg_map_option = logo_options["filter_graph_map_option"].split()

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        *ffmpeg_input_options,
        "-c:v", "libx264",
        "-preset", config_vars["H264_PRESET"],
        "-crf", config_vars["H264_CRF"],
        "-level:v", "4.1",
        "-pix_fmt", "yuv420p",
        "-r", config_vars["VIDEO_FRAMERATE"],
        "-b:v", config_vars["VIDEO_BITRATE"],
        "-maxrate", config_vars["VIDEO_BITRATE"],
        "-bufsize", str(int(config_vars["VIDEO_BITRATE"].replace("M","")) * 2) + "M",
    ]
    if filter_complex_parts:
         ffmpeg_cmd.extend(["-filter_complex", "; ".join(filter_complex_parts)])

    ffmpeg_cmd.extend(ffmpeg_map_option)
    ffmpeg_cmd.append(output_video_path)

    logging.info(f"Starting FFmpeg for 'none' template: {' '.join(ffmpeg_cmd)}")
    run_command(ffmpeg_cmd, env=common_env)

    gource_process.wait()
    if gource_process.returncode != 0:
        logging.warning(f"Gource process exited with code: {gource_process.returncode}")
    logging.info("'none' template execution finished.")

def execute_border_template(config_vars, logo_options, common_env):
    """Executes the 'border' template (complex Gource/FFmpeg with overlays)."""
    logging.info("Executing 'border' template.")
    pipe_names = ["gource_main.pipe", "gource_overlay.pipe"]
    create_named_pipes(pipe_names)
    gource_main_pipe_path = os.path.join(TMP_DIR, pipe_names[0])
    gource_overlay_pipe_path = os.path.join(TMP_DIR, pipe_names[1])

    main_w, main_h = map(int, config_vars["VIDEO_RESOLUTION"].split('x'))

    gource_w = main_w - (main_w // 6)
    gource_h = main_h
    overlay_w = main_w // 6
    overlay_h = main_h // 2

    gource_w = (gource_w // 2) * 2
    overlay_w = (overlay_w // 2) * 2

    gource_res_str = f"{gource_w}x{gource_h}"
    overlay_res_str = f"{overlay_w}x{overlay_h}"

    gource_main_cmd = get_gource_base_command(config_vars, "-", resolution_str=gource_res_str)
    if not config_vars.get("GOURCE_TITLE"):
        gource_main_cmd.extend(["--title", "Main Gource Feed"])

    logging.info(f"Starting main Gource for 'border' template: {' '.join(gource_main_cmd)}")
    gource_main_process = subprocess.Popen(gource_main_cmd, stdout=open(gource_main_pipe_path, "wb"), env=common_env)

    gource_overlay_cmd = get_gource_base_command(config_vars, "-", resolution_str=overlay_res_str)
    gource_overlay_cmd = [cmd_part for cmd_part in gource_overlay_cmd if not cmd_part.startswith(('--title', '--logo'))]
    gource_overlay_cmd.extend([
        "--no-logo", "--transparent",
        "--font-size", str(max(10, int(overlay_h * 0.8) // 10)),
        "--fixed-user-size", "--hide", "bloom,filenames,dirnames,avatars",
        "--date-format", config_vars.get("GOURCE_DATE_FORMAT", "%Y-%m-%d %H:%M"),
        "--title", " "
    ])

    logging.info(f"Starting overlay Gource for 'border' template: {' '.join(gource_overlay_cmd)}")
    gource_overlay_process = subprocess.Popen(gource_overlay_cmd, stdout=open(gource_overlay_pipe_path, "wb"), env=common_env)

    output_video_path = os.path.join(config_vars["VIDEO_DIR"], "output.mp4")

    ffmpeg_input_options = [
        "-r", config_vars["VIDEO_FRAMERATE"], "-f", "image2pipe", "-vcodec", "ppm", "-i", gource_main_pipe_path,
        "-r", config_vars["VIDEO_FRAMERATE"], "-f", "image2pipe", "-vcodec", "ppm", "-i", gource_overlay_pipe_path,
    ]
    if logo_options.get("logo_input_option"):
        ffmpeg_input_options.extend(logo_options["logo_input_option"].split())

    filter_complex = (
        f"[1:v] pad=w={overlay_w}:h={main_h}:x=0:y=0:color=black@0.0 [overlay_padded]; "
        f"[overlay_padded] crop=w={overlay_w}:h={main_h}:x=0:y=0 [overlay_final]; "
        f"[0:v][overlay_final] hstack=inputs=2 [combined_video]; "
        f"[combined_video] drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='%{{localtime\\:%Y-%m-%d %H\\:%M\\:%S}}':"
        f"x=W-tw-10:y=H-th-10:fontsize={main_h // 30}:fontcolor=white@0.8:box=1:boxcolor=black@0.5 [with_date];"
    )

    current_stream_label = "[with_date]"

    if config_vars.get("GOURCE_FILTERS"):
        filter_complex += f" {current_stream_label} {config_vars['GOURCE_FILTERS']} [filtered_gource_video];"
        current_stream_label = "[filtered_gource_video]"

    filter_complex += f" {current_stream_label} format=yuv420p [final_video];"

    final_map_option = logo_options["filter_graph_map_option"].split()

    if logo_options.get("logo_filter_graph_segment"):
        logo_segment = logo_options["logo_filter_graph_segment"]
        if logo_options["logo_input_option"] and ffmpeg_input_options.count("-i") > 2:
            logo_segment = logo_segment.replace("[1:v]", "[2:v]")
        filter_complex += f" {logo_segment}"

    if config_vars.get("GLOBAL_FILTERS"):
        pre_global_stream_label = final_map_option[1]
        filter_complex += f" {pre_global_stream_label} {config_vars['GLOBAL_FILTERS']} [final_output_video];"
        final_map_option = ["-map", "[final_output_video]"]

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        *ffmpeg_input_options,
        "-filter_complex", filter_complex,
        *final_map_option,
        "-c:v", "libx264",
        "-preset", config_vars["H264_PRESET"],
        "-crf", config_vars["H264_CRF"],
        "-level:v", "4.1",
        "-pix_fmt", "yuv420p",
        "-r", config_vars["VIDEO_FRAMERATE"],
        "-b:v", config_vars["VIDEO_BITRATE"],
        "-maxrate", config_vars["VIDEO_BITRATE"],
        "-bufsize", str(int(config_vars["VIDEO_BITRATE"].replace("M","")) * 2) + "M",
        output_video_path,
    ]

    logging.info(f"Starting FFmpeg for 'border' template: {' '.join(ffmpeg_cmd)}")
    run_command(ffmpeg_cmd, env=common_env)

    gource_main_process.wait()
    gource_overlay_process.wait()
    if gource_main_process.returncode != 0:
        logging.warning(f"Main Gource process exited with code: {gource_main_process.returncode}")
    if gource_overlay_process.returncode != 0:
        logging.warning(f"Overlay Gource process exited with code: {gource_overlay_process.returncode}")
    logging.info("'border' template execution finished.")

def run_visualization(config_vars, logo_options):
    """Runs the Gource and FFmpeg processes based on the selected template."""
    os.makedirs(config_vars["VIDEO_DIR"], exist_ok=True)
    # os.makedirs(config_vars["HTML_DIR"], exist_ok=True) # Removed: HTML_DIR no longer created by script if not for output

    common_env = os.environ.copy()
    common_env["DISPLAY"] = os.environ.get("DISPLAY", ":99")

    template_type = config_vars.get("TEMPLATE", "none")
    logging.info(f"Selected template: {template_type}")

    if template_type == "border":
        execute_border_template(config_vars, logo_options, common_env)
    else:
        if template_type != "none":
            logging.warning(f"Unknown template '{template_type}', defaulting to 'none'.")
        execute_none_template(config_vars, logo_options, common_env)

# format_filesize and finalize_video functions are removed.

def main():
    config_vars = fetch_env_variables()
    try:
        start_xvfb(config_vars)
        prepare_gource_log(config_vars)
        logo_options = handle_logo(config_vars)
        run_visualization(config_vars, logo_options)
        # finalize_video(config_vars) # Call removed
        logging.info(f"Video generation complete. Output available at: {config_vars['VIDEO_DIR']}/output.mp4") # New log message
    except Exception as e:
        logging.error(f"An critical error occurred during the script execution: {e}", exc_info=True)
    finally:
        stop_xvfb()
        if os.path.exists(TMP_DIR):
            try:
                shutil.rmtree(TMP_DIR)
                logging.info(f"Cleaned up temporary directory: {TMP_DIR}")
            except Exception as e:
                logging.warning(f"Could not clean up temporary directory {TMP_DIR}: {e}")
        logging.info("Xvfb stopped. Script finished.")

if __name__ == "__main__":
    main()
