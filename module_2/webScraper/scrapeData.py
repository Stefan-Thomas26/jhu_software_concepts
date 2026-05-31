from urllib import parse
import urllib3
import time

# Make global pool manager
HTTP = urllib3.PoolManager()

def scrape_data(base_url, pageNum):
    # Create URL using the page number
    pageString = (f"survey?page={pageNum}")
    webpageUrl = parse.urljoin(base_url, pageString)
    
    for attempt in range(5):
        try:
            # Make a request to the server for the URL
            response = HTTP.request(
                "GET",
                webpageUrl,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            if response.status == 200:          
                # Read the html data stored on the webpage
                html_data = response.data.decode("utf-8")
                return html_data

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            
            if attempt == 4:
                raise
            # Give server a quick break if a request fails
            time.sleep(2)

    # td class="tw-py-5 tw-px-3 tw-text-sm --> indicates start of new application
    # tw-border-non --> meta data for each applicant

    # scrape FUNCTION END