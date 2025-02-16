#!/bin/bash
# This script runs the eve_killmails Python script.
# Log file for run_killmail.sh
LOG_FILE="/scripts/eve_killmails/log/run_killmail.log"
exec >> "$LOG_FILE" 2>&1
echo "-------------------------------------"
echo "Starting run_killmail.sh at $(date)"

# Change to the working directory
cd /scripts/eve_killmails

# Activate the virtual environment
source /scripts/eve_env/bin/activate

# Execute the Python script using the full path
python /scripts/eve_killmails/eve_killmails.py

# Deactivate the virtual environment
deactivate

echo "Finished run_killmail.sh at $(date)"
