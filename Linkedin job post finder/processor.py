import pandas as pd
import re

# Keywords that indicate active development
DEVELOPMENT_KEYWORDS = [
    'build', 'prototype', 'greenfield', 'develop', 'architect',
    'launch', 'design', 'create', 'innovate', 'research',
    'engineer', 'implement', 'construct', 'develop', 'pioneer'
]

# Technical keywords to extract
TECH_KEYWORDS = [
    'python', 'java', 'javascript', 'typescript', 'react', 'angular',
    'node', 'aws', 'azure', 'gcp', 'docker', 'kubernetes',
    'machine learning', 'ai', 'artificial intelligence', 'data science',
    'blockchain', 'iot', 'cloud', 'microservices', 'api'
]

def calculate_intent_score(description):
    score = 0
    found_keywords = []
    
    # Convert to lowercase for case-insensitive matching
    desc_lower = description.lower()
    
    # Check for development keywords
    for keyword in DEVELOPMENT_KEYWORDS:
        if keyword in desc_lower:
            score += 10
            found_keywords.append(keyword)
    
    # Check for technical keywords
    for keyword in TECH_KEYWORDS:
        if keyword in desc_lower:
            score += 5
            found_keywords.append(keyword)
    
    return score, list(set(found_keywords))

def process_jobs(jobs_df):
    if jobs_df.empty:
        return pd.DataFrame()
    
    processed_jobs = []
    
    for _, row in jobs_df.iterrows():
        description = row['description']
        score, keywords = calculate_intent_score(description)
        
        processed_job = {
            'Company': row['company'],
            'Role': row['title'],
            'Location': row['location'],
            'Intent Score': score,
            'Tech Keywords': ', '.join(keywords),
            'Description': description,
            'Source': row['source'],
            'Posted Date': row['posted_date'],
            'LinkedIn Search': f"https://www.linkedin.com/search/results/people/?keywords={row['title']}%20{row['company']}"
        }
        
        processed_jobs.append(processed_job)
    
    return pd.DataFrame(processed_jobs) 