import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv
from industry_keywords import INDUSTRY_KEYWORDS

# Load environment variables
load_dotenv()

class JobScraper:
    def __init__(self):
        self.development_keywords = [
            'build', 'prototype', 'greenfield', 'develop', 'architect',
            'launch', 'design', 'create', 'engineer', 'innovate',
            'research', 'R&D', 'new product', 'product development'
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Initialize Google Sheets connection with specific credentials file
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'new-job-product-developeme-e8fedbafff68.json', scope)
        self.gc = gspread.authorize(credentials)
        
        # Open the specific sheet by ID
        try:
            self.spreadsheet = self.gc.open_by_key('1ICiOa5oTYJmO9MN3KCx3rbuu6XutTHgGeiafhiW2YB4')
            self.worksheet = self.spreadsheet.sheet1
            
            # Set up headers if the sheet is empty
            if not self.worksheet.get_all_records():
                headers = [
                    "Company", "Title", "Description", "Location", 
                    "Posted Date", "Intent Score", "Industry Score",
                    "Tech Keywords", "Industry", "LinkedIn Search"
                ]
                self.worksheet.append_row(headers)
        except Exception as e:
            print(f"Error accessing Google Sheet: {str(e)}")
            raise

    def scrape_google_jobs(self, query, location, industry=None):
        """Scrape job listings from Google Jobs with industry-specific keywords"""
        base_url = "https://www.google.com/search"
        
        # Add industry-specific keywords if industry is specified
        if industry and industry in INDUSTRY_KEYWORDS:
            industry_keywords = INDUSTRY_KEYWORDS[industry]
            query = f"{query} {' OR '.join(industry_keywords)}"
        
        params = {
            'q': f'{query} jobs {location}',
            'ibp': '1,1'
        }
        
        try:
            response = requests.get(base_url, params=params, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            jobs = []
            job_cards = soup.find_all('div', class_='g')
            
            for card in job_cards:
                job = {}
                job['company'] = card.find('div', class_='vNEEBe').text if card.find('div', class_='vNEEBe') else 'Unknown'
                job['title'] = card.find('h3').text if card.find('h3') else 'Unknown'
                job['description'] = card.find('div', class_='YgLbBe').text if card.find('div', class_='YgLbBe') else ''
                job['location'] = location
                job['posted_date'] = datetime.now().strftime('%Y-%m-%d')
                job['industry'] = industry if industry else 'General'
                
                # Calculate intent score
                job['intent_score'] = self.calculate_intent_score(job['description'])
                job['tech_keywords'] = self.extract_tech_keywords(job['description'])
                
                # Add industry-specific scoring
                if industry and industry in INDUSTRY_KEYWORDS:
                    job['industry_score'] = self.calculate_industry_score(job['description'], industry)
                else:
                    job['industry_score'] = 0
                
                jobs.append(job)
            
            return jobs
        except Exception as e:
            print(f"Error scraping Google Jobs: {str(e)}")
            return []

    def calculate_intent_score(self, description):
        """Calculate development intent score based on keywords"""
        score = 0
        description = description.lower()
        
        for keyword in self.development_keywords:
            if keyword.lower() in description:
                score += 1
        
        return score

    def calculate_industry_score(self, description, industry):
        """Calculate industry-specific score based on keywords"""
        score = 0
        description = description.lower()
        
        if industry in INDUSTRY_KEYWORDS:
            for keyword in INDUSTRY_KEYWORDS[industry]:
                if keyword.lower() in description.lower():
                    score += 1
        
        return score

    def extract_tech_keywords(self, description):
        """Extract technical keywords from job description"""
        tech_keywords = []
        common_tech = ['python', 'java', 'javascript', 'react', 'node', 'aws', 
                      'docker', 'kubernetes', 'machine learning', 'ai', 'cloud']
        
        for tech in common_tech:
            if tech.lower() in description.lower():
                tech_keywords.append(tech)
        
        return ', '.join(tech_keywords)

    def update_google_sheet(self, jobs):
        """Update Google Sheet with new job listings"""
        try:
            # Get existing data
            existing_data = self.worksheet.get_all_records()
            existing_companies = set(row['Company'] for row in existing_data)
            
            # Prepare new data
            new_rows = []
            for job in jobs:
                if job['company'] not in existing_companies:
                    new_rows.append([
                        job['company'],
                        job['title'],
                        job['description'],
                        job['location'],
                        job['posted_date'],
                        job['intent_score'],
                        job['industry_score'],
                        job['tech_keywords'],
                        job['industry'],
                        f"https://www.linkedin.com/search/results/people/?keywords=CTO%20{job['company']}"
                    ])
            
            # Append new rows if any
            if new_rows:
                self.worksheet.append_rows(new_rows)
            
            return len(new_rows)
        except Exception as e:
            print(f"Error updating Google Sheet: {str(e)}")
            return 0

    def run_scraper(self, queries, locations, industries=None):
        """Run the scraper for multiple queries, locations, and industries"""
        all_jobs = []
        
        for query in queries:
            for location in locations:
                if industries:
                    for industry in industries:
                        jobs = self.scrape_google_jobs(query, location, industry)
                        all_jobs.extend(jobs)
                else:
                    jobs = self.scrape_google_jobs(query, location)
                    all_jobs.extend(jobs)
        
        # Update Google Sheet
        new_entries = self.update_google_sheet(all_jobs)
        return new_entries 