import os
import re
import csv
import logging
from urllib.parse import urlparse
import requests
import yt_dlp
from .channels import get_channel_name_from_id
from .shows import get_show_name_from_id
from urllib3.exceptions import MaxRetryError, NewConnectionError
from requests.adapters import HTTPAdapter


def get_download_location(show_mode):
    script_location = os.getcwd()
    if show_mode is True:
        download_location = os.path.join(script_location, "Downloads")
    else:
        download_location = os.path.join(script_location, "roosterteeth")

    if not os.path.exists(download_location):
        os.makedirs(download_location)

    return download_location


current_dir = get_download_location(False)
log_output_file = os.path.join(current_dir, "rooster.log")
# logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(
    filename=log_output_file,
    filemode="w",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


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
        "title": episode_title,
        "channe_title": channe_title,
        "is_first_content": is_first_content,
        "large_thumbnail_url_ytdl": large_thumbnail_url_ytdl,
    }


# for ia
def get_valid_filename(name):
    s = str(name).strip().replace(" ", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    return s


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


def generate_file_name(data, show_mode):
    episode_number = get_episode_number(data["episode_number"])
    season_number = get_season_name(data["season_number"])
    if show_mode is True:
        if data["is_first_content"] is True:
            return f"{data['original_air_date']} - ☆ {season_number}{episode_number} - {data['title']} ({data['id_numerical']})"
        else:
            return f"{data['original_air_date']} - {season_number}{episode_number} - {data['title']} ({data['id_numerical']})"
    else:
        safe_title = get_valid_filename(data["title"])
        return f"{data['original_air_date']}_{safe_title}_[{data['id_numerical']}]"


def get_season_name(season):
    season_string = str(season)
    formatted_string = re.sub(r"\b(\d)\b", r"0\1", season_string)
    return f"S{formatted_string}"


def get_episode_number(episode):
    episode_string = str(episode)
    formatted_string = re.sub(r"\b(\d)\b", r"0\1", episode_string)
    return f"E{formatted_string}"


def generate_episode_container_name(data):
    return f"{data['original_air_date']} - {data['id_numerical']}"


def generate_basic_file_name(data):
    return f"{data['channel_title']} {data['title']} [{data['id_numerical']}]"


def download_thumbnail_fallback(episode_data, show_mode):
    # Ensure the download location exists
    dl_location = get_download_location(show_mode)
    os.makedirs(dl_location, exist_ok=True)

    # Generate the file name and create the directory
    file_name = generate_file_name(episode_data, show_mode)
    if show_mode is True:
        file_directory = os.path.join(
            dl_location,
            episode_data["channel_title"],
            episode_data["show_title"],
            get_season_name(episode_data["season_number"]),
            generate_episode_container_name(episode_data),
        )
    else:
        safe_channel_name = get_valid_filename(episode_data["channel_title"])
        safe_show_name = get_valid_filename(episode_data["show_title"])
        file_directory = os.path.join(
            dl_location, safe_channel_name, safe_show_name, file_name
        )

    file_directory = os.path.join(dl_location, episode_data["show_title"], file_name)
    thumbnail_url = episode_data["large_thumb_alt"]
    file_extension = os.path.splitext(thumbnail_url)[1]

    file_path = os.path.join(file_directory, f"{file_name}{file_extension}")

    # Attempt to download
    s = requests.Session()
    s.mount(thumbnail_url, HTTPAdapter(max_retries=5))

    try:
        response = s.get(thumbnail_url)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"Large Thumbnail downloaded to: {file_path}")
            return True
        else:
            print(f"Failed to download thumbnail from: {thumbnail_url}")
    except Exception as e:
        print(
            f"An error occurred: {e}. Please note this episodeId: {episode_data['id_numerical']}"
        )
    return False


def download_thumbnail(thumbnail_url, episode_data, show_mode):
    # Ensure the download location exists
    dl_location = get_download_location(show_mode)
    os.makedirs(dl_location, exist_ok=True)

    # Generate the file name and create the directory
    file_name = generate_file_name(episode_data, show_mode)
    if show_mode is True:
        file_directory = os.path.join(
            dl_location,
            episode_data["channel_title"],
            episode_data["show_title"],
            get_season_name(episode_data["season_number"]),
            generate_episode_container_name(episode_data),
        )
    else:
        safe_channel_name = get_valid_filename(episode_data["channel_title"])
        safe_show_name = get_valid_filename(episode_data["show_title"])
        file_directory = os.path.join(
            dl_location, safe_channel_name, safe_show_name, file_name
        )
    os.makedirs(file_directory, exist_ok=True)

    if thumbnail_url is not None:  # from yt-dlp data
        file_extension = os.path.splitext(thumbnail_url)[1]
    else:  # from api data
        logging.warning("Downloading thumbnail using fallback method")
        thumbnail_url = episode_data["large_thumb"]
        file_extension = os.path.splitext(thumbnail_url)[1]

    file_path = os.path.join(file_directory, f"{file_name}{file_extension}")

    # Attempt to download
    s = requests.Session()
    s.mount(thumbnail_url, HTTPAdapter(max_retries=5))

    try:
        # TEST
        response = s.get(thumbnail_url)
        if response.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"Large Thumbnail downloaded to: {file_path}")
            return True
        else:
            print(f"Failed to download thumbnail from: {thumbnail_url}")
            alt_thumb_status = download_thumbnail_fallback(episode_data, show_mode)
    except MaxRetryError as e:
        print(f"MaxRetryError occurred: {e}")
        if hasattr(e, "pool"):
            e.pool.close()
        print("Closed connections to avoid further issues.")
        if episode_data["large_thumbnail_alt"]:
            alt_thumb_status = download_thumbnail_fallback(episode_data, show_mode)
    except NewConnectionError as e:
        print(f"NewConnectionError occurred: {e}")
        if episode_data["large_thumbnail_alt"]:
            alt_thumb_status = download_thumbnail_fallback(episode_data, show_mode)

    except Exception as e:
        print(f"An error occurred: {e}")
        if episode_data["large_thumbnail_alt"]:
            alt_thumb_status = download_thumbnail_fallback(episode_data, show_mode)

    return alt_thumb_status


def downloader(
    username, password, vod_url, episode_data, concurrent_fragments, show_mode
):
    video_options = {
        "username": username,
        "password": password,
        "restrictedfilenames": True,
        "forcejson": False,
        "writeinfojson": True,
        "writedescription": True,
        "writesubtitles": True,
        "sub_lang": "all",
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
        video_options["writethumbnail"] = True
    else:
        file_name = generate_file_name(episode_data, show_mode)
        dl_location = get_download_location(show_mode)
        thumbnail_success = download_thumbnail(
            yt_dlp_dict_data["large_thumbnail_url_ytdl"], episode_data, show_mode
        )
        if thumbnail_success is not True:
            video_options["writethumbnail"] = True

    name_with_extension = file_name + ".%(ext)s"

    # if we are in show mode, episode folder will be inside a show folder
    if show_mode is True:
        if episode_data is not False:
            full_name_with_dir = os.path.join(
                dl_location,
                episode_data["channel_title"],
                episode_data["show_title"],
                get_season_name(episode_data["season_number"]),
                generate_episode_container_name(episode_data),
                name_with_extension,
            )
    else:
        logging.warning("show mode True but has Fallback data")
        safe_channel_name = get_valid_filename(episode_data["channel_title"])
        safe_show_name = get_valid_filename(episode_data["show_title"])
        full_name_with_dir = os.path.join(
            dl_location,
            safe_channel_name,
            safe_show_name,
            file_name,
            name_with_extension,
        )

    video_options["outtmpl"] = full_name_with_dir

    # pass off to yt-dlp for downloading
    print("Starting download: ", full_name_with_dir)
    try:
        yt_dlp.YoutubeDL(video_options).download(vod_url)
    except:
        logging.warning(
            f"Error with yt_dlp downloading. ID: {episode_data['id_numerical']}"
        )


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
            title = make_filename_safe(attributes.get("title"))
            channel_id = attributes.get("channel_id")
            season_id = attributes.get("season_id")
            original_air_date_full = attributes.get("original_air_date", "")
            is_first_content = attributes.get("is_sponsors_only")
            show_id = attributes.get("show_id")
            parent_slug = attributes.get("parent_content_slug", "")
            show_title = make_filename_safe(get_show_name_from_id(show_id))
            episode_number = attributes.get("number")
            season = attributes.get("season_number", "99")
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
                "title": title,
                "original_air_date": original_air_date,
                "show_title": show_title,
                "is_first_content": is_first_content,
                "channel_title": channel_title,
                "large_thumb": large_thumb,
                "season_number": season,
                "episode_number": episode_number,
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
            uuid = episode_obj.get("uuid")
            images = episode_obj.get("included", {}).get("images", [])
            large_thumb = get_high_quality_thumbnail_link(images)

            episode_type = episode_obj.get("type")
            attributes = episode_obj.get("attributes", {})
            title = make_filename_safe(attributes.get("title"))
            channel_id = attributes.get("channel_id")
            original_air_date_full = attributes.get("original_air_date", "")
            is_first_content = attributes.get("is_sponsors_only")
            show_id = show_title = attributes.get("show_id")
            show_title = make_filename_safe(get_show_name_from_id(show_id))
            season_id = attributes.get("season_id")
            parent_slug = attributes.get("parent_content_slug", "")
            season = attributes.get("season_number", "99")
            episode_number = attributes.get("number")

            if season_id:
                large_thumb_alt = f"https://cdn.ffaisal.com/thumbnail/{show_id}/{season_id}/{uuid}.jpg"
            else:
                large_thumb_alt = f"https://cdn.ffaisal.com/thumbnail/{show_id}/bonus-content-{parent_slug}/{uuid}.jpg"

            original_air_date = (
                original_air_date_full.split("T")[0]
                if "T" in original_air_date_full
                else None
            )
            channel_title = make_filename_safe(get_channel_name_from_id(channel_id))

            return {
                "id_numerical": episode_id,
                "title": title,
                "original_air_date": original_air_date,
                "show_title": show_title,
                "is_first_content": is_first_content,
                "channel_title": channel_title,
                "large_thumb": large_thumb,
                "large_thumb_alt": large_thumb_alt,
                "season_number": season,
                "episode_number": episode_number,
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
