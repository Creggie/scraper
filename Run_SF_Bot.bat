@echo off
cd /d "%~dp0"
echo Starting Screaming Frog Automator...
python -m streamlit run sf_automator.py
pause
