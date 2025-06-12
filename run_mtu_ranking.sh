#!/bin/bash
# Script pour exécuter le générateur de classement MTU sur le Raspberry Pi

# Set the log directory and create it if it doesn't exist
LOG_DIR="/scripts/eve_killmails/log"
mkdir -p "$LOG_DIR"

# Define the log file
LOG_FILE="$LOG_DIR/run_mtu_ranking.log"
exec >> "$LOG_FILE" 2>&1
echo "-------------------------------------"
echo "Starting run_mtu_ranking.sh at $(date)"

# Change to the script directory
cd /scripts/eve_killmails

# Activate the virtual environment
source /scripts/eve_env/bin/activate

# Execute the Python MTU ranking generator
echo "Generating MTU ranking report..."
python3 mtu_ranking_generator.py --output html/mtu_ranking.html

# Deactivate the virtual environment
deactivate

# Define the report file name and the web directory
REPORT_FILE="html/mtu_ranking.html"
WEB_DIR="/var/www/news.eve-goats.fr/"

# Check that the report file exists and that the web directory exists
if [ -f "$REPORT_FILE" ]; then
    if [ -d "$WEB_DIR" ]; then
        echo "Copying MTU ranking report to $WEB_DIR"
        # Use sudo for copying files if necessary
        sudo cp "$REPORT_FILE" "$WEB_DIR" && echo "MTU ranking report copied successfully" || echo "Error copying MTU ranking report"
    else
        echo "Error: Web directory $WEB_DIR does not exist."
    fi
else
    echo "Error: Generated MTU ranking report not found."
fi

echo "Finished run_mtu_ranking.sh at $(date)"