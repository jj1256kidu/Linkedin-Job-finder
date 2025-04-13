# R&D Job Finder

An automated tool that scrapes and analyzes job postings to find companies actively hiring for R&D and product development roles. The data is automatically updated to Google Sheets every 6 hours.

## Features

- Scrapes job listings from multiple sources
- Analyzes job descriptions for R&D and development keywords
- Automatically updates Google Sheets with fresh data
- Streamlit dashboard for data visualization
- GitHub Actions automation for regular updates

## Setup

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up Google Sheets:
- Create a Google Sheet named "Product developement"
- Create a sheet named "Data" within it
- Share the sheet with the service account email from your credentials

4. Set up GitHub Actions:
- Go to repository Settings > Secrets and Variables > Actions
- Add `GOOGLE_CREDENTIALS` secret with your service account JSON

5. Run locally:
```bash
streamlit run app.py
```

## Data Updates

- Data is automatically updated every 6 hours via GitHub Actions
- You can manually trigger an update from the Actions tab
- Updates are logged and can be monitored in the Actions tab

## Project Structure

- `app.py`: Main Streamlit application
- `scraper.py`: Job scraping logic
- `processor.py`: Job data processing and scoring
- `update_jobs.py`: Automated update script
- `.github/workflows/update_jobs.yml`: GitHub Actions workflow

## Contributing

Feel free to open issues or submit pull requests for improvements.

## Usage

1. Open the Streamlit dashboard in your browser
2. Use the sidebar filters to narrow down results
3. Click "Scrape New Jobs" to update the database
4. View and export results as needed

## Data Structure

The application stores the following information for each job:
- Company Name
- Job Title
- Location
- Intent Score
- Tech Keywords
- Job Description
- Source
- Posted Date
- LinkedIn Search URL

## Note

This application uses web scraping to gather data. Please be mindful of the websites' terms of service and rate limits. The application includes delays between requests to avoid overwhelming the servers. 