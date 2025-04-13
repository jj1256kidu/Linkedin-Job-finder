import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from dotenv import load_dotenv
from job_scraper import JobScraper
from industry_keywords import INDUSTRY_KEYWORDS

# Load environment variables
load_dotenv()

# Initialize Google Sheets connection
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'new-job-product-developeme-e8fedbafff68.json', scope)
gc = gspread.authorize(credentials)
spreadsheet = gc.open_by_key('1ICiOa5oTYJmO9MN3KCx3rbuu6XutTHgGeiafhiW2YB4')
worksheet = spreadsheet.sheet1

def main():
    st.title("🚀 R&D Job Finder Dashboard")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Get unique locations and companies
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    if not df.empty:
        locations = ['All'] + sorted(df['Location'].unique().tolist())
        companies = ['All'] + sorted(df['Company'].unique().tolist())
        industries = ['All'] + sorted(df['Industry'].unique().tolist())
        
        selected_location = st.sidebar.selectbox("Location", locations)
        selected_company = st.sidebar.selectbox("Company", companies)
        selected_industry = st.sidebar.selectbox("Industry", industries)
        min_score = st.sidebar.slider("Minimum Intent Score", 0, 10, 0)
        
        # Apply filters
        filtered_df = df.copy()
        if selected_location != 'All':
            filtered_df = filtered_df[filtered_df['Location'] == selected_location]
        if selected_company != 'All':
            filtered_df = filtered_df[filtered_df['Company'] == selected_company]
        if selected_industry != 'All':
            filtered_df = filtered_df[filtered_df['Industry'] == selected_industry]
        filtered_df = filtered_df[filtered_df['Intent Score'] >= min_score]
        
        # Display data
        st.write(f"Found {len(filtered_df)} matching jobs")
        
        # Create a new DataFrame with clickable LinkedIn links
        display_df = filtered_df.copy()
        display_df['LinkedIn Search'] = display_df.apply(
            lambda row: f'[Search on LinkedIn]({row["LinkedIn Search"]})', axis=1)
        
        # Display the table
        st.dataframe(
            display_df[['Company', 'Title', 'Location', 'Industry', 'Intent Score', 'Industry Score', 'Tech Keywords', 'LinkedIn Search']],
            column_config={
                "LinkedIn Search": st.column_config.LinkColumn("LinkedIn Search")
            }
        )
        
        # Export to CSV
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="rd_jobs.csv",
            mime="text/csv"
        )
        
        # Manual refresh button
        if st.sidebar.button("Refresh Data"):
            scraper = JobScraper()
            queries = ["R&D", "product development", "innovation"]
            locations = ["United States", "Europe", "Asia"]
            industries = list(INDUSTRY_KEYWORDS.keys())
            new_entries = scraper.run_scraper(queries, locations, industries)
            st.sidebar.success(f"Added {new_entries} new job listings!")
    else:
        st.warning("No data available. Please run the scraper first.")

if __name__ == "__main__":
    main() 
