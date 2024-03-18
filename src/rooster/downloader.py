import os
import re
import logging
from urllib.parse import urlparse
import requests
import shutil
import json
import yt_dlp

from .channels import get_channel_name_from_id
from .shows import get_show_name_from_id

from urllib3.exceptions import MaxRetryError, NewConnectionError
from requests.adapters import HTTPAdapter
from requests.exceptions import SSLError
from requests.exceptions import RequestException
from pathlib import Path
import internetarchive


def get_download_location(fn_mode: str) -> Path:
    """
    Retrieves the download location based on the show mode.
    Args: fn_mode: show | ia | archivist
    Returns:
        Path: A pathlib.Path object
    """

    script_path = Path.cwd()

    if fn_mode == "show" or fn_mode == "archivist":
        download_path = script_path / "Downloads"

    if fn_mode == "ia":
        # download_path = script_path / "roosterteeth-temp"
        download_path = Path("~/.rooster").expanduser()

    download_path.mkdir(parents=True, exist_ok=True)
    return download_path


def save_successful_downloaded_slugs(slug):
    downlaoded_log_path = get_downloaded_log_filename()
    try:
        with open(downlaoded_log_path, "a") as log_file:
            log_file.write(slug + "\n")
    except Exception as ex:
        logging.critical(
            f"Successful Download Log: An error occurred while saving slug {slug} - {ex}"
        )


def save_failed_upload_url_slugs(url):
    downlaoded_log_path = get_failed_uploaded_log_filename()
    try:
        with open(downlaoded_log_path, "a") as log_file:
            log_file.write(url + "\n")
    except Exception as ex:
        logging.critical(
            f"Failed Upload Log: An error occurred while saving url {url} - {ex}"
        )


log_dir = Path.cwd() / "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)


logging.basicConfig(
    filename="logs/rooster.log",
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


def get_downloaded_log_filename():
    """
    Gets the path to the downlaoded log file using pathlib.
    This is a manual logging process to find dupe much quicker
    Returns:
        Path: The path to the archive log file.
    """

    script_path = Path.cwd()
    archive_log_path = script_path / "logs" / "downloaded.log"

    return archive_log_path


def get_failed_uploaded_log_filename():
    """
    Gets the path to the downlaoded log file using pathlib.
    This is a manual logging process to find dupe much quicker
    Returns:
        Path: The path to the archive log file.
    """

    script_path = Path.cwd()
    archive_log_path = script_path / "logs" / "uploaded.log"

    return archive_log_path


def get_archive_log_filename():
    """
    Gets the path to the archive log file using pathlib.
    Returns:
        Path: The path to the archive log file.
    """

    script_path = Path.cwd()
    archive_log_path = script_path / "logs" / "archive.log"

    return archive_log_path


def exists_in_downloaded_log(slug, slugs):
    return slug in slugs


# def exists_in_downloaded_log(slug):
#     downlaoded_log_path = get_downloaded_log_filename()
#     if os.path.isfile(downlaoded_log_path):
#         with open(downlaoded_log_path, "r") as f:
#             for line in f:
#                 if line.rstrip() == slug:
#                     return True
#         return False


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


def make_filename_safe_unicode(input_string):
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
    if data["episode_type"] == "bonus_feature":
        return f"roosterteeth-{data['id_numerical']}-bonus"
    else:
        return f"roosterteeth-{data['id_numerical']}"


def get_folder_location_for_ia_upload(episode_data) -> str:
    dl_path = get_download_location(fn_mode="ia")
    ia_upload_dir = (
        dl_path
        / episode_data["channel_title"]
        / episode_data["show_title"]
        / get_season_name(episode_data["season_number"])
        / generate_episode_container_name(episode_data)
    )

    return str(ia_upload_dir)


def check_if_ia_item_exists(episode_data) -> bool:
    itemname = get_itemname(episode_data)
    item = internetarchive.get_item(itemname)
    if item.exists:
        return True, itemname
    return False, itemname

    # if r[0].status_code != 200:
    #     print(
    #         f"Upload failed for: https://roosterteeth.com/watch/{episoda_data['slug']}"
    #     )
    #     logging.warning(
    #         f"Upload failed for: https://roosterteeth.com/watch/{episoda_data['slug']}"
    #     )
    # else:
    #     print(
    #         f"Uploaded successfully to: https://archive.org/details/roosterteeth-{identifier_ia}"
    #     )
    #     try:
    #         print("Cleaning up...")
    #         logging.info(f"Deleting files after IA uploads from {directory_location}")
    #         directory_location.rmdir()
    #     except Exception as e:
    #         print(f"An error occurred while uploading {identifier_ia} {e}")
    #         logging.critical(f"An error occurred while uploading {identifier_ia} {e}")


def generate_ia_meta(episode_data):
    collection = "opensource_movies"
    mediatype = "movies"
    title = episode_data["title_meta"]
    creator = episode_data["channel_title_meta"]
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
    first_exclusive = "First" if episode_data["is_first_content"] else "Public"
    first_exclusive_bool = True if episode_data["is_first_content"] else False

    if genres_list is not None:
        genres_list.extend(
            [
                "Rooster Teeth",
                first_exclusive,
                creator,
                episode_data["slug"],
            ]
        )
        tags_string = ";".join(genres_list)
    else:
        genres_list = []
        genres_list.extend(
            [
                "Rooster Teeth",
                first_exclusive,
                creator,
                episode_data["slug"],
            ]
        )
        tags_string = ";".join(genres_list)

    while len(tags_string.encode("utf-8")) > 255:
        tags_list = tags_string.split(";")
        tags_list.pop()
        tags_string = ";".join(tags_list)

    show_title = episode_data["show_title_meta"]
    season_number = episode_data["season_number"]
    episode_number = episode_data["episode_number"]

    metadata = dict(
        mediatype=mediatype,
        collection=collection,
        creator=creator,  # channel title
        title=title,
        description=description,
        date=date,
        year=year,
        subject=tags_string,
        originalUrl=original_url,
        show_title=show_title,
        season=int(season_number),
        episode=int(episode_number),
        firstExclusive=first_exclusive_bool,
        scanner="Rooster - Roosterteeth Website Mirror 0.2.0b",
    )
    return metadata


def has_video_and_image(directory) -> bool:
    mp4_files = list(directory.glob("*.mp4"))
    jpg_files = list(directory.glob("*.jpg"))
    png_files = list(directory.glob("*.png"))
    gif_files = list(directory.glob("*.gif"))
    if mp4_files:
        if jpg_files or png_files or gif_files:
            return True

    return False


def check_if_files_are_ready(directory) -> bool:
    mp4_files = list(directory.glob("*.mp4"))
    parts = [
        "*.part",
        "*.f303.*",
        "*.f302.*",
        "*.ytdl",
        "*.f251.*",
        "*.248.*",
        "*.f247.*",
        "*.temp",
        "*.ytdlp",
    ]

    temp_files = []
    for file_type in parts:
        temp_files.extend(directory.glob(f"*.{file_type}"))

    if mp4_files:
        if not temp_files:
            return True
    return False


def generate_file_name(data, fn_mode) -> str:
    episode_number = get_episode_number(data["episode_number"])
    season_number = get_season_name(data["season_number"])
    if data["episode_type"] == "bonus_feature":
        proper_id = f"{data['id_numerical']}-bonus"
    else:
        proper_id = f"{data['id_numerical']}"

    if fn_mode == "show":
        if data["is_first_content"] is True:
            return f"{data['original_air_date']} - ☆ {season_number}{episode_number} - {data['title']} ({proper_id})"
        else:
            return f"{data['original_air_date']} - {season_number}{episode_number} - {data['title']} ({proper_id})"

    if fn_mode == "ia":
        safe_title = get_valid_filename(data["title"])
        return f"{data['original_air_date']}_{safe_title}_[{proper_id}]"

    if fn_mode == "archivist":
        safe_title = get_valid_filename(data["title"])
        return f"{data['original_air_date']}_{safe_title}_[{proper_id}]"

    return None


def get_season_name(season):
    season_string = str(season)
    formatted_string = re.sub(r"\b(\d)\b", r"0\1", season_string)
    return f"S{formatted_string}"


def get_episode_number(episode):
    episode_string = str(episode)
    formatted_string = re.sub(r"\b(\d)\b", r"0\1", episode_string)
    return f"E{formatted_string}"


def generate_episode_container_name(data, fn_mode) -> str:
    if data["episode_type"] == "bonus_feature":
        proper_id = f"{data['id_numerical']}-bonus"
    else:
        proper_id = f"{data['id_numerical']}"

    return f"{data['original_air_date']} - {proper_id}"


def generate_basic_file_name(data):
    return f"{data['channel_title']} {data['title']} [{data['id_numerical']}]"


def download_thumbnail_fallback(episode_data, fn_mode):
    print("Attemping to download HQ thumbnail... (Fallback)")
    try:
        # Ensure the download location exists
        dl_path = Path(get_download_location(fn_mode=fn_mode))

        # Generate the file name and create the directory
        file_name = generate_file_name(
            data=episode_data,
            fn_mode=fn_mode,
        )
        if fn_mode == "show":
            file_directory = (
                dl_path
                / episode_data["channel_title"]
                / episode_data["show_title"]
                / get_season_name(episode_data["season_number"])
                / generate_episode_container_name(episode_data, fn_mode)
            )

        if fn_mode == "ia":
            safe_channel_name = get_valid_filename(episode_data["channel_title"])
            safe_show_name = get_valid_filename(episode_data["show_title"])
            file_directory = dl_path / get_valid_filename(
                generate_episode_container_name(episode_data, fn_mode)
            )

        if fn_mode == "archivist":
            safe_channel_name = get_valid_filename(episode_data["channel_title"])
            safe_show_name = get_valid_filename(episode_data["show_title"])
            episode_container = get_valid_filename(
                generate_episode_container_name(episode_data, fn_mode)
            )
            file_directory = (
                dl_path / safe_channel_name / safe_show_name / episode_container
            )

        file_directory = dl_path / episode_data["show_title"] / file_name
        thumbnail_url = episode_data["large_thumb_alt"]
        file_extension = os.path.splitext(thumbnail_url)[1]

        file_path = file_directory / f"{file_name}{file_extension}"
        if file_path.exists():
            print("Thumbnail already exists. Skipping download.")
            return

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


def download_thumbnail(thumbnail_url, episode_data, fn_mode):
    print("Attemping to download HQ thumbnail...")
    try:
        # Ensure the download location exists
        dl_path = Path(get_download_location(fn_mode=fn_mode))
        dl_path.mkdir(parents=True, exist_ok=True)

        # Generate the file name and create the directory
        file_name = generate_file_name(
            data=episode_data,
            fn_mode=fn_mode,
        )
        if fn_mode == "show":
            file_directory = (
                dl_path
                / episode_data["channel_title"]
                / episode_data["show_title"]
                / get_season_name(episode_data["season_number"])
                / generate_episode_container_name(episode_data, fn_mode)
            )
        if fn_mode == "ia":
            safe_channel_name = get_valid_filename(episode_data["channel_title"])
            safe_show_name = get_valid_filename(episode_data["show_title"])
            file_directory = dl_path / get_valid_filename(
                get_valid_filename(
                    generate_episode_container_name(episode_data, fn_mode)
                )
            )

        if fn_mode == "archivist":
            safe_channel_name = get_valid_filename(episode_data["channel_title"])
            safe_show_name = get_valid_filename(episode_data["show_title"])
            episode_container = get_valid_filename(
                generate_episode_container_name(episode_data, fn_mode)
            )
            file_directory = (
                dl_path / safe_channel_name / safe_show_name / episode_container
            )

        file_directory.mkdir(parents=True, exist_ok=True)

        if thumbnail_url is not None:  # from yt-dlp data
            file_extension = os.path.splitext(thumbnail_url)[1]
        else:  # from api data
            thumbnail_url = episode_data["large_thumb"]
            file_extension = os.path.splitext(thumbnail_url)[1]

        file_path = file_directory / f"{file_name}{file_extension}"

        if file_path.exists():
            print("Thumbnail already exists. Skipping download.")
            return

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
                logging.info(
                    f"An error occurred: {e}. Please note this episodeId: {episode_data['id_numerical']}"
                )
                alt_thumb_status = download_thumbnail_fallback(episode_data, fn_mode)
        except MaxRetryError as e:
            print(f"MaxRetryError occurred: {e}")
            if hasattr(e, "pool"):
                e.pool.close()
            print("Closed connections to avoid further issues.")
            logging.warning(f"MaxRetryError occurred: {e}")

            if episode_data["large_thumbnail_alt"]:
                alt_thumb_status = download_thumbnail_fallback(episode_data, fn_mode)
        except NewConnectionError as e:
            print(f"NewConnectionError occurred: {e}")
            logging.warning(f"NewConnectionError occurred: {e}")
            if episode_data["large_thumbnail_alt"]:
                alt_thumb_status = download_thumbnail_fallback(episode_data, fn_mode)

        except Exception as e:
            print(f"An error occurred: {e}")
            logging.critical(f"An error occurred: {e}")
            if episode_data["large_thumbnail_alt"]:
                alt_thumb_status = download_thumbnail_fallback(episode_data, fn_mode)

        return alt_thumb_status

    except (FileNotFoundError, OSError) as err:
        logging.warning(f"Error occurred: {err}")
        return False


def download_thumb_from_yt_dlp_data(extractor_options, vod_url, episode_data, fn_mode):
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
    if yt_dlp_dict_data["large_thumbnail_url_ytdl"]:
        thumbnail_success = download_thumbnail(
            yt_dlp_dict_data["large_thumbnail_url_ytdl"],
            episode_data,
            fn_mode,
        )
        return thumbnail_success


def downloader(
    username,
    password,
    vod_url,
    episode_data,
    concurrent_fragments,
    use_aria,
    fn_mode,
    fragment_retries,
    fragment_abort,
    keep_after_upload,
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
        "fragment_retries": fragment_retries,
        "skip_unavailable_fragments": fragment_abort,
        "download_archive": get_archive_log_filename(),
        # "progress_hooks": [ydl_progress_hook],
        "retry_sleep_functions": {
            "http": lambda attempt: min(10, attempt**2),
            "fragment": lambda attempt: min(5, attempt),
            "file_access": lambda attempt: min(2, attempt * 0.5),
        },
        "sleep_interval": 3,
        "max_sleep_interval": 5,
    }
    extractor_options = {
        "username": username,
        "password": password,
    }

    ## use aria2c if it exists in system
    if use_aria is True:
        if is_tool("aria2c"):
            video_options["external_downloader"] = "aria2c"
            video_options["external_downloader_args"] = [
                "-j 16",
                " -x 16",
                "-s 16",
            ]
    else:
        video_options["concurrent_fragment_downloads"] = int(concurrent_fragments)

    # TODO:
    # why am i calling the info_dict before checking if I have filename
    # data or not? thumbnail infO? idk
    # try:
    #     info_dict = yt_dlp.YoutubeDL(extractor_options).extract_info(
    #         vod_url, download=False
    #     )
    # except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError) as err:
    #     print(err)
    #     print("Are you sure its a valid link?")
    #     print("Are you sure you are logged in?")
    #     print("If you are, are you a FIRST member?")
    #     logging.warning(f"{err} yt-dlp parser error for {vod_url}")
    # yt_dlp_dict_data = extract_data_from_ytdl_dict(info_dict=info_dict)

    ###
    # generate file name
    ## generate directory
    if episode_data:  # Have Episode Data
        # step 1: Download Thumbnail
        if episode_data["large_thumb"]:
            try:
                thumbnail_success = download_thumbnail(
                    episode_data["large_thumb"], episode_data, fn_mode
                )
                if not thumbnail_success:
                    download_thumb_from_yt_dlp_data(
                        extractor_options=extractor_options,
                        vod_url=vod_url,
                        episode_data=episode_data,
                        fn_mode=fn_mode,
                    )
            except FileNotFoundError as fnf_err:
                print(f"Error with file location or sth {fnf_err}")
                logging.warning(f"Error with file location error {fnf_err}")
            except:
                print("Error Downloading HQ Thumbs. Will download LQ Thumb")
                logging.warning("Error Downloading HQ Thumbs. Will download LQ Thumb")
                video_options["writethumbnail"] = True

        # Step 2: Generate File Name
        # Two type of file name:
        # Show Mode: For keeping files
        # IA Mode: For uploading to IA, and deleting afterwards
        file_name = generate_file_name(
            data=episode_data,
            fn_mode=fn_mode,
        )
        name_with_extension = file_name + ".%(ext)s"

        # Step 3: Download directory
        # Downloads folder if fn_mode is show | archivist
        # ~/.roosterteeth folder if if fn_mode is ia
        dl_location = get_download_location(fn_mode=fn_mode)

        # Step 4: Generate full download directory
        if fn_mode == "show":
            # Channel Name / Show Title / Sxx / YYYY-MM-DD [ID] / Filename
            full_name_with_dir = (
                dl_location / episode_data["channel_title"] / episode_data["show_title"]
            )
            full_name_with_dir /= get_season_name(episode_data["season_number"])
            full_name_with_dir /= generate_episode_container_name(episode_data, fn_mode)
            full_name_with_dir /= name_with_extension

        if fn_mode == "ia":
            safe_channel_name = get_valid_filename(episode_data["channel_title"])
            safe_show_name = get_valid_filename(episode_data["show_title"])
            full_name_with_dir = (
                dl_location
                / get_valid_filename(
                    generate_episode_container_name(episode_data, fn_mode)
                )
                / name_with_extension
            )
        if fn_mode == "archivist":
            safe_channel_name = get_valid_filename(episode_data["channel_title"])
            safe_show_name = get_valid_filename(episode_data["show_title"])
            full_name_with_dir = (
                dl_location
                / safe_channel_name
                / safe_show_name
                / get_valid_filename(
                    generate_episode_container_name(episode_data, fn_mode)
                )
                / name_with_extension
            )

    else:
        print("Episode Data not found")

    video_options["outtmpl"] = str(full_name_with_dir)

    # IA Specific Task
    if fn_mode == "ia":
        # container_location = (
        #     get_folder_location_for_ia_upload(episode_data=episode_data) + "/"
        # )
        ia_metadata = generate_ia_meta(episode_data=episode_data)

    # pass off to yt-dlp for downloading
    print("Starting download: ", full_name_with_dir)
    try:
        yt_dlp.YoutubeDL(video_options).download(vod_url)
        print(f"{episode_data['id_numerical']} Downloaded successfully {vod_url}")

        if has_video_and_image(
            full_name_with_dir.parent
        ):  # checks for mp4 and jpg/png existance
            print("Downloads include image/video file, saving to downloaded log")
            save_successful_downloaded_slugs(slug=episode_data["slug"])

        # check whether every file has downloaded. specially mp4
        # upload_ia
        # SAVE SLUG to a new file for checking
        if fn_mode == "ia":
            container_dir = full_name_with_dir.parent
            ready_for_upload = check_if_files_are_ready(directory=container_dir)

            if ready_for_upload:
                print("Directory contains mp4 file and no parts, Uploading")
                upload_status = upload_ia(
                    directory_location=container_dir,
                    md=ia_metadata,
                    episoda_data=episode_data,
                    keep_after_upload=keep_after_upload,
                )
                if upload_status is not True:
                    print("Something went wrong with the upload, try again later.")
                else:
                    if not keep_after_upload:
                        shutil.rmtree(container_dir)

            else:
                print("Directory does not contain .mp4 files. Exiting.")
                logging.critical(
                    f"Directory does not contain .mp4 files: {container_dir}"
                )

        else:
            print(
                f"An error occurred while trying to upload from this location: {container_dir}"
            )
            logging.critical(
                f"An error occurred while trying to upload from this location: {container_dir}"
            )

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
    s = requests.Session()
    s.mount(url, HTTPAdapter(max_retries=5))

    try:
        response = s.get(url)
        if response.status_code == 200:
            episode_data = response.json().get("data", [])
        else:
            print(f"Failed to get api data from: {url}")
            logging.info(
                f"An error occurred: {e}. Please note this episodeId: {episode_data['id_numerical']}"
            )
            return None
    except MaxRetryError as e:
        print(f"MaxRetryError occurred: {e}")
        if hasattr(e, "pool"):
            e.pool.close()
        print("Closed connections to avoid further issues.")
        logging.warning(f"MaxRetryError occurred: {e}")
        return None
    except NewConnectionError as e:
        print(f"NewConnectionError occurred: {e}")
        logging.warning(f"NewConnectionError occurred: {e}")
        return None

    except Exception as e:
        print(f"An error occurred: {e}")
        logging.critical(f"An error occurred: {e}")
        return None

    episode_data = response.json().get("documents", [])
    if episode_data:
        episode_obj = episode_data[0]
        episode_id = episode_obj.get("id")
        uuid = episode_obj.get("uuid")
        episode_type = episode_obj.get("type")
        attributes = episode_obj.get("attributes", {})
        title = make_filename_safe_unicode(attributes.get("title"))
        title_meta = attributes.get("title")
        channel_id = attributes.get("channel_id")
        season_id = attributes.get("season_id")
        original_air_date_full = attributes.get("original_air_date", "")
        is_first_content = attributes.get("is_sponsors_only")
        show_id = attributes.get("show_id")
        parent_slug = attributes.get("parent_content_slug", "")
        show_title = make_filename_safe_unicode(get_show_name_from_id(show_id))
        show_title_meta = get_show_name_from_id(show_id)
        episode_number = attributes.get("number")
        season = attributes.get("season_number", "99")
        if season_id:
            large_thumb = (
                f"https://cdn.ffaisal.com/thumbnail/{show_id}/{season_id}/{uuid}.jpg"
            )
        else:
            large_thumb = f"https://cdn.ffaisal.com/thumbnail/{show_id}/bonus-content-{parent_slug}/{uuid}.jpg"

        original_air_date = (
            original_air_date_full.split("T")[0]
            if "T" in original_air_date_full
            else None
        )
        channel_title = make_filename_safe_unicode(get_channel_name_from_id(channel_id))
        channel_title_meta = get_channel_name_from_id(channel_id)
        description = attributes.get("description")
        slug = attributes.get("slug")
        genres = attributes.get("genres")

        return {
            "id_numerical": episode_id,
            "title": title,
            "original_air_date": original_air_date,
            "show_title": show_title,
            "show_title_meta": show_title_meta,
            "title_meta": title_meta,
            "is_first_content": is_first_content,
            "channel_title": channel_title,
            "channel_title_meta": channel_title_meta,
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
        return None


def get_episode_data_from_rt_api(url):
    s = requests.Session()
    s.mount(url, HTTPAdapter(max_retries=5))

    try:
        response = s.get(url)
        if response.status_code == 200:
            episode_data = response.json().get("data", [])
        else:
            print(f"Failed to get api data from: {url}")
            logging.info(
                f"An error occurred: {e}. Please note this episodeId: {episode_data['id_numerical']}"
            )
            return None
    except MaxRetryError as e:
        print(f"MaxRetryError occurred: {e}")
        if hasattr(e, "pool"):
            e.pool.close()
        print("Closed connections to avoid further issues.")
        logging.warning(f"MaxRetryError occurred: {e}")
        return None
    except NewConnectionError as e:
        print(f"NewConnectionError occurred: {e}")
        logging.warning(f"NewConnectionError occurred: {e}")
        return None

    except Exception as e:
        print(f"An error occurred: {e}")
        logging.critical(f"An error occurred: {e}")
        return None

    if episode_data:
        episode_obj = episode_data[0]
        episode_id = episode_obj.get("id")
        uuid = episode_obj.get("uuid")
        images = episode_obj.get("included", {}).get("images", [])
        large_thumb = get_high_quality_thumbnail_link(images)

        episode_type = episode_obj.get("type")
        attributes = episode_obj.get("attributes", {})
        title = make_filename_safe_unicode(attributes.get("title"))
        title_meta = attributes.get("title")
        channel_id = attributes.get("channel_id")
        original_air_date_full = attributes.get("original_air_date", "")
        is_first_content = attributes.get("is_sponsors_only")
        show_id = attributes.get("show_id")
        show_title = make_filename_safe_unicode(get_show_name_from_id(show_id))
        show_title_meta = get_show_name_from_id(show_id)
        season_id = attributes.get("season_id")
        parent_slug = attributes.get("parent_content_slug", "")
        season = attributes.get("season_number", "99")
        episode_number = attributes.get("number")

        if season_id:
            large_thumb_alt = (
                f"https://cdn.ffaisal.com/thumbnail/{show_id}/{season_id}/{uuid}.jpg"
            )
        else:
            large_thumb_alt = f"https://cdn.ffaisal.com/thumbnail/{show_id}/bonus-content-{parent_slug}/{uuid}.jpg"

        original_air_date = (
            original_air_date_full.split("T")[0]
            if "T" in original_air_date_full
            else None
        )
        channel_title = make_filename_safe_unicode(get_channel_name_from_id(channel_id))
        channel_title_meta = get_channel_name_from_id(channel_id)
        description = attributes.get("description")
        slug = attributes.get("slug")
        genres = attributes.get("genres")

        return {
            "id_numerical": episode_id,
            "title": title,
            "original_air_date": original_air_date,
            "show_title": show_title,
            "show_title_meta": show_title_meta,
            "title_meta": title_meta,
            "is_first_content": is_first_content,
            "channel_title": channel_title,
            "channel_title_meta": channel_title_meta,
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
        return None


def show_stuff(
    username,
    password,
    vod_url,
    concurrent_fragments,
    fast_check,
    use_aria,
    fn_mode,
    fragment_retries,
    fragment_abort,
    total_slugs,
    ignore_existing,
    keep_after_upload,
    update_metadata,
):
    if not is_tool("ffmpeg"):
        print("ffmpeg not installed, go do that")
        exit()
    # check manually
    if fast_check:
        if exists_in_downloaded_log(slug=vod_url.split("/")[-1], slugs=total_slugs):
            print(f"{vod_url}: URL already recorded in downloaded log")
            return

    api_url = get_rt_api_url(url=vod_url)
    episode_data = None
    episode_data = get_episode_data_from_rt_api(api_url)
    if episode_data is None:
        alt_api_url = get_api_url(url=vod_url)
        episode_data = get_episode_data_from_api(alt_api_url)

    # update meta:
    if update_metadata is True:
        item_exists, identifier = check_if_ia_item_exists(episode_data=episode_data)
        if item_exists is False:
            print(f"Item doesn't exist yet, can't update metadata for {vod_url}")
            logging.info(f"Item doesn't exist yet, can't update metadata for {vod_url}")
            return
        else:
            update_ia_metadata(episode_data)
            return

    if episode_data is None:
        print("Both API Failed.. Skipping...")
    else:
        if exists_in_archive(episode_data):
            print(
                f'{episode_data["id_numerical"]}: {episode_data["title"]} already recorded in archive'
            )
        else:
            if fn_mode == "ia":
                if not ignore_existing:
                    item_exists, identifier = check_if_ia_item_exists(
                        episode_data=episode_data
                    )
                    if item_exists is True:
                        print(
                            f"Item already exists at https://archive.org/details/{identifier}"
                        )
                        logging.info(
                            f"Item already exists at https://archive.org/details/{identifier}"
                        )
                        return

            downloader(
                username,
                password,
                vod_url,
                episode_data,
                concurrent_fragments,
                use_aria,
                fn_mode,
                fragment_retries,
                fragment_abort,
                keep_after_upload,
            )


def upload_ia(directory_location, md, episoda_data, keep_after_upload):
    identifier_ia = get_itemname(episoda_data)

    # TODO: parse ia_config file

    # if None in {s3_access_key, s3_secret_key}:
    #     msg = "`internetarchive` configuration file is not configured" " properly."
    #     raise Exception(msg)

    dir_loc_with_slash = str(directory_location) + "/"

    dete_after_upload = not keep_after_upload

    item = internetarchive.get_item(identifier=identifier_ia)

    try:
        r = item.upload(
            # identifier=identifier_ia,
            files=dir_loc_with_slash,
            metadata=md,
            verbose=True,
            retries=9001,
            request_kwargs=dict(timeout=9001),
            delete=dete_after_upload,
            # checksum=True,
        )

        VIDEO_OKAY = False
        successful_uploads = 0
        for response in r:
            if response.status_code == 200:
                successful_uploads += 1

            # Check if the URL ends with '.mp4'
            if response.url.endswith(".mp4"):
                print(
                    f"{md['title']}Uploaded Successfully at https://archive.org/details/{identifier_ia}"
                )
                VIDEO_OKAY = True

        if successful_uploads != len(r):
            print(f"{successful_uploads} out of {len(r)} uploaded successfully")
        if successful_uploads == 0:
            save_failed_upload_url_slugs(md["originalUrl"])
            print(
                "something went wrong with the uploads. if you are updating existing item, ignore this. And any NoneType Error"
            )

        return VIDEO_OKAY

        # if r[0].status_code == 200:
        #     print(
        #         f"Uploaded Successfully at https://archive.org/details/{identifier_ia}"
        #     )
        #     total_responses = len(r)
        #     successful_responses = sum(
        #         1 for response in r if response.status_code == 200
        #     )
        #     unsuccessful_responses = total_responses - successful_responses
        #     if unsuccessful_responses > 0:
        #         print(
        #             f"{unsuccessful_responses} out of {total_responses} uploads were unsuccessful. Please check the Archive.org link to make sure all is OKAY."
        #         )
        #     directory_location.rmdir()

        #     return True
        # else:
        #     print("Something went wrong. Try again.")
        #     save_failed_upload_url_slugs(md["originalUrl"])

    except SSLError as ssl_error:
        print(f"SSLError occurred: {ssl_error}")
        logging.critical(f"SSLError occurred: {ssl_error}")

    except MaxRetryError as max_retry_error:
        print(f"MaxRetryError occurred: {max_retry_error}")
        logging.critical(f"MaxRetryError occurred: {max_retry_error}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        logging.critical(f"An unexpected error occurred: {e}")

    return False


def update_ia_metadata(episode_data):
    ia_meta = generate_ia_meta(episode_data=episode_data)
    identifier_ia = get_itemname(data=episode_data)
    ia_meta.pop("mediatype")
    ia_meta.pop("collection")

    item = internetarchive.get_item(identifier=identifier_ia)
    r = item.modify_metadata(metadata=ia_meta, debug=False)

    if r.status_code == 200:
        print("Update successfully queued!")
        return True
    else:
        if r.text:
            parsed = json.loads(r.text)
            print(f"Error: {parsed['error']}")

        else:
            print(
                "something went wrong while updating metadata. Permission issue? r u owner of the item?"
            )
    return False


# Debug
# show_stuff(
#     username="raptorh2000@gmail.com",
#     password="PASSWORD",
#     vod_url="https://roosterteeth.com/watch/gameplay-2018-dollal",
#     concurrent_fragments=10,
#     fast_check=True,
#     use_aria=False,
#     fn_mode="ia",
#     fragment_retries=10,
#     fragment_abort=False,
#     total_slugs="slugs",
#     ignore_existing=True,
#     keep_after_upload=True,
#     update_metadata=True,
# )
