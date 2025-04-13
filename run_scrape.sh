#!/bin/bash

export PYTHONPATH=.

# Define the path to the Python script
SCRIPT_PATH="scrape.py"

# Run the Python script
/usr/bin/python3 "$SCRIPT_PATH"

# 0 0 * * * run_scraper.sh >> /path/to/logfile.log 2>&1
