#!/usr/bin/python3 -B
from .downloader import show_stuff
import argparse
import logging
import os
import validators
from .parser import RoosterTeethParser


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


logging.basicConfig(
    filename=log_output_file,
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)


def process_links_from_file(
    username, password, filename, concurrent_fragments, show_mode, fragment_retries, fragment_abort
):
    with open(filename, "r") as file:
        links = file.readlines()
        num_links = len(links)
        print(f"Found {num_links} links.")

    for index, line in enumerate(links, start=1):
        print(f"Downloading link {index} of {num_links}: {line.strip()}")
        try:
            show_stuff(
                username, password, line.strip(), concurrent_fragments, show_mode, fragment_retries, fragment_abort
            )
        except Exception as e:
            # Log the exception
            print(f"Error occurred while processing link {index}: {line.strip()}")
            logging.critical(
                f"Error occurred while processing link {index}: {line.strip()}"
            )

def process_links_from_list(username, password, episode_links, concurrent_fragments, show_mode, fragment_retries, fragment_abort, input_value):
    num_links = len(episode_links)
    for index,episode in enumerate(episode_links):
        print(f"Downloading link {index+1} of {num_links}: {episode}")
        try:
            show_stuff(
                username, password, episode, concurrent_fragments, show_mode, fragment_retries, fragment_abort
            )
        except Exception as e:
            # Log the exception
            print(f"Error occurred while processing link {index+1}: {episode} | Input : {input_value}")
            logging.critical(
                f"Error occurred while processing link {index+1}: {episode} | Input: {input_value}"
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
    parser.add_argument("--show", action="store_true", help="Flag to show something")
    parser.add_argument(
        "--fragment-retries",
        default=10,
        type=int,
        help="Number of attempts to retry downloading fragments (default is 10)",
    )
    parser.add_argument("--fragment-abort", action="store_false", help="Abort if fail to download fragment (default off)")

    parser.add_argument("input", help="URL or file containing list of links")

    args = parser.parse_args()

    username = args.email
    password = args.password
    input_value = args.input
    concurrent_fragments = args.concurrent_fragments
    show_flag = args.show
    fragment_retries = args.fragment_retries
    fragment_abort = args.fragment_abort

    if show_flag:
        show_mode = True
    else:
        show_mode = False

    if input_value.endswith(".txt"):
        process_links_from_file(
            username, password, input_value, concurrent_fragments, show_mode, fragment_retries, fragment_abort
        )
    else:
        if validators.url(input_value):
            url_parts = input_value.split("/")
            if 'roosterteeth.com' in url_parts and 'series' in url_parts:
                parser = RoosterTeethParser()
                episode_links = parser.get_episode_links(input_value)
                if episode_links is not None:
                    process_links_from_list(username, password, episode_links, concurrent_fragments, show_mode, fragment_retries, fragment_abort, input_value)
                else:
                    print(f"something went wrong with parsing: {input_value}. Try again or check your links")
                    logging.critical(f"parsing failed for: {input_value}")
                    exit()

            elif 'roosterteeth.com' in url_parts and 'watch' in url_parts:
                show_stuff(username, password, input_value, concurrent_fragments, show_mode, fragment_retries, fragment_abort)
            else:
                print("Unsupported RT URL. Only supports Series and Episodes")
                exit()
        else:
            print(f"invalid url: {input_value}. Exiting.")
            logging.warning(f"invalid url: {input_value}. Exiting.")
            exit()

if __name__ == "__main__":
    raise SystemExit(main())
