from seleniumbase import Driver
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import urllib.parse

def scrape_cartown(url="https://www.cartownlexington.com/new-vehicles/", scrape_all=False):
    print("Initializing Browser (Undetected Mode)...")
    driver = Driver(uc=True, headless=False)
    
    try:
        vehicles = []
        page_index = 0 # _p parameter starts at 0 for page 1 usually, or we iterate until empty
        
        while True:
            # Construct URL for specific page
            # If scrape_all is False, we just use the base URL (which is effectively page 0)
            target_url = url
            if scrape_all:
                if "?" in url:
                    target_url = f"{url}&_p={page_index}"
                else:
                    target_url = f"{url}?_p={page_index}"
            
            print(f"--- Scraping Page (Index {page_index}) ---")
            print(f"Navigating to {target_url}...")
            
            driver.get(target_url)
            
            # Smart Wait
            # Wait for either the inventory container OR a "No Results" message
            try:
                print("Waiting for data to load...")
                time.sleep(5) # Base wait for Cloudflare/Animation
                
                # Check 1: Did we land on a valid page with vehicles?
                soup = BeautifulSoup(driver.page_source, "html.parser")
                vehicle_wraps = soup.select(".result-wrap")
                
                if not vehicle_wraps:
                    # Check 2: Is there a "No Results" indicator?
                    # or did we just fail to load?
                    # If we are on page_index > 0 and find no vehicles, we assume we are done.
                    if page_index > 0 and scrape_all:
                        print("No vehicles found on this page. Reached end of inventory.")
                        break
                    else:
                        print("WARNING: No vehicles found on the first page. Site structure might have changed or Cloudflare blocked loading.")
                        break
                
                # Extract Data
                import json
                new_vehicles_count = 0
                for wrap in vehicle_wraps:
                    json_str = wrap.get("data-vehicle")
                    if json_str:
                        try:
                            data = json.loads(json_str)
                            # Helper for clean price
                            if 'price' in data:
                                data['price'] = str(data['price'])
                            vehicles.append(data)
                            new_vehicles_count += 1
                        except json.JSONDecodeError:
                            continue
                
                print(f"Found {new_vehicles_count} vehicles on this page. Total so far: {len(vehicles)}")
                
                # Verify if we actually got new data
                if new_vehicles_count == 0 and page_index > 0:
                    print("Page loaded but no valid vehicle data found. Stopping.")
                    break

            except Exception as e:
                print(f"Error extracting data on page {page_index}: {e}")
                break
            
            if not scrape_all:
                print("Scrape All is disabled. Stopping after first page.")
                break
                
            page_index += 1
            time.sleep(2) # Polite delay
                
        print(f"Scraping complete. Found {len(vehicles)} total vehicles.")
        
        if len(vehicles) > 0:
            df = pd.DataFrame(vehicles)
            # Reorder and rename columns
            column_mapping = {
                'year': 'Year',
                'make': 'Make',
                'model': 'Model',
                'trim': 'Trim',
                'vin': 'VIN',
                'stock': 'Stock #',
                'price': 'Final Price',
                'msrp': 'MSRP',
                'ext_color': 'Exterior Color',
                'int_color': 'Interior Color'
            }
            
            # Rename columns that exist
            df = df.rename(columns=column_mapping)
            
            # Select columns to output
            desired_order = ['Year', 'Make', 'Model', 'Trim', 'VIN', 'Stock #', 'MSRP', 'Final Price', 'Exterior Color', 'Interior Color']
            existing_cols = [c for c in desired_order if c in df.columns]
            extra_cols = [c for c in df.columns if c not in existing_cols]
            
            df = df[existing_cols + extra_cols]
            
            # Save local backup
            df.to_csv("inventory.csv", index=False)
            df.to_json("inventory.json", orient="records", indent=4)
            
            return df
        else:
            return None

    except Exception as e:
        print(f"Critical error: {e}")
        return None
    finally:
        print("Closing browser...")
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    scrape_cartown(scrape_all=False)
