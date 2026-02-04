@echo off
cd /d "%~dp0"
echo Starting Scraper App...
python -m streamlit run app.py
pause
