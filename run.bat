@echo off
cd /d "%~dp0"
python -m tracker.main
start "" opportunities.xlsx
