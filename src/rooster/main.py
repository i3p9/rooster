#!/usr/bin/python3 -B
from .downloader import show_stuff, get_download_location
import argparse
import logging
import os
import validators
from .parser import RoosterTeethParser
from pathlib import Path


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


current_dir = get_download_location(fn_mode="show")
log_output_file = os.path.join(current_dir, "rooster.log")


logging.basicConfig(
    filename=log_output_file,
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)


def process_links_from_file(
    username,
    password,
    filename,
    concurrent_fragments,
    fast_check,
    use_aria,
    fn_mode,
):
    with open(filename, "r") as file:
        links = file.readlines()
        num_links = len(links)
        print(f"Found {num_links} links.")

    for index, line in enumerate(links, start=1):
        print(f"Downloading link {index} of {num_links}: {line.strip()}")
        try:
            show_stuff(
                username,
                password,
                line.strip(),
                concurrent_fragments,
                fast_check,
                use_aria,
                fn_mode,
            )
        except Exception as e:
            # Log the exception
            print(f"Error occurred while processing link {index}: {line.strip()}")
            logging.critical(
                f"{e} - Error occurred while processing link {index}: {line.strip()}"
            )


def process_links_from_list(
    username,
    password,
    episode_links,
    concurrent_fragments,
    input_value,
    fast_check,
    use_aria,
    fn_mode,
):
    num_links = len(episode_links)
    for index, episode in enumerate(episode_links):
        print(f"Downloading link {index+1} of {num_links}: {episode}")
        try:
            show_stuff(
                username,
                password,
                episode,
                concurrent_fragments,
                fast_check,
                use_aria,
                fn_mode,
            )
        except Exception as e:
            # Log the exception
            print(
                f"{e} Error occurred while processing link {index+1}: {episode} | Input : {input_value}"
            )
            logging.critical(
                f"{e} Error occurred while processing link {index+1}: {episode} | Input: {input_value}"
            )


def main():
    parser = argparse.ArgumentParser(description="Process command line arguments")

    parser.add_argument("--email", help="Email for authentication")
    parser.add_argument("--password", help="Password for authentication")
    parser.add_argument(
        "--concurrent-fragments",
        default=10,
        type=int,
        help="Number of concurrent fragments (default is 10)",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--show", action="store_true", help="Download in a Predefied Show formatting"
    )
    group.add_argument(
        "--ia", action="store_true", help="Upload to IA and delete uploaded file"
    )

    group.add_argument(
        "--archivist", action="store_true", help="Downloads in a Archivist like fashion"
    )
    parser.add_argument(
        "--fast-check",
        action="store_true",
        help="Enable Fast check for already downlaoded links",
    )
    parser.add_argument(
        "--use-aria",
        action="store_true",
        help="Use aria2c as downloader if it exists in system",
    )

    parser.add_argument("input", help="URL or file containing list of links")

    args = parser.parse_args()
    # if args.show and args.ia:
    #     parser.error("Cannot specify both --show and --ia. Please choose one.")

    username = args.email
    password = args.password
    input_value = args.input
    concurrent_fragments = args.concurrent_fragments
    show_flag = args.show
    upload_to_ia = args.ia
    archivist_mode = args.archivist
    fast_check = args.fast_check
    use_aria = args.use_aria

    if show_flag:
        fn_mode = "show"
    elif archivist_mode:
        fn_mode = "archivist"
    elif upload_to_ia:
        fn_mode = "ia"
        print("Upload to IA not finished Yet. Exiting...")
        exit()

    if input_value.endswith(".txt"):
        process_links_from_file(
            username,
            password,
            input_value,
            concurrent_fragments,
            fast_check,
            use_aria,
            fn_mode,
        )
    else:
        if validators.url(input_value):
            url_parts = input_value.split("/")
            if "roosterteeth.com" in url_parts and "series" in url_parts:
                parser = RoosterTeethParser()
                episode_links = parser.get_episode_links(input_value)
                if episode_links is not None:
                    process_links_from_list(
                        username,
                        password,
                        episode_links,
                        concurrent_fragments,
                        input_value,
                        fast_check,
                        use_aria,
                        fn_mode,
                    )
                else:
                    print(
                        f"something went wrong with parsing: {input_value}. Try again or check your links"
                    )
                    logging.critical(f"parsing failed for: {input_value}")
                    exit()

            elif "roosterteeth.com" in url_parts and "watch" in url_parts:
                show_stuff(
                    username,
                    password,
                    input_value,
                    concurrent_fragments,
                    fast_check,
                    use_aria,
                    fn_mode,
                )
            else:
                print("Unsupported RT URL. Only supports Series and Episodes")
                exit()
        else:
            print(f"invalid url: {input_value}. Exiting.")
            logging.warning(f"invalid url: {input_value}. Exiting.")
            exit()


if __name__ == "__main__":
    raise SystemExit(main())
