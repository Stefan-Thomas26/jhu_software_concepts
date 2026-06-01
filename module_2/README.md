# Module 2 - Web Scraping

***Due Date***: May 31, 2026


## Personal Information
***Author:*** Stefan Thomas

***Hopkins ID:*** 6B9051


## Approach

I completed this assignment in two phases:
1) Scrape, clean, and output the data stored on [thegradcafe.com](https://www.thegradcafe.com/survey) as a JSON file

2) Using the output JSON file from Step 1, pass it into the simple LLM provided to further enrich the JSON list for each applicant entry

### File Organization
Here is the file organization of the `module_2` folder:

create a runWebScraper module to store the following 
    - confirmRobot.py
    - scrapeData.py
    - cleanData.py
    - saveData.py
    - loadData.py
    - GradApplicant.py


## Known Bugs 

    `




# TO BE DELETED BELOW
Data we want to collect from GradCafe
- School
- Program ()
    - Department
    - Type: Masters, PhD
- Decision Data
- Comments
- Admission Semester
- GPA, if given
- Date added



https://www.thegradcafe.com/survey?page=10

How do I comb through all multiple pages of data? I can do a for loop chaning the 'page=10' spot and then the webpage jumps to that new page.
This is powerful because then I can go through 10000 pages, and get loads of data, althoguth processing may take some time. May want to start small with 10 pages, and then increase it when things
are looking good and the output JSON is everything I want


TIPS and TRICKS
- use urllib to manage URLS, like gradcafe.com
- use selenium to load the URL, wait unitl javascript has pulled in the
    -extract the rendered html using selnium page_source
- parallelize this 

Steps
[] Scrape 1 page of data and get the data that I want
[] Update framework to manage looping over multiple pages of data
    [] Parallelize this process


## Using selenium
use urllib to manage URLs