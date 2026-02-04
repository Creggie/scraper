import pandas as pd
import json
import tkinter as tk
from tkinter import filedialog
import os

def clean_and_convert():
    print("Please select the CSV file extracted from Screaming Frog...")
    
    # Hide the main tkinter window
    root = tk.Tk()
    root.withdraw()

    # Open file selector
    file_path = filedialog.askopenfilename(
        title="Select Screaming Frog Export CSV",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )

    if not file_path:
        print("No file selected. Exiting.")
        return

    print(f"Processing: {file_path}")
    
    try:
        # Load the CSV
        # We assume the file might have extra header rows or strange encoding depending on Excel export settings
        try:
            df = pd.read_csv(file_path)
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='latin1')

        # Find columns that look like they contain the JSON data
        # Screaming Frog usually names them "Vehicle Data 1", "Vehicle Data 2", etc.
        # or sometimes just one column if you did a different extraction.
        # We will look for any column that contains "{" and "vin" as a heuristic
        
        json_cols = [col for col in df.columns if df[col].astype(str).str.contains('{"', regex=False).any()]
        
        if not json_cols:
            print("Could not automatically find columns containing JSON data.")
            print("Columns found:", df.columns.tolist())
            return
            
        print(f"Found {len(json_cols)} columns potentially containing vehicle JSON.")
        
        all_vehicles = []
        
        for index, row in df.iterrows():
            for col in json_cols:
                cell_value = row[col]
                if pd.isna(cell_value):
                    continue
                
                # Clean up string if necessary (Screaming Frog sometimes leaves whitespace)
                cell_value = str(cell_value).strip()
                
                if cell_value.startswith("{") and cell_value.endswith("}"):
                    try:
                        data = json.loads(cell_value)
                        all_vehicles.append(data)
                    except json.JSONDecodeError:
                        # Sometimes quotes are escaped weirdly in CSVs
                        try:
                            # Attempt very basic fix for CSV double-quote escaping
                            fixed_val = cell_value.replace('""', '"')
                            data = json.loads(fixed_val)
                            all_vehicles.append(data)
                        except:
                            pass
                            
        if not all_vehicles:
            print("No valid JSON objects were extracted. Please check the CSV format.")
            return
            
        # Create new DataFrame from the dictionary list
        clean_df = pd.DataFrame(all_vehicles)
        
        # Organize columns nicely
        # Prioritize key fields
        priority_cols = ['vin', 'stock', 'year', 'make', 'model', 'trim', 'price', 'msrp', 'ext_color', 'int_color']
        
        # Get all actual columns present
        actual_cols = clean_df.columns.tolist()
        
        # Create final column order: Priority ones first (if they exist), then the rest
        final_order = [c for c in priority_cols if c in actual_cols] + [c for c in actual_cols if c not in priority_cols]
        
        clean_df = clean_df[final_order]
        
        # Save output
        output_path = os.path.splitext(file_path)[0] + "_cleaned.csv"
        clean_df.to_csv(output_path, index=False)
        
        print(f"✅ Success! Extracted {len(clean_df)} vehicles.")
        print(f"💾 Saved clean file to: {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    try:
        clean_and_convert()
        input("\nPress Enter to close...")
    except KeyboardInterrupt:
        pass
