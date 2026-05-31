import urllib3
import confirmRobot
from urllib import parse

from bs4 import BeautifulSoup

import re

from dataclasses import dataclass, asdict

import json


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
    print("") 

# Read the html data stored on the webpage
html_data = response.data.decode("utf-8")

soup = BeautifulSoup(html_data, "html.parser")

# !!!!!!Place the below function in a different FILE
def isNewStudent(row ):
    # define a function to assess if row is a the beginning of a student entry
    # From observing the html, the lines with the university name have the following
    # divider pattern : "div.tw-font-medium.tw-text-gray-900.tw-text-sm"
    containsUniversityName = bool(row.select_one("div.tw-font-medium.tw-text-gray-900.tw-text-sm"))
    return(containsUniversityName)

def parse_main_row(row, base_url, applicant, count):
    applicant.applicantNumber = count
    applicant.university = row.select_one("div.tw-font-medium.tw-text-gray-900.tw-text-sm").get_text(strip=True)

    # in the 2nd <td> element in the html, find all <span> elements
    spans = row.select("td:nth-of-type(2) span")
    applicant.program = spans[0].get_text(strip=True)
    applicant.degreeType = spans[1].get_text(strip=True)
    applicant.date_posted = row.select_one("td:nth-of-type(3)").get_text(strip=True)
    applicant.decision = row.select_one("td:nth-of-type(4)").get_text(strip=True)
    
    link_tag = row.find("a")
    applicant.url = parse.urljoin(base_url, link_tag["href"]) if link_tag else None
    
    return (applicant)

    # print(university)
    # print(program)
    # print(degreeType)
    # print(date_posted)
    # print(decision)
    # print(url)
    # return {
    #     "university": university,
    #     "program": program,
    #     "degree": degreeType,
    #     "date_posted": date_posted,
    #     "decision": decision,
    #     "url": url
        # }
    

def parse_details_row(row, applicant):
    # initialzie data
    # data = {
    #     "semester": None,
    #     "citizenship": None,
    #     "gre_q": None,
    #     "gre_v": None,
    #     "gre_aw": None,
    #     "gpa": None
    # }

    applicant.semester = None
    applicant.citizenship   = None 
    applicant.gre_q  = None
    applicant.gre_v  = None
    applicant.gre_aw = None
    applicant.gpa = None

    badges = row.select("div.tw-inline-flex")
    
    for b in badges:
        text = b.get_text(" ", strip=True)

        # Semester
        if re.match(r"(Fall|Spring|Summer|Winter)\s+\d{4}", text):
            # data["semester"] = text
            applicant.semester = text

        # Citizenship
        elif text in ["International", "American", "Other"]:
            # data["citizenship"] = text
            applicant.citizenship = text 
        # GRE Quant
        elif text.startswith("GRE V"):
            # data["gre_v"] = float(text.replace("GRE V", "").strip())
            applicant.gre_v = float(text.replace("GRE V", "").strip())

        elif text.startswith("GRE AW"):
            # data["gre_aw"] = float(text.replace("GRE AW", "").strip())
           applicant.gre_aw = float(text.replace("GRE AW", "").strip())

        elif text.startswith("GRE"):
            # plain GRE score
            try:
                # data["gre_q"] = int(re.search(r"\d{3}", text).group())
                applicant.gre_q = int(re.search(r"\d{3}", text).group())
            except:
                pass

        elif text.startswith("GPA"):
            # data["gpa"] = float(text.replace("GPA", "").strip())
            applicant.gpa = float(text.replace("GPA", "").strip())

    # print(data)
    return (applicant)


def parse_comment_row(row, applicant):
    containsComment = bool(row.find("p"))
    if containsComment:
        applicant.comment = row.get_text("p", strip=True) 
    else:
        applicant.comment = None

    # print(comment)
    return applicant

@dataclass
class GradApplicant:
    applicantNumber: int = None
    university: str = None
    program: str = None
    degreeType: str = None
    date_posted: str = None
    decision: str = None
    semester: str = None
    citizenship: str = None
    gpa: float = None
    gre_q: int = None
    gre_v: int = None
    gre_aw: float = None
    comment: str = None
    url: str = None


count = 0
tableRows = soup.find_all("tr") #tr is table row, which is each entry in thew webpage
allGradApplicants = []
for index, row in enumerate(tableRows):
    
    if isNewStudent(row):
        print("======= NEW STUDENT =========")
        count = count+1
        print(index)
        applicant = GradApplicant()
        parse_main_row(row,BASE_URL, applicant, count)

        # parse the next row, which contains more details
        if (index+1 < len(tableRows)):
            detailsRow = tableRows[index+1]
            parse_details_row(detailsRow, applicant)
        
        # parse the next next row, which SOMETIMES contains a comment.
        # only do this if the next row contains a <p> element
        if (index+2 < len(tableRows)):
            commentRow = tableRows[index+2]
            parse_comment_row(commentRow, applicant)

        for name, value in vars(applicant).items():
            print(f"{name}:   {value}")

        allGradApplicants.append(applicant)
    else:
        continue

allData = [asdict(student) for student in allGradApplicants]

with open("gradcafe.json", "w", encoding="utf-8") as f:
    json.dump(allData, f, indent=4)
        
        

    # view the table row html, which is the all the data associated with one entry
    # print(row.prettify())
    
    # classes = row.get("class",[])
    # print(classes)


    # tableData = row.find_all("td")
    # for datapoint in tableData:
    #     print(datapoint.prettify())

    
   
    # cells = row.find_all("td") #Find all table row data tags
    # data = [cell.get_text(strip=True) for cell in cells]
    # print(data)


# td class="tw-py-5 tw-px-3 tw-text-sm --> indicates start of new application
# tw-border-non --> meta data for each applicant

# Show all data
# print(soup.prettify())
