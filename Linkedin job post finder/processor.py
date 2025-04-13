import pandas as pd
import re
from keywords import get_all_keywords, get_keywords_by_category

# Get all keywords
ALL_KEYWORDS = get_all_keywords()

def calculate_intent_score(description, title):
    score = 0
    found_keywords = []
    
    # Convert to lowercase for case-insensitive matching
    desc_lower = description.lower()
    title_lower = title.lower()
    
    # Check for keywords in both title and description
    for keyword in ALL_KEYWORDS:
        keyword_lower = keyword.lower()
        if keyword_lower in desc_lower or keyword_lower in title_lower:
            # Higher score for matches in title
            if keyword_lower in title_lower:
                score += 15
            else:
                score += 10
            found_keywords.append(keyword)
    
    # Check for technical skills
    technical_skills = get_keywords_by_category('technical_skills')
    for skill in technical_skills:
        if skill.lower() in desc_lower:
            score += 5
            found_keywords.append(skill)
    
    return score, list(set(found_keywords))

def process_jobs(jobs_df):
    if jobs_df.empty:
        return pd.DataFrame()
    
    processed_jobs = []
    
    for _, row in jobs_df.iterrows():
        description = row['description']
        title = row['title']
        score, keywords = calculate_intent_score(description, title)
        
        # Determine domain based on keywords
        domain = "General"
        domain_keywords = get_keywords_by_category('domains')
        for domain_name, domain_terms in domain_keywords.items():
            if any(term.lower() in description.lower() for term in domain_terms):
                domain = domain_name
                break
        
        processed_job = {
            'Company': row['company'],
            'Role': row['title'],
            'Location': row['location'],
            'Domain': domain,
            'Intent Score': score,
            'Tech Keywords': ', '.join(keywords),
            'Description': description,
            'Source': row['source'],
            'Posted Date': row['posted_date'],
            'LinkedIn Search': f"https://www.linkedin.com/search/results/people/?keywords={row['title']}%20{row['company']}"
        }
        
        processed_jobs.append(processed_job)
    
    return pd.DataFrame(processed_jobs) 