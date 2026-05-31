import urllib3
from urllib import parse

def scrape(base_url, pageNum):
    # Create URL using the page number
    pageString = (f"survey?page={pageNum}")
    webpageUrl = parse.urljoin(base_url, pageString)

    # Make a request to the server for the URL
    http = urllib3.PoolManager()
    response = http.request(
        "GET",
        webpageUrl,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    if response.status == 200:          
        print(response.status) # HTTP status code
        print(f"Successfully loaded webpage: {webpageUrl}") 
        print("") 

    # Read the html data stored on the webpage
    html_data = response.data.decode("utf-8")

    return html_data

    # td class="tw-py-5 tw-px-3 tw-text-sm --> indicates start of new application
    # tw-border-non --> meta data for each applicant

    # scrape FUNCTION END