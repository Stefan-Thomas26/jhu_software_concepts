from bs4 import BeautifulSoup
from webScraper import GradApplicant
import re
from urllib import parse


# ===================================
# Check if the input table row is the
# start of a new student entry
# ===================================
def _is_new_student(row):
    # define a function to assess if row is a the beginning of a student entry
    # From observing the html, the lines with the university name have the following
    # divider pattern : "div.tw-font-medium.tw-text-gray-900.tw-text-sm"
    isNewStudentEntry = bool(row.select_one("div.tw-font-medium.tw-text-gray-900.tw-text-sm"))
    return(isNewStudentEntry)
    # _is_new_student FUNCTION END


# ===================================
# Parse table row that contains pertinent
# grad applicant data
# ===================================
def _parse_main_row(row, base_url, applicant):
    applicant.university = row.select_one("div.tw-font-medium.tw-text-gray-900.tw-text-sm").get_text(strip=True)

    # in the 2nd <td> element in the html, find all <span> elements
    spans = row.select("td:nth-of-type(2) span")
    applicant.program = spans[0].get_text(strip=True)
    applicant.degreeType = spans[1].get_text(strip=True)
    applicant.datePosted = row.select_one("td:nth-of-type(3)").get_text(strip=True)
    applicant.status = row.select_one("td:nth-of-type(4)").get_text(strip=True)
    
    link_tag = row.find("a")
    applicant.url = parse.urljoin(base_url, link_tag["href"]) if link_tag else None
    
    return (applicant) 
    # _parse_main_row FUNCTION END


# ===================================
# Parse table row that contains other
# grad applicant data
# ===================================
def _parse_details_row(row, applicant):
    # initialzie data
    applicant.semester = None
    applicant.citizenship   = None 
    applicant.gre  = None
    applicant.gre_v  = None
    applicant.gre_aw = None
    applicant.gpa = None

    badges = row.select("div.tw-inline-flex")
    
    for b in badges:
        text = b.get_text(" ", strip=True)

        # Semester
        if re.match(r"(Fall|Spring|Summer|Winter)\s+\d{4}", text):
            applicant.semester = text

        # Citizenship
        elif text in ["International", "American", "Other"]:
            applicant.citizenship = text 
        # GRE Verbal
        elif text.startswith("GRE V"):
            applicant.gre_v = float(text.replace("GRE V", "").strip())
        # GRE Analytical Writing
        elif text.startswith("GRE AW"):
           applicant.gre_aw = float(text.replace("GRE AW", "").strip())

        elif text.startswith("GRE"):
            # plain GRE score
            try:
                applicant.gre = int(re.search(r"\d{3}", text).group())
            except:
                pass

        elif text.startswith("GPA"):
            applicant.gpa = float(text.replace("GPA", "").strip())

    return (applicant)
    # _parse_details_row FUNCTION END


# =============================
# Parse table row that contains
# grad applicant comments 
# =============================
def _parse_comment_row(row, applicant):
    containsComment = bool(row.find("p"))
    if containsComment:
        applicant.comment = row.get_text("p", strip=True) 
    else:
        applicant.comment = None

    return applicant
    # _parse_comment_row FUNCTION END


# =============================
# Clean the input html and extract
# and organize pertinent data
# for each grad school applicant
# =============================
def clean_data(html_data, base_url):
    
    # Create a BeautifulSoup instance
    soup = BeautifulSoup(html_data, "html.parser")
    
    # Get table rows from the html
    #tr is table row, which is each entry in thew webpage
    tableRows = soup.find_all("tr") 
    
    # Initialize lists to store grad applicant data
    applicantsFromCurrentPage = []

    # Looping through all table row elements from html
    for index, row in enumerate(tableRows): # this gives an (index, row) pair
        if _is_new_student(row):
            # print("======= NEW STUDENT =========")
            applicant = GradApplicant.GradApplicant()
            _parse_main_row(row, base_url, applicant)

            # parse the next row, which contains more details
            if (index+1 < len(tableRows)):
                detailsRow = tableRows[index+1]
                _parse_details_row(detailsRow, applicant)
            
            # parse the next next row, which SOMETIMES contains a comment.
            # only do this if the next row contains a <p> element
            if (index+2 < len(tableRows)):
                commentRow = tableRows[index+2]
                _parse_comment_row(commentRow, applicant)

            # for name, value in vars(applicant).items():
                # print(f"{name}:   {value}")

            applicantsFromCurrentPage.append(applicant)
        else:
            continue

    return applicantsFromCurrentPage
    # clean_data FUNCTION END
