# Module 4 — Testing and Documentation

This Flask web application scrapes graduate school application data from [thegradcafe.com](https://www.thegradcafe.com), stores it in a PostgreSQL database, and displays SQL-driven analysis results on a dynamic webpage.

---

## Project Structure - UPDATE

```
module_4/
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
1. Create a PostgreSQL database called `applicantdata`


### Step 3 — Create the database

The webpage _should_ show empty values or zeros upon startup, assuming a database has not already been found and linked to. 

Click the **Create Database** button on the webpage. This will:
2. Load all entries from `module_2/llm_extended_applicant_data.json` into it

### Step 4 — View the analysis


---



---

---



## Troubleshooting
