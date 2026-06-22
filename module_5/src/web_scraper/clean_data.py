"""Module for parsing and cleaning HTML data from grad school applicant pages."""

import re
from urllib import parse

from bs4 import BeautifulSoup

from . import grad_applicant


# ===================================
# Check if the input table row is the
# start of a new student entry
# ===================================
def _is_new_student(row):
    """Return True if the table row marks the start of a new student entry."""
    is_new_student_entry = bool(
        row.select_one("div.tw-font-medium.tw-text-gray-900.tw-text-sm")
    )
    return is_new_student_entry


# ===================================
# Parse table row that contains pertinent
# grad applicant data
# ===================================
def _parse_main_row(row, base_url, applicant):
    """Parse the main table row and populate core applicant fields."""
    applicant.university = row.select_one(
        "div.tw-font-medium.tw-text-gray-900.tw-text-sm"
    ).get_text(strip=True)

    # Get program and degree type from 2nd <td> element
    spans = row.select("td:nth-of-type(2) span")
    applicant.program = spans[0].get_text(strip=True)
    applicant.degree_type = spans[1].get_text(strip=True)
    applicant.date_posted = row.select_one("td:nth-of-type(3)").get_text(strip=True)

    # Get status
    status_td = row.select_one("td:nth-of-type(4)")
    status_text = status_td.get_text(strip=True)
    if " on " in status_text:
        parts = status_text.split(" on ", 1)
        applicant.status = parts[0].strip()
        applicant.status_date = parts[1].strip()
    else:
        applicant.status = status_text
        applicant.status_date = None

    link_tag = row.find("a")
    applicant.url = parse.urljoin(base_url, link_tag["href"]) if link_tag else None

    return applicant


# ===================================
# Parse table row that contains other
# grad applicant data
# ===================================
def _parse_details_row(row, applicant):
    """Parse the details row and populate GRE, GPA, semester, and citizenship fields."""
    applicant.semester = None
    applicant.citizenship = None
    applicant.gre = None
    applicant.gre_v = None
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
        # GRE general score
        elif text.startswith("GRE"):
            try:
                applicant.gre = float(re.search(r"\d{3}", text).group())
            except ValueError:
                pass
        # GPA
        elif text.startswith("GPA"):
            applicant.gpa = float(text.replace("GPA", "").strip())

    return applicant


# =============================
# Parse table row that contains
# grad applicant comments
# =============================
def _parse_comment_row(row, applicant):
    """Parse the comment row and populate the applicant comment field if present."""
    contains_comment = bool(row.find("p"))
    if contains_comment:
        applicant.comment = row.get_text("p", strip=True)
    else:
        applicant.comment = None

    return applicant


# =============================
# Clean the input html and extract
# and organize pertinent data
# for each grad school applicant
# =============================
def clean_data(html_data, base_url):
    """Parse HTML and return a list of GradApplicant objects from the page."""
    soup = BeautifulSoup(html_data, "html.parser")
    table_rows = soup.find_all("tr")
    applicants_from_current_page = []

    for index, row in enumerate(table_rows):
        if _is_new_student(row):
            applicant = grad_applicant.GradApplicant()
            _parse_main_row(row, base_url, applicant)

            # Parse the next row for additional details
            if index + 1 < len(table_rows):
                details_row = table_rows[index + 1]
                _parse_details_row(details_row, applicant)

            # Parse the following row for optional comment
            if index + 2 < len(table_rows):
                comment_row = table_rows[index + 2]
                _parse_comment_row(comment_row, applicant)

            applicants_from_current_page.append(applicant)

    return applicants_from_current_page
