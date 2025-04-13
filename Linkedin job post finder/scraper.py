import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
import json
from typing import List, Dict, Optional
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self, credentials_path: str = "credentials.json"):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.geolocator = Nominatim(user_agent="job_scraper")
        self.driver = None
        self.credentials_path = credentials_path
        self.setup_google_sheets()
        
    def setup_google_sheets(self):
        """Initialize Google Sheets connection"""
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_path, scope)
            self.gc = gspread.authorize(credentials)
            logger.info("Successfully connected to Google Sheets")
        except Exception as e:
            logger.error(f"Error setting up Google Sheets: {e}")
            raise

    def push_to_sheets(self, df: pd.DataFrame, spreadsheet_name: str = "Product development", worksheet_name: str = "Data"):
        """Push job data to Google Sheets"""
        try:
            logger.info(f"Attempting to open spreadsheet: {spreadsheet_name}")
            # Open the spreadsheet
            spreadsheet = self.gc.open(spreadsheet_name)
            logger.info(f"Successfully opened spreadsheet: {spreadsheet_name}")
            
            # Select the worksheet
            try:
                worksheet = spreadsheet.worksheet(worksheet_name)
                logger.info(f"Found existing worksheet: {worksheet_name}")
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(worksheet_name, rows=1000, cols=20)
                logger.info(f"Created new worksheet: {worksheet_name}")
            
            # Clear existing data
            worksheet.clear()
            logger.info("Cleared existing data from worksheet")
            
            # Add headers
            headers = df.columns.tolist()
            worksheet.append_row(headers)
            logger.info(f"Added headers: {headers}")
            
            # Add data
            set_with_dataframe(worksheet, df, include_index=False, include_column_header=False, resize=True)
            logger.info(f"Successfully pushed {len(df)} jobs to Google Sheets")
            
            # Verify data was written
            cell_count = worksheet.row_count
            logger.info(f"Current worksheet row count: {cell_count}")
            
        except Exception as e:
            logger.error(f"Error pushing to Google Sheets: {e}")
            raise

    def setup_selenium(self):
        """Initialize Selenium WebDriver"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        
    def get_location_details(self, location_str: str) -> Dict:
        """Get detailed location information using geopy"""
        try:
            location = self.geolocator.geocode(location_str, timeout=10)
            if location:
                return {
                    'city': location_str,
                    'country': location.address.split(',')[-1].strip(),
                    'latitude': location.latitude,
                    'longitude': location.longitude
                }
        except GeocoderTimedOut:
            logger.warning(f"Geocoding timeout for location: {location_str}")
        return {
            'city': location_str,
            'country': 'Unknown',
            'latitude': None,
            'longitude': None
        }

    def scrape_linkedin(self, keywords: List[str], location: str = "global") -> List[Dict]:
        """Scrape LinkedIn jobs with global coverage"""
        jobs = []
        try:
            if not self.driver:
                self.setup_selenium()
                
            for keyword in keywords:
                # Construct LinkedIn search URL
                search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location={location}"
                self.driver.get(search_url)
                
                # Wait for job listings to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "jobs-search__results-list"))
                )
                
                # Scroll to load more jobs
                for _ in range(3):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                
                # Extract job listings
                job_elements = self.driver.find_elements(By.CLASS_NAME, "job-search-card")
                
                for job_element in job_elements:
                    try:
                        job_data = {
                            'source': 'LinkedIn',
                            'title': job_element.find_element(By.CLASS_NAME, "job-search-card__title").text,
                            'company': job_element.find_element(By.CLASS_NAME, "job-search-card__subtitle").text,
                            'location': job_element.find_element(By.CLASS_NAME, "job-search-card__location").text,
                            'posted_date': job_element.find_element(By.CLASS_NAME, "job-search-card__listdate").text,
                            'job_url': job_element.find_element(By.CLASS_NAME, "job-search-card__link").get_attribute('href'),
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        # Get detailed location information
                        location_details = self.get_location_details(job_data['location'])
                        job_data.update(location_details)
                        
                        jobs.append(job_data)
                    except Exception as e:
                        logger.error(f"Error parsing job element: {e}")
                        
                time.sleep(random.uniform(2, 4))  # Random delay between searches
                
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                
        return jobs

    def scrape_indeed(self, keywords: List[str], location: str = "global") -> List[Dict]:
        """Scrape Indeed jobs with global coverage"""
        jobs = []
        try:
            for keyword in keywords:
                # Construct Indeed search URL
                search_url = f"https://www.indeed.com/jobs?q={keyword}&l={location}"
                response = requests.get(search_url, headers=self.headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                job_elements = soup.find_all('div', class_='job_seen_beacon')
                
                for job_element in job_elements:
                    try:
                        job_data = {
                            'source': 'Indeed',
                            'title': job_element.find('h2', class_='jobTitle').text.strip(),
                            'company': job_element.find('span', class_='companyName').text.strip(),
                            'location': job_element.find('div', class_='companyLocation').text.strip(),
                            'posted_date': job_element.find('span', class_='date').text.strip(),
                            'job_url': "https://www.indeed.com" + job_element.find('a')['href'],
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        # Get detailed location information
                        location_details = self.get_location_details(job_data['location'])
                        job_data.update(location_details)
                        
                        jobs.append(job_data)
                    except Exception as e:
                        logger.error(f"Error parsing job element: {e}")
                        
                time.sleep(random.uniform(2, 4))  # Random delay between searches
                
        except Exception as e:
            logger.error(f"Error scraping Indeed: {e}")
            
        return jobs

    def scrape_glassdoor(self, keywords: List[str], location: str = "global") -> List[Dict]:
        """Scrape Glassdoor jobs with global coverage"""
        jobs = []
        try:
            for keyword in keywords:
                # Construct Glassdoor search URL
                search_url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={keyword}&locT=C&locId=1"
                response = requests.get(search_url, headers=self.headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                job_elements = soup.find_all('li', class_='react-job-listing')
                
                for job_element in job_elements:
                    try:
                        job_data = {
                            'source': 'Glassdoor',
                            'title': job_element.find('a', class_='jobLink').text.strip(),
                            'company': job_element.find('div', class_='employerName').text.strip(),
                            'location': job_element.find('div', class_='location').text.strip(),
                            'posted_date': job_element.find('div', class_='job-age').text.strip(),
                            'job_url': "https://www.glassdoor.com" + job_element.find('a', class_='jobLink')['href'],
                            'scraped_at': datetime.now().isoformat()
                        }
                        
                        # Get detailed location information
                        location_details = self.get_location_details(job_data['location'])
                        job_data.update(location_details)
                        
                        jobs.append(job_data)
                    except Exception as e:
                        logger.error(f"Error parsing job element: {e}")
                        
                time.sleep(random.uniform(2, 4))  # Random delay between searches
                
        except Exception as e:
            logger.error(f"Error scraping Glassdoor: {e}")
            
        return jobs

    def scrape_all_sources(self, keywords: List[str], location: str = "global") -> pd.DataFrame:
        """Scrape jobs from all sources and return as DataFrame"""
        all_jobs = []
        
        # Scrape from LinkedIn
        linkedin_jobs = self.scrape_linkedin(keywords, location)
        all_jobs.extend(linkedin_jobs)
        
        # Scrape from Indeed
        indeed_jobs = self.scrape_indeed(keywords, location)
        all_jobs.extend(indeed_jobs)
        
        # Scrape from Glassdoor
        glassdoor_jobs = self.scrape_glassdoor(keywords, location)
        all_jobs.extend(glassdoor_jobs)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_jobs)
        
        # Add timestamp for when the data was scraped
        df['scraped_at'] = datetime.now().isoformat()
        
        return df

    def save_to_csv(self, df: pd.DataFrame, filename: str = "jobs_data.csv"):
        """Save job data to CSV file"""
        df.to_csv(filename, index=False)
        logger.info(f"Saved {len(df)} jobs to {filename}")

    def save_to_json(self, df: pd.DataFrame, filename: str = "jobs_data.json"):
        """Save job data to JSON file"""
        df.to_json(filename, orient='records', lines=True)
        logger.info(f"Saved {len(df)} jobs to {filename}")

    def scrape_and_update_sheets(self, keywords: List[str], location: str = "global", 
                               spreadsheet_name: str = "Product development", 
                               worksheet_name: str = "Data"):
        """Scrape jobs and update Google Sheets in one operation"""
        try:
            # Scrape jobs
            jobs_df = self.scrape_all_sources(keywords, location)
            
            if not jobs_df.empty:
                # Push to Google Sheets
                self.push_to_sheets(jobs_df, spreadsheet_name, worksheet_name)
                
                # Print summary
                print(f"\nScraped {len(jobs_df)} jobs from multiple sources")
                print("\nJob distribution by source:")
                print(jobs_df['source'].value_counts())
                print("\nJob distribution by country:")
                print(jobs_df['country'].value_counts())
            else:
                logger.warning("No jobs found to update in Google Sheets")
                
        except Exception as e:
            logger.error(f"Error in scrape_and_update_sheets: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Job Scraper')
    parser.add_argument('--keywords', nargs='+', help='List of keywords to search for')
    parser.add_argument('--location', default='global', help='Location to search in')
    args = parser.parse_args()

    logger.info("Starting job scraper")
    logger.info(f"Keywords: {args.keywords}")
    logger.info(f"Location: {args.location}")

    scraper = JobScraper()
    
    try:
        # Scrape jobs
        jobs_df = scraper.scrape_all_sources(args.keywords, args.location)
        
        if not jobs_df.empty:
            logger.info(f"Scraped {len(jobs_df)} jobs")
            # Push to Google Sheets
            scraper.push_to_sheets(jobs_df)
            
            # Print summary
            print(f"\nScraped {len(jobs_df)} jobs from multiple sources")
            print("\nJob distribution by source:")
            print(jobs_df['source'].value_counts())
            print("\nJob distribution by country:")
            print(jobs_df['country'].value_counts())
        else:
            logger.warning("No jobs found to update in Google Sheets")
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 
