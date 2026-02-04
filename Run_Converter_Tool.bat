@echo off
cd /d "%~dp0"
echo Starting CSV Converter Tool...
python -m streamlit run converter_app.py
pause
