import urllib3, json
import confirmRobot
from urllib import parse, request
from bs4 import BeautifulSoup


# =========================================
# Define Constants % Verifiy Robot.txt file
# =========================================
BASE_URL = "https://www.thegradcafe.com"
# confirmRobot.confirmRobot(BASE_URL)


# ===============
# Scrape the Web!
# ===============
test_url = parse.urljoin(BASE_URL,"survey?page=1")

http = urllib3.PoolManager()
response = http.request(
    "GET",
    test_url,
    headers={"User-Agent": "Mozilla/5.0"}
)

if response.status == 200:
    print(response.status) # HTTP status code
    print("Successfully loaded webpage")  

# Read the html data stored on the webpage
html_data = response.data.decode("utf-8")

soup = BeautifulSoup(html_data, "html.parser")

tableRows = soup.find_all("tr") #tr is table row, which is each entry in thew webpage
for entry in tableRows:
    print(entry.prettify(), end="\n" * 2)
    for row in tableRows:
        cells = row.find_all("td")
        data = [cell.get_text(strip=True) for cell in cells]
        print(data)

    break

# Show all data
# print(soup.prettify())


# print all the text
# text = soup.get_text()
# spaceless_text = text.replace("\n\n", "")
# print(spaceless_text)