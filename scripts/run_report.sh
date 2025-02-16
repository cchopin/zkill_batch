#!/bin/bash
# This script executes the report generator for the previous month,
# then copies the generated report and index.html to the web directory.
# A log file (with a timestamp) is generated in /scripts/eve_killmails/log.
# Note: If you run into permission issues copying to /var/www/news.eve-goats.fr,
# configure sudoers to allow the current user to execute cp without a password.

# Set the log directory and create it if it doesn't exist
LOG_DIR="/scripts/eve_killmails/log"
mkdir -p "$LOG_DIR"

# Define the log file (appending output)
LOG_FILE="$LOG_DIR/run_report.log"
exec >> "$LOG_FILE" 2>&1
echo "-------------------------------------"
echo "Starting run_report.sh at $(date)"

# Activate the virtual environment
source /scripts/eve_env/bin/activate

# Set the absolute path to the Python report generator script (adjust as needed)
SCRIPT_PATH="/scripts/eve_killmails/killmail_report_generator.py"

# Calculate the year and month for the previous month (Linux syntax)
YEAR=$(date --date="1 month ago" +%Y)
MONTH=$(date --date="1 month ago" +%m)

# For macOS, use the following (uncomment and comment out the Linux lines):
# YEAR=$(date -v -1m +%Y)
# MONTH=$(date -v -1m +%m)

# Execute the Python report generator with the calculated parameters
python3 "$SCRIPT_PATH" --year "$YEAR" --month "$MONTH" --corporation "Goat to Go"

# Deactivate the virtual environment
deactivate

# Define the expected report file name (format: YYYYMM.html) and the web directory
REPORT_FILE="html/${YEAR}${MONTH}.html"
WEB_DIR="/var/www/news.eve-goats.fr/"

# Check that the report and index files exist and that the web directory exists
if [ -f "html/index.html" ] && [ -f "$REPORT_FILE" ]; then
    if [ -d "$WEB_DIR" ]; then
        echo "Attempting to copy index.html and report to $WEB_DIR"
        # Use sudo for copying files if necessary
        sudo cp html/index.html "$WEB_DIR" && echo "Index copied to $WEB_DIR" || echo "Error copying index.html"
        sudo cp "$REPORT_FILE" "$WEB_DIR" && echo "Report copied to $WEB_DIR" || echo "Error copying report file"
    else
        echo "Error: Web directory $WEB_DIR does not exist."
    fi
else
    echo "Error: Generated report or index.html not found."
fi

echo "Finished run_report.sh at $(date)"
