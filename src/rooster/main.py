#!/usr/bin/python3 -B
from .downloader import show_stuff
import argparse


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

    parser.add_argument("url", help="URL to be processed")

    args = parser.parse_args()

    username = args.email
    password = args.password
    url = args.url
    concurrent_fragments = args.concurrent_fragments
    show_stuff(username, password, url, concurrent_fragments)


if __name__ == "__main__":
    raise SystemExit(main())
