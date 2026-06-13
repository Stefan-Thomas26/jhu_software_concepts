# Creating a BeautifulSoup object

from bs4 import BeautifulSoup
from urllib3.request import urlopen

# list of courses offered at JHU
url = "https://e-catalogue.jhu.edu./course-serach/"


# open web page
page = urlopen(url)
html = page.read().decode("utf-8")
soup = BeautifulSoup(html, "html.parser")

text = soup.get_text()
spaceless_text = text.replace("\n\n", "")
print(spaceless_text)
