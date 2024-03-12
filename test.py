import requests
from urllib.parse import urlparse


def get_api_url(url):
    parsed_url = urlparse(url)
    slug = parsed_url.path.rstrip("/").split("/")[-1]
    api_url = f"https://roosterteeth.fhm.workers.dev/findEpisode?slug={slug}"
    return api_url


def get_episode_data_from_api(url):
    base_url = get_api_url(url)
    print("base_url: ", base_url)
    response = requests.get(base_url)
    print(response)


get_episode_data_from_api("https://roosterteeth.com/watch/red-vs-blue-vga-fortnite")
