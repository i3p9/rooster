import os
import re
import logging
from urllib.parse import urlparse
import requests
import yt_dlp
from .channels import get_channel_name_from_id
from .shows import get_show_name_from_id
from urllib3.exceptions import MaxRetryError, NewConnectionError
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException
from pathlib import Path
import internetarchive


def get_download_location(show_mode: bool) -> Path:
    """
    Retrieves the download location based on the show mode.
    Args: show_mode (bool):
    Returns:
        Path: A pathlib.Path object
    """

    script_path = Path.cwd()

    if show_mode is True:
        download_path = script_path / "Downloads"
    else:
        download_path = script_path / "roosterteeth"

    download_path.mkdir(parents=True, exist_ok=True)
    return download_path


logging.basicConfig(
    filename="rooster.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
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
    """
    Gets the path to the archive log file using pathlib.
    Returns:
        Path: The path to the archive log file.
    """

    script_path = Path.cwd()
    archive_log_path = script_path / "archive.log"

    return archive_log_path


def exists_in_archive(episode_data):
    id_episode = str(episode_data["id_numerical"])
    if episode_data["season_number"] == "99":
        id_episode += "-bonus"  # Handle bonus ids
    archive = get_archive_log_filename()
    if os.path.isfile(archive):
        with open(archive, "r") as f:
            for line in f:
                id_archive = line.split(" ")[1].rstrip()
                if id_archive == id_episode:
                    return True
    return False


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


# Upload to IA


def get_itemname(data) -> str:
    # roosterteeth-test appended for test purposes. -test will be removed
    return f"roosterteeth-test-{data['id_numerical']}"


def get_folder_location_for_ia_upload(episode_data) -> str:
    dl_path = get_download_location(True)
    ia_upload_dir = (
        dl_path
        / episode_data["channel_title"]
        / episode_data["show_title"]
        / get_season_name(episode_data["season_number"])
        / generate_episode_container_name(episode_data)
    )

    return str(ia_upload_dir)


def check_if_ia_item_exists(episode_data) ->bool:
    itemname = get_itemname(episode_data)
    item = internetarchive.get_item(itemname)
    if item.exists:
        return True
    return False


def upload_ia(directory_location, metadata, episoda_data):
    identifier_ia = get_itemname(episoda_data)

    # TODO: parse ia_config file

    # parsed_ia_s3_config = parse_config_file(ia_config_path)[2]["s3"]
    # s3_access_key = parsed_ia_s3_config["access"]
    # s3_secret_key = parsed_ia_s3_config["secret"]

    # if None in {s3_access_key, s3_secret_key}:
    #     msg = "`internetarchive` configuration file is not configured" " properly."
    #     raise Exception(msg)

    print("identifier: ", identifier_ia)
    print("files: ", directory_location)
    print("metadata: ", metadata)
    r = internetarchive.upload(
        identifier=identifier_ia, files=directory_location, metadata=metadata
    )
    print(r[0].status_code)


def generate_ia_meta(episode_data) -> dict:
    collection = "opensource_movies"
    mediatype = "movies"
    title = episode_data["title"]
    creator = episode_data["channel_title"]
    description = episode_data["description"]
    if description is None:
        description = ""
    else:
        description = re.sub("\r?\n", "<br>", description)
    date = episode_data["original_air_date"]
    year = episode_data["original_air_date"][:4]
    episode_slug = episode_data["slug"]
    original_url = f"https://roosterteeth.com/watch/{episode_slug}"
    genres_list = episode_data["genres"]
    if genres_list is not None:
        genres_list.extend(["RoosterTeeth", creator, episode_data["slug"]])
        tags_list = ";".join(genres_list)
    else:  # TODO:256 byte fix
        genres_list = []
        genres_list.extend(["RoosterTeeth", creator, episode_data["slug"]])
        tags_list = ";".join(genres_list)

    metadata = dict(
        mediatype=mediatype,
        collection=collection,
        creator=creator,
        title=title,
        description=description,
        date=date,
        year=year,
        subject=tags_list,
        originalUrl=original_url,
    )
    return metadata


def generate_file_name(data, show_mode) -> str:
    episode_number = get_episode_number(data["episode_number"])
    season_number = get_season_name(data["season_number"])
    if data["episode_type"] == "bonus_feature":
        proper_id = f"{data['id_numerical']}-bonus"
    else:
        proper_id = f"{data['id_numerical']}"

    if show_mode is True:
        if data["is_first_content"] is True:
            return f"{data['original_air_date']} - ☆ {season_number}{episode_number} - {data['title']} ({proper_id})"
        else:
            return f"{data['original_air_date']} - {season_number}{episode_number} - {data['title']} ({proper_id})"
    else:
        safe_title = get_valid_filename(data["title"])
        return f"{data['original_air_date']}_{safe_title}_[{proper_id}]"


def get_season_name(season):
    season_string = str(season)
    formatted_string = re.sub(r"\b(\d)\b", r"0\1", season_string)
    return f"S{formatted_string}"


def get_episode_number(episode):
    episode_string = str(episode)
    formatted_string = re.sub(r"\b(\d)\b", r"0\1", episode_string)
    return f"E{formatted_string}"


def generate_episode_container_name(data) -> str:
    if data["episode_type"] == "bonus_feature":
        proper_id = f"{data['id_numerical']}-bonus"
    else:
        proper_id = f"{data['id_numerical']}"

    return f"{data['original_air_date']} - {proper_id}"


def generate_basic_file_name(data):
    return f"{data['channel_title']} {data['title']} [{data['id_numerical']}]"


def download_thumbnail_fallback(episode_data, show_mode):
    print("Attemping to download HQ thumbnail... (Fallback)")
    try:
        # Ensure the download location exists
        dl_path = Path(get_download_location(show_mode))

        # Generate the file name and create the directory
        file_name = generate_file_name(episode_data, show_mode)
        if show_mode is True:
            file_directory = (
                dl_path
                / episode_data["channel_title"]
                / episode_data["show_title"]
                / get_season_name(episode_data["season_number"])
                / generate_episode_container_name(episode_data)
            )
        else:
            safe_channel_name = get_valid_filename(episode_data["channel_title"])
            safe_show_name = get_valid_filename(episode_data["show_title"])
            file_directory = dl_path / safe_channel_name / safe_show_name / file_name

        file_directory = dl_path / episode_data["show_title"] / file_name
        thumbnail_url = episode_data["large_thumb_alt"]
        file_extension = os.path.splitext(thumbnail_url)[1]
        file_path = file_directory / f"{file_name}{file_extension}"

        # Attempt to download
        s = requests.Session()
        s.mount(thumbnail_url, HTTPAdapter(max_retries=5))

        try:
            response = s.get(thumbnail_url)
            if response.status_code == 200:
                file_directory.mkdir(parents=True, exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"Large Thumbnail Fallback downloaded to: {file_path}")
                logging.info(f"Large Thumbnail Fallback downloaded to: {file_path}")
                return True
            else:
                logging.info(
                    f"Thumbnail Fallback: Failed to download thumbnail from: {thumbnail_url}"
                )
                print(f"Failed to download thumbnail from: {thumbnail_url}")
        except RequestException as e:
            print(
                f"An error occurred: {e}. Please note this episodeId: {episode_data['id_numerical']}"
            )
            logging.info(
                f"An error occurred: {e}. Please note this episodeId: {episode_data['id_numerical']}"
            )

    except (FileNotFoundError, OSError) as err:
        logging.warning(f"Error occurred: {err}")
        return False
    return False


def download_thumbnail(thumbnail_url, episode_data, show_mode):
    print("Attemping to download HQ thumbnail...")
    try:
        # Ensure the download location exists
        dl_path = Path(get_download_location(show_mode))
        dl_path.mkdir(parents=True, exist_ok=True)

        # Generate the file name and create the directory
        file_name = generate_file_name(episode_data, show_mode)
        if show_mode is True:
            file_directory = (
                dl_path
                / episode_data["channel_title"]
                / episode_data["show_title"]
                / get_season_name(episode_data["season_number"])
                / generate_episode_container_name(episode_data)
            )
        else:
            safe_channel_name = get_valid_filename(episode_data["channel_title"])
            safe_show_name = get_valid_filename(episode_data["show_title"])
            file_directory = dl_path / safe_channel_name / safe_show_name / file_name

        file_directory.mkdir(parents=True, exist_ok=True)

        if thumbnail_url is not None:  # from yt-dlp data
            file_extension = os.path.splitext(thumbnail_url)[1]
        else:  # from api data
            logging.warning("Downloading thumbnail using RT API method")
            thumbnail_url = episode_data["large_thumb"]
            file_extension = os.path.splitext(thumbnail_url)[1]

        file_path = file_directory / f"{file_name}{file_extension}"

        # Attempt to download
        s = requests.Session()
        s.mount(thumbnail_url, HTTPAdapter(max_retries=5))

        try:
            response = s.get(thumbnail_url)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"Large Thumbnail downloaded to: {file_path}")
                logging.info(f"Large Thumbnail downloaded to: {file_path}")
                return True
            else:
                print(f"Failed to download thumbnail from: {thumbnail_url}")
                logging.info(
                    f"An error occurred: {e}. Please note this episodeId: {episode_data['id_numerical']}"
                )
                alt_thumb_status = download_thumbnail_fallback(episode_data, show_mode)
        except MaxRetryError as e:
            print(f"MaxRetryError occurred: {e}")
            if hasattr(e, "pool"):
                e.pool.close()
            print("Closed connections to avoid further issues.")
            logging.warning(f"MaxRetryError occurred: {e}")

            if episode_data["large_thumbnail_alt"]:
                alt_thumb_status = download_thumbnail_fallback(episode_data, show_mode)
        except NewConnectionError as e:
            print(f"NewConnectionError occurred: {e}")
            logging.warning(f"NewConnectionError occurred: {e}")
            if episode_data["large_thumbnail_alt"]:
                alt_thumb_status = download_thumbnail_fallback(episode_data, show_mode)

        except Exception as e:
            print(f"An error occurred: {e}")
            logging.critical(f"An error occurred: {e}")
            if episode_data["large_thumbnail_alt"]:
                alt_thumb_status = download_thumbnail_fallback(episode_data, show_mode)

        return alt_thumb_status

    except (FileNotFoundError, OSError) as err:
        logging.warning(f"Error occurred: {err}")
        return False


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
        print("Are you sure its a valid link?")
        print("Are you sure you are logged in?")
        print("If you are, are you a FIRST member?")
        logging.warning(f"{err} yt-dlp parser error for {vod_url}")
    yt_dlp_dict_data = extract_data_from_ytdl_dict(info_dict=info_dict)

    if episode_data is False:
        logging.warning("both api failed, initiating failover")
        video_options["writethumbnail"] = True
    else:
        file_name = generate_file_name(episode_data, show_mode)
        dl_location = get_download_location(show_mode)
        try:
            if yt_dlp_dict_data["large_thumbnail_url_ytdl"]:
                thumbnail_success = download_thumbnail(
                    yt_dlp_dict_data["large_thumbnail_url_ytdl"],
                    episode_data,
                    show_mode,
                )
            else:
                thumbnail_success = download_thumbnail(
                    episode_data["large_thumb"],
                    episode_data,
                    show_mode,
                )

        except FileNotFoundError as fnf_err:
            print(f"Error with file location or sth {fnf_err}")
            logging.warning(f"Error with file location error {fnf_err}")
        except:
            thumbnail_success = False
            logging.warning("thumbnail_success error")

        if thumbnail_success is not True:
            video_options["writethumbnail"] = True

    name_with_extension = file_name + ".%(ext)s"

    # if we are in show mode, episode folder will be inside a show folder
    if show_mode is True:
        if episode_data is not False:
            full_name_with_dir = (
                dl_location / episode_data["channel_title"] / episode_data["show_title"]
            )
            full_name_with_dir /= get_season_name(episode_data["season_number"])
            full_name_with_dir /= generate_episode_container_name(episode_data)
            full_name_with_dir /= name_with_extension
    else:
        logging.warning("show mode True but has Fallback data")
        safe_channel_name = get_valid_filename(episode_data["channel_title"])
        safe_show_name = get_valid_filename(episode_data["show_title"])
        full_name_with_dir = (
            dl_location
            / safe_channel_name
            / safe_show_name
            / file_name
            / name_with_extension
        )

    video_options["outtmpl"] = str(full_name_with_dir)

    # ia prepare
    container_location = (get_folder_location_for_ia_upload(episode_data=episode_data) + "/")
    ia_metadata = generate_ia_meta(episode_data=episode_data)

    print(container_location)
    print(ia_metadata)

    # pass off to yt-dlp for downloading
    print("Starting download: ", full_name_with_dir)
    try:
        yt_dlp.YoutubeDL(video_options).download(vod_url)
        logging.info(
            f"{episode_data['id_numerical']} Downloaded successfully {vod_url}"
        )
        #check whether every file has downloaded. specially mp4
        #upload_ia
    except:
        logging.critical(
            f"{episode_data['id_numerical']} Error with yt_dlp downloading for: {vod_url}"
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
            description = attributes.get("description")
            slug = attributes.get("slug")
            genres = attributes.get("genres")

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
                "episode_type": episode_type,
                "description": description,
                "slug": slug,
                "genres": genres,
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
            description = attributes.get("description")
            slug = attributes.get("slug")
            genres = attributes.get("genres")

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
                "episode_type": episode_type,
                "description": description,
                "slug": slug,
                "genres": genres,
            }
        else:
            # go to fallback data fetch via my api
            return False


def show_stuff(username, password, vod_url, concurrent_fragments, show_mode):
    if not is_tool("ffmpeg"):
        print("ffmpeg not installed, go do that")
        exit()
    api_url = get_rt_api_url(url=vod_url)
    episode_data = None
    episode_data = get_episode_data_from_rt_api(api_url)
    if exists_in_archive(episode_data):
        print(
            f'{episode_data["id_numerical"]}: {episode_data["title"]} already recorded in archive'
        )
    else:
        if episode_data is False:
            episode_data = get_episode_data_from_api(vod_url)
        downloader(
            username, password, vod_url, episode_data, concurrent_fragments, show_mode
        )
