import streamlit as st
import pandas as pd
import json
import io

st.set_page_config(page_title="JSON to CSV Converter", page_icon="🛠️", layout="wide")

st.title("🛠️ Screaming Frog JSON Converter")
st.markdown("""
Upload your **Screaming Frog CSV export** below.  
This tool will automatically extract the hidden JSON data (VIN, MSRP, etc.) and give you a clean Excel/CSV file.
""")

uploaded_file = st.file_uploader("Drop your CSV file here", type=["csv"])

if uploaded_file is not None:
    st.info("Processing file...")
    
    try:
        # Read the file
        # Try-catch for encoding issues which are common with Excel exports
        try:
            df = pd.read_csv(uploaded_file)
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='latin1')
            
        # Find JSON columns
        # We look for columns containing "{" and "vin" or just "{" and "}" structure
        json_cols = [col for col in df.columns if df[col].astype(str).str.contains('{"', regex=False).any()]
        
        if not json_cols:
            st.error("❌ No usage data found. Are you sure this is a Custom Extraction export with JSON data?")
            st.write("Columns found:", df.columns.tolist())
        else:
            success_count = 0
            all_vehicles = []
            
            # Progress bar
            progress_bar = st.progress(0)
            
            # Iterate and Extract
            # Using iterrows is slow for massive files but fine for typical inventory < 10k rows
            total_rows = len(df)
            
            for index, row in df.iterrows():
                # Update progress every 10%
                if index % max(1, int(total_rows / 10)) == 0:
                    progress_bar.progress(int((index / total_rows) * 100))
                    
                for col in json_cols:
                    cell_value = row[col]
                    if pd.isna(cell_value):
                        continue
                    
                    cell_value = str(cell_value).strip()
                    if cell_value.startswith("{") and cell_value.endswith("}"):
                        try:
                            # Parse JSON
                            data = json.loads(cell_value)
                            all_vehicles.append(data)
                            success_count += 1
                        except json.JSONDecodeError:
                            # Try simple fix for double-quotes escaped by CSV format
                            try:
                                fixed_val = cell_value.replace('""', '"')
                                data = json.loads(fixed_val)
                                all_vehicles.append(data)
                                success_count += 1
                            except:
                                pass
            
            progress_bar.progress(100)
            
            if not all_vehicles:
                st.warning("Found JSON columns but failed to extract valid objects. Check file format.")
            else:
                # Create DataFrame
                clean_df = pd.DataFrame(all_vehicles)
                
                # Column Ordering
                priority_cols = ['vin', 'stock', 'year', 'make', 'model', 'trim', 'price', 'msrp', 'ext_color', 'int_color']
                actual_cols = clean_df.columns.tolist()
                final_order = [c for c in priority_cols if c in actual_cols] + [c for c in actual_cols if c not in priority_cols]
                clean_df = clean_df[final_order]
                
                # Success UI
                st.success(f"✅ Successfully extracted **{len(clean_df)}** vehicles!")
                
                # Preview
                st.subheader("Preview")
                st.dataframe(clean_df.head(5))
                
                # Download Button
                csv_buffer = clean_df.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Download Cleaned CSV",
                    data=csv_buffer,
                    file_name="cleaned_inventory.csv",
                    mime="text/csv",
                    type="primary"
                )

    except Exception as e:
        st.error(f"Error processing file: {e}")
