import os
import re
import csv
import logging
from urllib.parse import urlparse
import requests
import yt_dlp
from .channels import get_channel_name_from_id
from .shows import get_show_name_from_id


def get_high_quality_thumbnail_link(images):
    for image in images:
        image_type = image.get("type", "")
        if (
            image_type.lower() == "episode_image"
            or image_type.lower() == "bonus_feature_image"
        ):
            attributes = image.get("attributes", {})
            if attributes.get("image_type", "").lower() == "profile":
                image_url = attributes.get("large", "")
                if image_url:
                    return image_url
    return False


def get_archive_log_filename():
    script_location = os.getcwd()
    archive_log_location = os.path.join(script_location, "archive.log")
    return archive_log_location


def get_download_location():
    script_location = os.getcwd()
    download_location = os.path.join(
        script_location, "Downloads"
    )  # Replace "downloads" with your desired folder name

    if not os.path.exists(download_location):
        os.makedirs(download_location)

    return download_location


current_dir = get_download_location()
log_output_file = os.path.join(current_dir, "rooster.log")
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(
    filename=log_output_file,
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def extract_data_from_ytdl_dict(info_dict):
    episode_id = info_dict["id"]
    episode_title = info_dict["title"]
    channel_id = info_dict["channel_id"]
    is_first_content = False if info_dict["availability"] == "public" else True
    channe_title = get_channel_name_from_id(channel_id)
    large_thumbnail_url_ytdl = None

    for thumbnail in info_dict["thumbnails"]:
        if thumbnail["id"] == "large":
            large_thumbnail_url_ytdl = thumbnail["url"]
            break

    return {
        "id_numerical": episode_id,
        "display_title": episode_title,
        "channe_title": channe_title,
        "is_first_content": is_first_content,
        "large_thumbnail_url_ytdl": large_thumbnail_url_ytdl,
    }


def append_to_csv(url, csv_filename="download_history.csv"):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_directory, csv_filename)
    file_exists = os.path.exists(full_path)

    with open(full_path, mode="a", newline="") as file:
        fieldnames = ["roosterteeth_url"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({"url": url})


def make_filename_safe(input_string):
    char_mappings = {
        ":": "꞉",
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


def generate_file_name(data):
    return f"{data['original_air_date']} - {data['channel_title']} - {data['show_title']} - {data['display_title']} ({data['id_numerical']})"


def generate_basic_file_name(data):
    return f"{data['channel_title']} {data['display_title']} [{data['id_numerical']}]"


def download_thumbnail(thumbnail_url, episode_data, show_mode):
    # Ensure the download location exists
    dl_location = get_download_location()
    os.makedirs(dl_location, exist_ok=True)

    # Generate the file name and create the directory
    file_name = generate_file_name(episode_data)
    if show_mode is True:
        file_directory = os.path.join(
            dl_location, episode_data["show_title"], file_name
        )
    else:
        file_directory = os.path.join(dl_location, file_name)
    os.makedirs(file_directory, exist_ok=True)

    if thumbnail_url is not None:  # from yt-dlp data
        file_extension = os.path.splitext(thumbnail_url)[1]
    else:  # from api data
        logging.warning("Downloading thumbnail using fallback method")
        thumbnail_url = episode_data["large_thumb"]
        file_extension = os.path.splitext(thumbnail_url)[1]

    file_path = os.path.join(file_directory, f"{file_name}{file_extension}")

    # Attempt to download
    response = requests.get(thumbnail_url)
    if response.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Large Thumbnail downloaded to: {file_path}")
    else:
        print(f"Failed to download thumbnail from: {thumbnail_url}")


def downloader(
    username, password, vod_url, episode_data, concurrent_fragments, show_mode
):
    video_options = {
        "username": username,
        "password": password,
        "forcejson": False,
        "writeinfojson": True,
        "writedescription": True,
        # "writethumbnail": True,
        "nooverwrites": True,
        "merge_output_format": "mp4",
        "retries": 10,
        "fragment_retries": 10,
        "download_archive": get_archive_log_filename(),
        # "progress_hooks": [ydl_progress_hook],
    }
    extractor_options = {
        "username": username,
        "password": password,
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
        video_options["concurrent_fragment_downloads"] = int(concurrent_fragments)
        print("aria2c not found, skipping.")

    # TODO:
    # why am i calling the info_dict before checking if I have filename
    # data or not? thumbnail infO? idk
    try:
        info_dict = yt_dlp.YoutubeDL(extractor_options).extract_info(
            vod_url, download=False
        )
    except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as err:
        print(err)
        print("Are you sure you are logged in?")
        print("If you are, are you a FIRST member?")
        exit()
    yt_dlp_dict_data = extract_data_from_ytdl_dict(info_dict=info_dict)

    if episode_data is False:
        logging.warning("both api failed, initiating failover")
        file_name = generate_basic_file_name(yt_dlp_dict_data)
        dl_location = get_download_location()
    else:
        file_name = generate_file_name(episode_data)
        dl_location = get_download_location()
        download_thumbnail(
            yt_dlp_dict_data["large_thumbnail_url_ytdl"], episode_data, show_mode
        )

    name_with_extension = file_name + "/" + file_name + ".%(ext)s"

    # if we are in show mode, episode folder will be inside a show folder
    if show_mode is True:
        if episode_data is not False:
            full_name_with_dir = os.path.join(
                dl_location, episode_data["show_title"], name_with_extension
            )
        else:
            logging.warning("show mode True but has Fallback data")
            full_name_with_dir = os.path.join(dl_location, name_with_extension)
    else:
        full_name_with_dir = os.path.join(dl_location, name_with_extension)

    video_options["outtmpl"] = full_name_with_dir

    # pass off to yt-dlp for downloading
    print("Starting download: ", full_name_with_dir)
    try:
        yt_dlp.YoutubeDL(video_options).download(vod_url)
        # append_to_csv(vod_url)
    except:
        logging.warning("Error with yt_dlp downloading")
    # TODO: Append only when done
    # append_to_csv(vod_url)


def get_rt_api_url(url):
    parsed_url = urlparse(url)
    slug = parsed_url.path.rstrip("/").split("/")[-1]
    api_url = f"https://svod-be.roosterteeth.com/api/v1/watch/{slug}"
    return api_url


def get_api_url(url):
    parsed_url = urlparse(url)
    slug = parsed_url.path.rstrip("/").split("/")[-1]
    api_url = f"https://roosterteeth.fhm.workers.dev/findEpisode?slug={slug}"
    return api_url


def get_episode_data_from_api(url):
    base_url = get_api_url(url)
    response = requests.get(base_url)
    if response.status_code == 200:
        episode_data = response.json().get("documents", [])
        if episode_data:
            episode_obj = episode_data[0]
            episode_id = episode_obj.get("id")
            uuid = episode_obj.get("uuid")
            episode_type = episode_obj.get("type")
            attributes = episode_obj.get("attributes", {})
            display_title = make_filename_safe(attributes.get("display_title"))
            channel_id = attributes.get("channel_id")
            season_id = attributes.get("season_id")
            original_air_date_full = attributes.get("original_air_date", "")
            is_first_content = attributes.get("is_sponsors_only")
            show_id = attributes.get("show_id")
            parent_slug = attributes.get("parent_content_slug", "")
            show_title = make_filename_safe(get_show_name_from_id(show_id))
            if season_id:
                large_thumb = f"https://cdn.ffaisal.com/thumbnail/{show_id}/{season_id}/{uuid}.jpg"
            else:
                large_thumb = f"https://cdn.ffaisal.com/thumbnail/{show_id}/bonus-content-{parent_slug}/{uuid}.jpg"

            original_air_date = (
                original_air_date_full.split("T")[0]
                if "T" in original_air_date_full
                else None
            )
            channel_title = make_filename_safe(get_channel_name_from_id(channel_id))

            return {
                "id_numerical": episode_id,
                "display_title": display_title,
                "original_air_date": original_air_date,
                "show_title": show_title,
                "is_first_content": is_first_content,
                "channel_title": channel_title,
                "large_thumb": large_thumb,
            }
        else:
            # write-fallback code via ytdlp info dict
            return False


def get_episode_data_from_rt_api(url):
    response = requests.get(url)
    if response.status_code == 200:
        episode_data = response.json().get("data", [])
        if episode_data:
            episode_obj = episode_data[0]
            episode_id = episode_obj.get("id")
            images = episode_obj.get("included", {}).get("images", [])
            large_thumb = get_high_quality_thumbnail_link(images)

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

            return {
                "id_numerical": episode_id,
                "display_title": display_title,
                "original_air_date": original_air_date,
                "show_title": show_title,
                "is_first_content": is_first_content,
                "channel_title": channel_title,
                "large_thumb": large_thumb,
            }
        else:
            # go to fallback data fetch via my api
            return False


def show_stuff(username, password, vod_url, concurrent_fragments, show_mode):
    if not is_tool("ffmpeg"):
        print("ffmpeg not installed, go do that")
        exit()
    api_url = get_rt_api_url(url=vod_url)
    episode_data = get_episode_data_from_rt_api(api_url)
    if episode_data is False:
        episode_data = get_episode_data_from_api(vod_url)
    downloader(
        username, password, vod_url, episode_data, concurrent_fragments, show_mode
    )
