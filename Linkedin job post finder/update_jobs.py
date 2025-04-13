from scraper import scrape_jobs
from processor import process_jobs
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_google_sheets():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'credentials.json', scope)
    gc = gspread.authorize(credentials)
    return gc

def update_sheet(df, sheet_name='Data', spreadsheet_name='Product developement'):
    try:
        gc = setup_google_sheets()
        spreadsheet = gc.open(spreadsheet_name)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Clear existing data
        worksheet.clear()
        
        # Update with new data
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        logger.info("Successfully updated Google Sheet")
        return True
    except Exception as e:
        logger.error(f"Error updating Google Sheet: {str(e)}")
        return False

def main():
    try:
        logger.info("Starting job scraping process...")
        
        # Scrape jobs
        jobs = scrape_jobs()
        logger.info(f"Scraped {len(jobs)} jobs")
        
        # Process jobs
        processed_jobs = process_jobs(jobs)
        logger.info("Processed job data")
        
        # Update Google Sheet
        success = update_sheet(processed_jobs)
        
        if success:
            logger.info("Job update completed successfully")
        else:
            logger.error("Failed to update Google Sheet")
            
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        raise

if __name__ == "__main__":
    main() 