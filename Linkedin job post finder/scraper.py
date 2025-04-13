import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import random

def scrape_google_jobs(query, location):
    base_url = "https://www.google.com/search"
    params = {
        "q": f"{query} jobs {location}",
        "ibp": "1,7"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        jobs = []
        job_cards = soup.find_all('div', class_='g')
        
        for card in job_cards:
            try:
                title = card.find('h3').text
                company = card.find('div', class_='s').text.split('·')[0].strip()
                location = card.find('div', class_='s').text.split('·')[1].strip()
                description = card.find('div', class_='st').text
                
                jobs.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'description': description,
                    'source': 'Google Jobs',
                    'posted_date': datetime.now().strftime('%Y-%m-%d')
                })
            except:
                continue
        
        return jobs
    except Exception as e:
        print(f"Error scraping Google Jobs: {str(e)}")
        return []

def scrape_indeed_jobs(query, location):
    base_url = "https://www.indeed.com/jobs"
    params = {
        "q": query,
        "l": location
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        jobs = []
        job_cards = soup.find_all('div', class_='job_seen_beacon')
        
        for card in job_cards:
            try:
                title = card.find('h2', class_='jobTitle').text.strip()
                company = card.find('span', class_='companyName').text.strip()
                location = card.find('div', class_='companyLocation').text.strip()
                description = card.find('div', class_='job-snippet').text.strip()
                
                jobs.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'description': description,
                    'source': 'Indeed',
                    'posted_date': datetime.now().strftime('%Y-%m-%d')
                })
            except:
                continue
        
        return jobs
    except Exception as e:
        print(f"Error scraping Indeed: {str(e)}")
        return []

def scrape_jobs():
    # Define search queries and locations
    queries = [
        "R&D engineer",
        "product development",
        "research and development",
        "new product development",
        "innovation engineer"
    ]
    
    locations = [
        "United States",
        "Europe",
        "Asia",
        "Remote"
    ]
    
    all_jobs = []
    
    for query in queries:
        for location in locations:
            # Scrape from Google Jobs
            google_jobs = scrape_google_jobs(query, location)
            all_jobs.extend(google_jobs)
            
            # Scrape from Indeed
            indeed_jobs = scrape_indeed_jobs(query, location)
            all_jobs.extend(indeed_jobs)
            
            # Add delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
    
    return pd.DataFrame(all_jobs) 