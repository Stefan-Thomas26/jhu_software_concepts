# Module 3 — Grad Café Data Analysis

This Flask web application scrapes graduate school application data from [thegradcafe.com](https://www.thegradcafe.com), stores it in a PostgreSQL database, and displays SQL-driven analysis results on a dynamic webpage.

---

## Project Structure

```
module_3/
├── app.py                            # Flask application and routes
├── load_data.py                      # PostgreSQL database creation and data loading
├── query_data.py                     # SQL queries for analysis
├── configuration.py                  # Loads credentials from userConfig.json
├── userConfig.json                   # Local credentials (NOT committed to GitHub)
├── requirements.txt                  # Python dependencies
├── limitations.pdf                   # Written reflection on data limitations
├── templates/
│   └── index.html                    # Flask HTML template
├── static/
│   └── style.css                     # Page styling
└── module_2/
    ├── runWebScraper.py              # Scraper entry point (full scrape & update scrape modes)
    ├── applicant_data.json           # Full initial scrape archive (raw)
    ├── llm_extended_applicant_data.json        # Full initial scrape archive (LLM-enriched)
    ├── new_applicant_data.json                 # Latest update batch (raw, overwritten each pull)
    ├── new_llm_extended_applicant_data.json    # Latest update batch (LLM-enriched, overwritten each pull)
    ├── webScraper/
    │   ├── scrapeData.py             # HTTP requests to Grad Café
    │   ├── cleanData.py              # HTML parsing with BeautifulSoup
    │   ├── saveData.py               # JSON file saving with append logic
    │   ├── loadData.py               # JSON file loading and viewing
    │   ├── confirmRobot.py           # Checks robots.txt before scraping
    │   └── GradApplicant.py          # Dataclass for a single applicant entry
    └── llm_hosting/
        └── app.py                    # LLM enrichment logic lives here
```

---

## Python Dependencies

- See `requirements.txt` file

---

## Setup

### 1. Clone the repository and cd into module_3

```bash
git clone git@github.com:Stefan-Thomas26/jhu_software_concepts.git
cd module_3
```

### 2. Configure credentials

Create a `userConfig.json` file in the `module_3/` folder:

```json
[{
    "user":      "your_postgres_username",
    "password":  "your_postgres_password",
    "host":      "localhost",
    "dataFile": "module_2/llm_extended_applicant_data.json"
}]
```

---

## Running the Application

All commands below assume you are running from the `module_3/` folder.

### Step 1 — Initial full scrape (first time only)

You need to scrape Grad Cafe and run the output JSON file through the LLM before runnning the application. This action produces files that will not be changed in the future.

You can do this by running the following:

```bash
cd module_2
python runWebScraper.py --mode full --part both
cd ..
```

This produces two archive files inside `module_2/`:
- `applicant_data.json` — all raw scraped entries
- `llm_extended_applicant_data.json` — LLM-enriched entries (used to load the DB)


> These files should never be overwritten by subsequent update runs.

### Step 2 — Start the Flask app

Within the `module_3/` folder, run:

```bash
python app.py
```

Next, copy the following URL to a browser:

```
http://192.168.0.44:8080
```


### Step 3 — Create the database

The webpage _should_ show empty values or zeros upon startup, assuming a database has not already been found and linked to. 

Click the **Create Database** button on the webpage. This will:
1. Create a PostgreSQL database called `applicantdata`
2. Load all entries from `module_2/llm_extended_applicant_data.json` into it

### Step 4 — View the analysis

Once the database is created, the page will display results for all SQL queries automatically. Click **Update Analysis** to update the results.

---

## Pulling New Data

Click the **Pull Data** button on the webpage. This runs a three-step background process:

1. **Scrape** — scrapes Grad Café page by page, checking each entry's URL against the database. Stops as soon as a full page of already-seen entries is found. Saves new entries to `module_2/new_applicant_data.json`.
2. **Run new data through LLM** — enriches the new entries from `module_2/new_applicant_data.json` with generated university and program names. This is output to a file `module_2/new_llm_extended_applicant_data.json`.
3. **DB load** — inserts the enriched new entries into PostgreSQL. Duplicate entries are safely skipped.


---

## Database Columns

Table name: `applicants`

| Column | Type | Description |
|--------|------|-------------|
| `p_id` | INTEGER | Unique identifier |
| `program` | TEXT | University and program combined |
| `degreeType` | TEXT | Degree type (PhD, Masters, etc.) |
| `datePosted` | DATE | Date entry was posted |
| `status` | TEXT | Admission status (Accepted, Rejected, etc.) |
| `statusDate` | TEXT | Date of status decision |
| `semester` | TEXT | Start term (e.g. Fall 2026) |
| `citizenship` | TEXT | American, International, or Other |
| `gpa` | FLOAT | Applicant GPA |
| `gre` | FLOAT | GRE Quantitative score |
| `gre_v` | FLOAT | GRE Verbal score |
| `gre_aw` | FLOAT | GRE Analytical Writing score |
| `comment` | TEXT | Applicant comments |
| `url` | TEXT | Link to original Grad Café post |
| `llm_generated_program` | TEXT | LLM-generated program name |
| `llm_generated_university` | TEXT | LLM-generated university name |

---

## SQL Analysis Questions

| # | Question |
|---|----------|
| Q1 |How many entries do you have in your database who have applied for Fall 2026? |
| Q2 | What percentage of entries are from international students (not American or Other) (to two decimal places)? |
| Q3 | What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics? |
| Q4 | What is their average GPA of American students in Fall 2026? |
| Q5 | What percent of entries for Fall 2026 are Acceptances (to two decimal places)? |
| Q6 | What is the average GPA of applicants who applied for Fall 2026 who are Acceptances? |
| Q7 | How many entries are from applicants who applied to JHU for a masters degrees in Computer Science? |
| Q8 | How many entries from 2026 are acceptances from applicants who applied to Georgetown University, MIT, Stanford University, or Carnegie Mellon University for a PhD in Computer Science? |
| Q9 | Do you numbers for question 8 change if you use LLM Generated Fields (rather than your downloaded fields)? |
| Q10 | What is the PhD rejection rate in 2025 vs 2026? |
| Q11 | What is the average GPA of accepted vs rejected PhD applicants in 2026? |

---

## Runtime Aruguments for _runWebScraper.py_

If you need to run the scraper manually from the command line, move into `module_2/` and then run one of the following:

```bash
# Full parallel scrape + LLM enrichment
# This should only be called once when generated initial scraped data files
python runWebScraper.py --mode full --part both

# Incremental update scrape + LLM enrichment (subsequent pulls)
python runWebScraper.py --mode update --part both

# Scrape only, DO NOT run LLM
python runWebScraper.py --mode full --part 1

# Run LLM ONLY, on an existing scraped file
python runWebScraper.py --mode full --part 2

# User-defined number of LLM worker processes (USE CAUTION)
python runWebScraper.py --mode full --part both --workers 4
```

---

## Troubleshooting

Here is a list of few ways to navigate errors you may encounter while running this app.

***ERROR: Page crashes on load with "database does not exist"***
- The app should take care of this — the page will load with empty results and a "—" placeholder. Click **Create Database** to set up your database.

***ERROR: "other users are accessing the database" error when deleting***

- Call `delete_database("applicantdata")` from `load_data.py` directly — it terminates all active sessions before dropping.

***ERROR: LLM column errors on insert***

- The table was created before the LLM columns were added. Drop the table and recreate the database via the **Create Database** button.

***ERROR: Import errors when running `runWebScraper.py` as subprocess***
- `runWebScraper.py` adds `module_3/` to `sys.path` automatically so it can find `configuration.py`. Be sure to not move files such that the expected file structure is broken.