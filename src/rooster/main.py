#!/usr/bin/python3 -B
from .downloader import show_stuff
import argparse


def process_links_from_file(username, password, filename, concurrent_fragments):
    with open(filename, "r") as file:
        links = file.readlines()
        num_links = len(links)
        print(f"Found {num_links} links.")

        for index, line in enumerate(links, start=1):
            print(f"Downloading link {index} of {num_links}: {line.strip()}")
            show_stuff(username, password, line.strip(), concurrent_fragments)


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

    parser.add_argument("input", help="URL or file containing list of links")

    args = parser.parse_args()

    username = args.email
    password = args.password
    input_value = args.input
    concurrent_fragments = args.concurrent_fragments
    if input_value.endswith(".txt"):
        process_links_from_file(username, password, input_value, concurrent_fragments)
    else:
        show_stuff(username, password, input_value, concurrent_fragments)


if __name__ == "__main__":
    raise SystemExit(main())
