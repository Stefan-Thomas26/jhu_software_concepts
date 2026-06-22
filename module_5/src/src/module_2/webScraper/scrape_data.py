"""Scrape Data Module will return raw html from a page from GradCafe"""

import time
from urllib import parse
import urllib3

HTTP = urllib3.PoolManager()


def scrape_data(base_url, page_num):
    """Function to scrape data from webpage and return the raw html"""

    page_string = f"survey?page={page_num}"
    webpage_url = parse.urljoin(base_url, page_string)

    for attempt in range(5):
        try:
            response = HTTP.request(
                "GET",
                webpage_url,
                headers={"User-Agent": "Mozilla/5.0"},
            )

            if response.status == 200:
                return response.data.decode("utf-8")

        except urllib3.exceptions.HTTPError as e:
            print(f"Attempt {attempt + 1} failed: {e}")

        time.sleep(2)

    raise RuntimeError(
        f"Failed to scrape {webpage_url} after 5 attempts"
    )
