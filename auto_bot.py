import subprocess
import os
import pandas as pd
import json
import time
import shutil
from datetime import datetime

# --- CONFIGURATION ---
SF_PATH = r"C:\Program Files (x86)\Screaming Frog SEO Spider\ScreamingFrogSEOSpider.exe"
BASE_URL = "https://www.cartownlexington.com/new-vehicles/"
MAX_PAGES = 25  # How many pagination pages to generate
OUTPUT_DIR = os.path.join(os.getcwd(), "auto_crawl_data")
URL_LIST_FILE = os.path.join(os.getcwd(), "urls_to_crawl.txt")

def generate_url_list():
    print(f"Generating URL list for {MAX_PAGES} pages...")
    with open(URL_LIST_FILE, "w") as f:
        # Base URL (Page 1)
        # f.write(BASE_URL + "\n") # Sometimes duplicate of p=0, skipping base
        
        # Pagination URLs
        for i in range(MAX_PAGES):
            if "?" in BASE_URL:
                url = f"{BASE_URL}&_p={i}"
            else:
                url = f"{BASE_URL}?_p={i}" 
            f.write(url + "\n")
    print(f"Saved URL list to {URL_LIST_FILE}")

def run_screaming_frog():
    if not os.path.exists(SF_PATH):
        print(f"ERROR: Screaming Frog not found at {SF_PATH}")
        return False

    # Clean previous output
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

    print("\n--- Starting Screaming Frog Crawl (Headless) ---")
    print("This may take a minute or two. Please wait...")

    # Command: Run list mode, headless, export custom extraction to folder
    cmd = [
        SF_PATH,
        "--list-mode", URL_LIST_FILE, 
        "--headless",
        "--output-folder", OUTPUT_DIR,
        "--export-custom-extraction" 
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Crawl complete!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running Screaming Frog: {e}")
        return False

def clean_data():
    print("\n--- Processing Data ---")
    # Find the exported CSV in the output directory
    exported_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".csv") and "custom_extraction" in f.lower()]
    
    if not exported_files:
        print("No extraction report found. Did the crawl finish successfully?")
        return

    csv_path = os.path.join(OUTPUT_DIR, exported_files[0])
    print(f"Found report: {exported_files[0]}")
    
    try:
        # Read properly handling potential encoding issues
        try:
            df = pd.read_csv(csv_path)
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding='latin1')

        # Identify JSON columns
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
                        # Try double quote fix
                        try:
                            data = json.loads(val.replace('""', '"'))
                            all_vehicles.append(data)
                        except:
                            pass

        if not all_vehicles:
            print("No vehicles extracted.")
            return

        # Create Clean DF
        clean_df = pd.DataFrame(all_vehicles)
        
        # Sort Columns
        priority = ['vin', 'stock', 'year', 'make', 'model', 'trim', 'price', 'msrp', 'ext_color', 'int_color']
        cols = clean_df.columns.tolist()
        order = [c for c in priority if c in cols] + [c for c in cols if c not in priority]
        clean_df = clean_df[order]
        
        # Save Final w/ Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        final_filename = f"Inventory_Final_{timestamp}.csv"
        
        clean_df.to_csv(final_filename, index=False)
        print(f"\nSUCCESS! ✅")
        print(f"Extracted {len(clean_df)} vehicles.")
        print(f"Saved to: {os.path.abspath(final_filename)}")
        
        # Attempt to open the file automatically
        os.startfile(final_filename)

    except Exception as e:
        print(f"Error processing data: {e}")

if __name__ == "__main__":
    generate_url_list()
    success = run_screaming_frog()
    if success:
        clean_data()
    
    print("\nDone.")
