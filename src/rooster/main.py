#!/usr/bin/python3 -B
from .downloader import show_stuff
import argparse
import logging
import os


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
    username, password, filename, concurrent_fragments, show_mode
):
    with open(filename, "r") as file:
        links = file.readlines()
        num_links = len(links)
        print(f"Found {num_links} links.")

    for index, line in enumerate(links, start=1):
        print(f"Downloading link {index} of {num_links}: {line.strip()}")
        try:
            show_stuff(
                username, password, line.strip(), concurrent_fragments, show_mode
            )
        except Exception as e:
            # Log the exception
            print(f"Error occurred while processing link {index}: {line.strip()}")
            logging.critical(
                f"Error occurred while processing link {index}: {line.strip()}"
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

    parser.add_argument("input", help="URL or file containing list of links")

    args = parser.parse_args()

    username = args.email
    password = args.password
    input_value = args.input
    concurrent_fragments = args.concurrent_fragments
    show_flag = args.show

    if show_flag:
        show_mode = True
    else:
        show_mode = False

    if input_value.endswith(".txt"):
        process_links_from_file(
            username, password, input_value, concurrent_fragments, show_mode
        )
    else:
        show_stuff(username, password, input_value, concurrent_fragments, show_mode)


if __name__ == "__main__":
    raise SystemExit(main())
