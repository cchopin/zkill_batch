#!/bin/bash
# Script pour régénérer uniquement l'index.html avec les liens Ishtar/MTU

# Set the log directory and create it if it doesn't exist
LOG_DIR="/scripts/eve_killmails/log"
mkdir -p "$LOG_DIR"

# Define the log file
LOG_FILE="$LOG_DIR/run_update_index.log"
exec >> "$LOG_FILE" 2>&1
echo "-------------------------------------"
echo "Starting run_update_index.sh at $(date)"

# Change to the script directory
cd /home/tely/scripts/eve_killmails

# Activate the virtual environment
source /scripts/eve_env/bin/activate

# Execute the Python index updater
echo "Updating index.html..."
python3 update_index.py

# Deactivate the virtual environment
deactivate

# Define the index file and the web directory
INDEX_FILE="html/index.html"
WEB_DIR="/var/www/news.eve-goats.fr/"

# Check that the index file exists and that the web directory exists
if [ -f "$INDEX_FILE" ]; then
    if [ -d "$WEB_DIR" ]; then
        echo "Copying updated index to $WEB_DIR"
        # Use sudo for copying files if necessary
        sudo cp "$INDEX_FILE" "$WEB_DIR" && echo "Index copied successfully" || echo "Error copying index"
    else
        echo "Error: Web directory $WEB_DIR does not exist."
    fi
else
    echo "Error: Generated index.html not found."
fi

echo "Finished run_update_index.sh at $(date)"