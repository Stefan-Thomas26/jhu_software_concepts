# Notes

# Using URLlib3
from urllib.request import urlopen
import json

url = #insert url here

# open the web page
page = urlopen(url);

# extract thet html from the page
htm_bytes = page.read() # now we have Bytes

# Load Json object
washington_weather = json.loads(html_bytes) # now a giant JSON ojbect

# What's the current temperature
print(f"Current temperature in D.C is:
      {washington_weather['properties']['periods'][0]['temperature']}")

# Thought processes here
# Thought bout where to get free weather data to
# Look at API stucutre and how they host their data



# HANDLING URL ERRORS
from urllib import error, request
url = # insert website here

try:
    response = request.urlopen(url)

except error.HTTPError as err:
    if err.code = 400:
        print("Bad Request!")
    else:
        print(f"An HTTP error has occured: {err}")


# HOW DO WE SCALE THIS to look at weather for multiple cities
import jsonfrom urllib import parse, requests
url = #insert url here

parse = parse.urlparse(url)


path = parsed.path


location_path = { "DC" : specific extension here
                    "NYC"
                }

for key in location_path:
    location_url = parse.urljoin(url, location_path[key])
    page = request.urlopen(location_url)
    htm_bytes = page.read()
    weather=  json.loads(html_bytes)


robot.txt file outliens paths where you are not allowed to access 


# ================================
#  Parsing crawler access
from urllib import parse, robotparse

agent = "stefan"

url = "https://www.thegradcafe.com/"

# set up a parser with the website
parser = robotparse.RobotFileParser(url)
parser.set_url(parse.urljoin(url,'robots.txt'))
parser.read()

# look through the following paths to see if we have access there
paths = [
    "/",
    "/cgi-bin/",
    "/admin",
    "survey/?program=Comuter+Science"
]



# USING REGULAR EXPRESSIONS
import re # this library contains the regex tooling

string = "Welcome to EN605.256: modern software concepts in Python!"

pattern = "[A-Za-z]{2}[0-9]*\.[0-9]+"

print(re.search(pattern,string)


re.split()

re.sub() --> basically a find and replace function

# pythex --> online tool that helps create and text regex queries









