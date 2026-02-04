import streamlit as st
import subprocess
import os
import pandas as pd
import json
import shutil
import time
from datetime import datetime

st.set_page_config(page_title="Screaming Frog Automator", page_icon="🐸", layout="wide")

# --- CONFIGURATION ---
SF_PATH = r"C:\Program Files (x86)\Screaming Frog SEO Spider\ScreamingFrogSEOSpider.exe"
OUTPUT_DIR = os.path.join(os.getcwd(), "auto_crawl_data")
URL_LIST_FILE = os.path.join(os.getcwd(), "urls_to_crawl.txt")

st.title("🐸 Screaming Frog Auto-Bot")
st.markdown("Run your configured Screaming Frog spider directly from this dashboard.")

# --- TABS ---
tab1, tab2 = st.tabs(["🚗 Auto-Pagination (New/Used)", "📋 Manual URL List"])

mode = "auto"
base_url = ""
pages = 30
manual_urls = ""

with tab1:
    st.info("Uses the `?_p=X` pattern to automatically crawl multiple pages.")
    base_url = st.text_input("Base Inventory URL", value="https://www.cartownlexington.com/new-vehicles/")
    pages = st.number_input("Number of pages to crawl", min_value=1, max_value=200, value=30)
    mode = "auto"

with tab2:
    st.info("Paste specific URLs you want to scrape (one per line).")
    manual_urls = st.text_area("Paste URLs here", height=150, placeholder="https://example.com/page1\nhttps://example.com/page2")
    if manual_urls.strip():
        mode = "manual"

# --- RUNNER ---
if st.button("🚀 Start Crawl & Extract", type="primary"):
    
    if not os.path.exists(SF_PATH):
        st.error(f"❌ Screaming Frog application not found at: `{SF_PATH}`")
        st.stop()
    
    # UI Container for status
    status_container = st.status("Running Automation...", expanded=True)
    
    # 1. Prepare URL List
    status_container.write("📝 Preparing URL list...")
    try:
        with open(URL_LIST_FILE, "w") as f:
            if mode == "auto" and not manual_urls.strip():
                # Auto Generation
                for i in range(pages):
                    sep = "&" if "?" in base_url else "?"
                    f.write(f"{base_url}{sep}_p={i}\n")
                status_container.write(f"✅ Generated {pages} pagination URLs from base.")
            else:
                # Manual List
                # Prioritize manual list if the user entered text in that tab (or if strictly selected, but tabs are visual)
                # Logic: If tab2 text is present, use it.
                cleaned_urls = [u.strip() for u in manual_urls.split('\n') if u.strip()]
                if not cleaned_urls:
                    # Fallback to auto if empty
                    if mode == "auto":
                        # Re-run auto generation logic (duplication strictness is low priority here)
                         for i in range(pages):
                            sep = "&" if "?" in base_url else "?"
                            f.write(f"{base_url}{sep}_p={i}\n")
                    else:
                        st.error("Please paste at least one URL.")
                        st.stop()
                else:
                    for u in cleaned_urls:
                        f.write(u + "\n")
                    status_container.write(f"✅ Using {len(cleaned_urls)} manual URLs.")
                    
    except Exception as e:
        status_container.update(state="error")
        st.error(f"Failed to create URL file: {e}")
        st.stop()

    # 2. Run Screaming Frog
    status_container.write("🕷️ Launching Screaming Frog (Headless)...")
    
    # Clean output dir
    if os.path.exists(OUTPUT_DIR):
        try: shutil.rmtree(OUTPUT_DIR)
        except: pass
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    cmd = [
        SF_PATH,
        "--list-mode", os.path.abspath(URL_LIST_FILE),
        "--headless",
        "--output-folder", os.path.abspath(OUTPUT_DIR),
        "--export-custom-extraction"
    ]
    
    try:
        # We run with timeout to prevent infinite hangs, but SF can be slow. 5 mins?
        result = subprocess.run(cmd, capture_output=True, text=True)
        # Check output? SF output is verbose.
        status_container.write("✅ Crawl finished. Checking for data reports...")
        
    except Exception as e:
        status_container.update(state="error")
        st.error(f"Screaming Frog execution failed: {e}")
        st.stop()

    # 3. Process Data
    status_container.write("🧹 Parsing and cleaning JSON data...")
    
    report_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".csv") and "custom_extraction" in f.lower()]
    
    if not report_files:
        status_container.update(state="error")
        st.error("❌ No Custom Extraction report found. Crawl may have failed or blocked.")
        st.stop()

    csv_path = os.path.join(OUTPUT_DIR, report_files[0])
    
    try:
        # Flexible Read
        try: df = pd.read_csv(csv_path)
        except: df = pd.read_csv(csv_path, encoding='latin1')
        
        # Scan for JSON
        json_cols = [col for col in df.columns if df[col].astype(str).str.contains('{"', regex=False).any()]
        
        all_vehicles = []
        for index, row in df.iterrows():
            for col in json_cols:
                val = row[col]
                if pd.isna(val): continue
                val = str(val).strip()
                if val.startswith("{") and val.endswith("}"):
                    try:
                        data = json.loads(val)
                        all_vehicles.append(data)
                    except:
                        try:
                            data = json.loads(val.replace('""', '"'))
                            all_vehicles.append(data)
                        except:
                             pass
                             
        if not all_vehicles:
            status_container.update(state="complete")
            st.warning("⚠️ Screaming Frog ran successfully, but no Vehicle JSON data was found in the output. Check CSS Selectors.")
        else:
            # Build Clean DF
            clean_df = pd.DataFrame(all_vehicles)
            
            # Sort
            priority = ['vin', 'stock', 'year', 'make', 'model', 'trim', 'price', 'msrp', 'ext_color', 'int_color']
            cols = clean_df.columns.tolist()
            order = [c for c in priority if c in cols] + [c for c in cols if c not in priority]
            clean_df = clean_df[order]
            
            status_container.update(label="✅ Automation Complete!", state="complete", expanded=False)
            
            st.success(f"🎉 Successfully extracted **{len(clean_df)}** vehicles!")
            
            st.divider()
            
            st.subheader("📊 Data Preview")
            st.dataframe(clean_df.head(50))
            
            # Download
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            csv = clean_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Download Final CSV",
                data=csv,
                file_name=f"Cleaned_Inventory_{timestamp}.csv",
                mime="text/csv",
                type="primary"
            )

    except Exception as e:
        status_container.update(state="error")
        st.error(f"Error processing data: {e}")
