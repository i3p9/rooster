import requests
from urllib.parse import urlparse, parse_qs


class RoosterTeethParser:
    _API_BASE = "https://svod-be.roosterteeth.com"
    _API_BASE_URL = f"{_API_BASE}/api/v1"
    HEADERS = {
        "authority": "svod-be.roosterteeth.com",
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "client-debug-id": "0.9053162591183688",
        "client-id": "4338d2b4bdc8db1239360f28e72f0d9ddb1fd01e7a38fbb07b4b1f4ba4564cc5",
        "client-type": "web",
        "content-type": "application/json",
        "origin": "https://roosterteeth.com",
    }

    def _extract_series_id(self, url):
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split("/")
        if len(path_parts) >= 3 and path_parts[1] == "series":
            return path_parts[2]
        return None

    def _extract_sesaon_links_in_order(self, id, season_number):
        api_url = f"https://svod-be.roosterteeth.com/api/v1/shows/{id}/seasons?order=asc&order_by"
        response = requests.request("GET", api_url, headers=self.HEADERS, data={})
        if response.ok:
            seasons_data = response.json()
            data = []
            for season in seasons_data["data"]:
                if season_number is not None:
                    if int(season["attributes"]["number"]) == int(season_number):
                        season_link = f"{self._API_BASE}{season['links']['episodes']}&page=1&per_page=999"
                        return [season_link]
                if season["links"]["episodes"]:
                    season_link = f"{self._API_BASE}{season['links']['episodes']}&page=1&per_page=999"
                    data.append(season_link)
            return data
        return None

    def _extract_bonus_series(self, id):
        api_url = f"https://svod-be.roosterteeth.com/api/v1/shows/{id}"
        response = requests.request("GET", api_url, headers=self.HEADERS, data={})
        if response.ok:
            show_data = response.json()
            for show in show_data["data"]:
                if show["links"]["bonus_features"]:
                    return f"{self._API_BASE}{show['links']['bonus_features']}"
                return None

    def _extract_season_number(self, url):
        query_params = parse_qs(urlparse(url).query)
        return query_params.get("season", [None])[0]

    def _fetch_episode_links(self, season_links):
        # Construct the API URL
        print(f"Found {len(season_links)} seasons. Grabbing episode lists for them...")
        episode_links = []
        season_count = 1
        for link in season_links:
            response = requests.get(link)
            response.raise_for_status()
            data = response.json()
            print(
                f"Parsing Season: {'Bonus Season (Checking if Exists)' if 'bonus_features' in link else season_count}..."
            )

            for episode in data.get("data", []):
                if episode["canonical_links"]["self"]:
                    link = (
                        f"https://roosterteeth.com{episode['canonical_links']['self']}"
                    )
                    episode_links.append(link)
                else:
                    print("no links found on season data")
            season_count += 1

        if episode_links:
            return episode_links
        else:
            return None

    def get_episode_links(self, url):
        series_id = self._extract_series_id(url)
        season_number = self._extract_season_number(url)
        if not series_id:
            raise ValueError("Invalid Rooster Teeth series URL")

        # Gets seasons
        if not season_number:
            # whole series
            series_slugs = self._extract_sesaon_links_in_order(series_id, season_number)
            bonus_content = self._extract_bonus_series(series_id)
            if series_slugs is not None:
                if bonus_content is not None:
                    series_slugs.append(bonus_content)
        else:
            # single season
            series_slugs = self._extract_sesaon_links_in_order(series_id, season_number)

        # Fetch episode links
        episode_links = self._fetch_episode_links(series_slugs)
        print(f"Found {len(episode_links)} episodes across {url}")
        if episode_links:
            return episode_links
        else:
            return None


# Usage Example
# parser = RoosterTeethParser()
# episode_links = parser.get_episode_links("https://roosterteeth.com/series/rt-podcast")
# print("Episode Links:", episode_links)
