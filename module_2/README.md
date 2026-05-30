# Module 2 README

## Instructions
PLACE HOLDER





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