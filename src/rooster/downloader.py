import os
import re
from urllib.parse import urlparse
import requests
import yt_dlp
from .channels import get_channel_name_from_id
from .shows import get_show_name_from_id


def make_filename_safe(input_string):
    char_mappings = {
        "/": "∕",
        "*": "＊",
        "?": "？",
        '"': "“",
        "<": "＜",
        ">": "＞",
        "|": "⏐",
    }
    safe_string = input_string
    for char, replacement in char_mappings.items():
        safe_string = safe_string.replace(char, replacement)

    return safe_string


def is_tool(name):
    """Check whether `name` is on PATH and marked as executable."""
    from shutil import which

    return which(name) is not None


def get_download_location():
    script_location = os.getcwd()
    download_location = os.path.join(
        script_location, "Downloads"
    )  # Replace "downloads" with your desired folder name

    if not os.path.exists(download_location):
        os.makedirs(download_location)

    return download_location


def generate_file_name(data):
    return f"{data['original_air_date']} - {data['channel_title']} - {data['show_title']} - {data['display_title']} ({data['id_numerical']})"


def downloader(username, password, vod_url, episode_data):
    video_options = {
        "username": username,
        "password": password,
        "forcejson": False,
        "writeinfojson": True,
        "writedescription": True,
        "writethumbnail": True,
        "nooverwrites": True,
        "merge_output_format": "mp4",
        # "progress_hooks": [ydl_progress_hook],
    }
    ## use aria2c if it exists in system
    if is_tool("aria2c"):
        video_options["external_downloader"] = "aria2c"
        video_options["external_downloader_args"] = [
            "-j 16",
            " -x 16",
            "-s 16",
            " -k 1M",
        ]
    else:
        print("aria2c not found, skipping.")

    if episode_data is False:
        print("Use yt-dlp's output")
        # todo

    file_name = generate_file_name(episode_data)
    dl_location = get_download_location()

    name_with_extension = file_name + "/" + file_name + ".%(ext)s"
    full_name_with_dir = os.path.join(dl_location, name_with_extension)
    video_options["outtmpl"] = full_name_with_dir
    # yt_dlp.utils.std_headers["Referer"] = link

    # pass off to yt-dlp for downloading
    print("Starting download: ", full_name_with_dir)
    yt_dlp.YoutubeDL(video_options).download(vod_url)


def get_api_url(url):
    parsed_url = urlparse(url)
    slug = parsed_url.path.rstrip("/").split("/")[-1]
    api_url = f"https://svod-be.roosterteeth.com/api/v1/watch/{slug}"
    return api_url


def get_episode_data_from_api(url):
    response = requests.get(url)
    if response.status_code == 200:
        episode_data = response.json().get("data", [])
        if episode_data:
            episode_obj = episode_data[0]
            episode_id = episode_obj.get("id")

            episode_type = episode_obj.get("type")
            attributes = episode_obj.get("attributes", {})
            display_title = make_filename_safe(attributes.get("display_title"))
            channel_id = attributes.get("channel_id")
            original_air_date_full = attributes.get("original_air_date", "")
            is_first_content = attributes.get("is_sponsors_only")
            show_id = show_title = attributes.get("show_id")
            show_title = make_filename_safe(get_show_name_from_id(show_id))

            original_air_date = (
                original_air_date_full.split("T")[0]
                if "T" in original_air_date_full
                else None
            )
            channel_title = make_filename_safe(get_channel_name_from_id(channel_id))

            # Return or use the extracted values as needed
            return {
                "id_numerical": episode_id,
                "display_title": display_title,
                "original_air_date": original_air_date,
                "show_title": show_title,
                "is_first_content": is_first_content,
                "channel_title": channel_title,
            }
        else:
            # write-fallback code via yt_dlp
            return False
            print("Something went wrong with the API, not my problem.")


def show_stuff(username, password, vod_url):
    api_url = get_api_url(url=vod_url)
    episode_data = get_episode_data_from_api(api_url)
    downloader(username, password, vod_url, episode_data)
