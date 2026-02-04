import streamlit as st
import pandas as pd
import time
from scrape_inventory import scrape_cartown

st.set_page_config(page_title="Car Town Scraper", page_icon="🚗", layout="wide")

st.title("🚗 Scraper")
st.markdown("Enter the inventory URL below to start scraping.")

# Input URL
url = st.text_input("Target URL", value="https://www.cartownlexington.com/new-vehicles/")
scrape_all = st.checkbox("Scrape All Pages (Might take a while)", value=False)

if st.button("Start Scraping", type="primary"):
    with st.spinner('Scraping in progress... this opens a browser visually to bypass security...'):
        try:
            # Run the scraper
            df = scrape_cartown(url=url, scrape_all=scrape_all)
            
            if df is not None and not df.empty:
                st.success(f"✅ Successfully scraped {len(df)} vehicles!")
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Vehicles", len(df))
                
                # Check for price columns for metrics
                if 'Final Price' in df.columns:
                    try:
                        # Clean price for calculation (remove $, etc)
                        avg_price = df['Final Price'].replace(r'[\$,]', '', regex=True).astype(float).mean()
                        col2.metric("Average Price", f"${avg_price:,.0f}")
                    except:
                        col2.metric("Average Price", "N/A")
                
                col3.metric("Models Found", df['Model'].nunique() if 'Model' in df.columns else "N/A")

                # Display Data
                st.dataframe(df, use_container_width=True)
                
                # Convert to CSV for download
                csv = df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name='inventory.csv',
                    mime='text/csv',
                )
            else:
                st.error("❌ No vehicles found. Check the browser window for issues.")
                
        except Exception as e:
            st.error(f"An error occurred: {e}")
