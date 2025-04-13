import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from scraper import scrape_jobs
from processor import process_jobs
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Sheets setup
def setup_google_sheets():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'credentials.json', scope)
    gc = gspread.authorize(credentials)
    return gc

def push_to_sheets(df, sheet_name='Data', spreadsheet_name='Product developement'):
    try:
        gc = setup_google_sheets()
        spreadsheet = gc.open(spreadsheet_name)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Clear existing data
        worksheet.clear()
        
        # Update with new data
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Error pushing to Google Sheets: {str(e)}")
        return False

def get_from_sheets(sheet_name='Data', spreadsheet_name='Product developement'):
    try:
        gc = setup_google_sheets()
        spreadsheet = gc.open(spreadsheet_name)
        worksheet = spreadsheet.worksheet(sheet_name)
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error getting data from Google Sheets: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("R&D Job Finder")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    industry = st.sidebar.text_input("Industry")
    location = st.sidebar.text_input("Location")
    min_score = st.sidebar.slider("Minimum Intent Score", 0, 100, 50)
    
    # Action buttons
    if st.sidebar.button("Scrape New Jobs"):
        with st.spinner("Scraping jobs..."):
            jobs = scrape_jobs()
            processed_jobs = process_jobs(jobs)
            if push_to_sheets(processed_jobs):
                st.success("Successfully updated Google Sheets!")
    
    # Display data
    df = get_from_sheets()
    if not df.empty:
        # Apply filters
        if industry:
            df = df[df['Industry'].str.contains(industry, case=False)]
        if location:
            df = df[df['Location'].str.contains(location, case=False)]
        df = df[df['Intent Score'] >= min_score]
        
        # Display data
        st.dataframe(df)
        
        # Export button
        if st.button("Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="job_listings.csv",
                mime="text/csv"
            )
    else:
        st.info("No data available. Click 'Scrape New Jobs' to start.")

if __name__ == "__main__":
    main() 