# Car Town Scraper App

A powerful, local web app to scrape vehicle inventory from **cartownlexington.com** (and potentially others) using automated browser control to bypass protections.

## Prerequisites

1.  **Google Chrome**: Must be installed.
2.  **Python**: Must be installed (3.8+).

## Setup (First Time Only)

1.  Open **PowerShell** or **Command Prompt** in this folder.
2.  Install dependencies:
    ```powershell
    pip install -r requirements.txt
    ```

## How to Run

1.  Start the user interface:
    ```powershell
    streamlit run app.py
    ```
2.  A new tab will open in your default browser showing the **Car Town Scraper** interface.
3.  Enter the URL (pre-filled with the default) and click **Start Scraping**.
4.  Watch the magic! A separate Chrome window will perform the work, and the results will appear in your main browser window.

## Features
-   **Visual Feedback**: See progress and live results.
-   **CSV Download**: One-click download of the scraped data.
-   **Metrics**: Instant summary of vehicle counts and pricing.
