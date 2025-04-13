# R&D Job Finder

A tool to find companies actively hiring for R&D and new product development roles by analyzing job postings.

## Features

- Scrapes job listings from Google Jobs
- Analyzes job descriptions for development intent
- Stores data in Google Sheets
- Interactive Streamlit dashboard
- Automated updates via GitHub Actions
- Real-time data with no duplicates

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd rnd-job-finder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google Sheets API:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Google Sheets API
   - Create a service account and download credentials
   - Save credentials as `credentials.json` in the project root

4. Create a Google Sheet and get its ID from the URL

5. Set up environment variables:
```bash
echo "SPREADSHEET_ID=your_sheet_id" > .env
```

6. Set up GitHub Secrets:
   - Go to your repository settings
   - Add these secrets:
     - `SPREADSHEET_ID`: Your Google Sheet ID
     - `GOOGLE_CREDENTIALS`: Contents of your credentials.json file

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Access the dashboard at `http://localhost:8501`

3. The scraper will automatically run every 6 hours via GitHub Actions

## Manual Scraping

To run the scraper manually:
```python
from job_scraper import JobScraper

scraper = JobScraper()
queries = ["R&D", "product development", "innovation"]
locations = ["United States", "Europe", "Asia"]
scraper.run_scraper(queries, locations)
```

## Contributing

Feel free to submit issues and enhancement requests! 