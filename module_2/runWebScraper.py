from urllib import parse
import urllib3
from webScraper import scrape


# ================
# Define Constants 
# ================
BASE_URL = "https://www.thegradcafe.com"
totalPages = 2

for pageNum in range(1, totalPages+1):

    scrape(BASE_URL, pageNum)

    





    # Create URL using the page number
    pageString = (f"survey?page={pageNum}")
    webpageUrl = parse.urljoin(BASE_URL, pageString)

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

    scrape(html_data)





    





# confirmRobot.confirmRobot(BASE_URL)