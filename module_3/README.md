# Module 3 — Grad Café Data Analysis

A Flask web application that scrapes graduate school application data from [thegradcafe.com](https://www.thegradcafe.com), stores it in a PostgreSQL database, and displays SQL-driven analysis results on a dynamic webpage.

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
    ├── runWebScraper.py              # Scraper entry point (full + update modes)
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

## Prerequisites

- Python 3.10+
- PostgreSQL (local install or Replit DB)
- pip

---

## Setup

### 1. Clone the repository and cd into module_3

```bash
git clone <your-ssh-url>
cd module_3
```

### 2. Configure credentials

Create a `userConfig.json` file in the `module_3/` directory:

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

All commands below assume you are running from the `module_3/` directory.

### Step 1 — Initial full scrape (first time only)

You need to scrape Grad Cafe and run the data through the LLM before runnning the application. This produces files that will not be changed in the future.

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

Then copy the following URL to a browser:

```
http://192.168.0.44:8080
```


### Step 3 — Create the database

Click the **Create Database** button on the webpage. This will:
1. Create a PostgreSQL database called `applicantdata`
2. Load all entries from `llm_extended_applicant_data.json` into it

### Step 4 — View the analysis

Once the database is created, the page will display results for all SQL queries automatically. Click **Update Analysis** to update the results.

---

## Pulling New Data

Click the **Pull Data** button on the webpage. This runs a three-step background process:

1. **Scrape** — scrapes Grad Café page by page, checking each entry's URL against the database. Stops as soon as a full page of already-seen entries is found. Saves new entries to `new_applicant_data.json`.
2. **LLM enrichment** — enriches the new entries with standardised university and program names → `new_llm_extended_applicant_data.json`.
3. **DB load** — inserts the enriched new entries into PostgreSQL. Duplicate entries are safely skipped.

The status bar shows live progress through each step. Once complete, click **↻ Update Analysis** to refresh the results.


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
| Q1 | How many entries applied for Fall 2026? |
| Q2 | What percentage of entries are international students? |
| Q3 | Average GPA, GRE, GRE Verbal, and GRE AW across all applicants? |
| Q4 | Average GPA of American students in Fall 2026? |
| Q5 | What percent of Fall 2026 entries are Acceptances? |
| Q6 | Average GPA of Fall 2026 acceptances? |
| Q7 | How many entries applied to JHU for a Masters in Computer Science? |
| Q8 | How many 2026 acceptances from Georgetown, MIT, Stanford, or CMU for PhD CS? |
| Q9 | Do Q8 numbers change using LLM-generated fields? |
| Q10 | PhD rejection rate in 2025 vs 2026? |
| Q11 | Average GPA of accepted vs rejected PhD applicants in 2026? |

---

## Scraper CLI Reference

If you need to run the scraper manually from the command line, run from inside `module_2/`:

```bash
# Full parallel scrape + LLM enrichment (initial load only)
python runWebScraper.py --mode full --part both

# Incremental update scrape + LLM enrichment (subsequent pulls)
python runWebScraper.py --mode update --part both

# Scrape only, no LLM
python runWebScraper.py --mode full --part 1

# LLM enrichment only, on an existing scraped file
python runWebScraper.py --mode full --part 2

# Custom number of LLM worker processes
python runWebScraper.py --mode full --part both --workers 4
```

---

## Troubleshooting

**Page crashes on load with "database does not exist"**
The app handles this gracefully — the page will load with empty results and a "—" placeholder. Click **⚙ Create Database** to set it up.

**"other users are accessing the database" error when deleting**
Call `delete_database("applicantdata")` from `load_data.py` directly — it terminates all active sessions before dropping.

**LLM column errors on insert**
The table was created before the LLM columns were added. Drop the table and recreate the database via the **⚙ Create Database** button.

**Import errors when running `runWebScraper.py` as subprocess**
`runWebScraper.py` adds `module_3/` to `sys.path` automatically so it can find `configuration.py`. Make sure you have not moved files out of the expected directory structure.
