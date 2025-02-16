#!/bin/bash
# This script creates backups of the database and scripts,
# then transfers them to your Mac, and cleans up old backups.
# Log file for backups.sh
LOG_FILE="/scripts/eve_killmails/log/backups.log"
exec >> "$LOG_FILE" 2>&1
echo "-------------------------------------"
echo "Starting backups.sh at $(date)"

# Configuration variables
MAC_USER=""          # Mac username
MAC_HOST=""          # Mac hostname or IP address
RETENTION_DAYS=10    # Number of days to retain backups (besides the first day of each month)

# Get the current date in YYYYMMDD format
DATE=$(date +%Y%m%d)

# Create a local temporary backup directory
mkdir -p /tmp/backup_temp

# Backup the database using the postgres user with gzip compression
sudo -u postgres pg_dump eve_killmails | gzip > /tmp/backup_temp/eve_killmails_$DATE.sql.gz

# Backup the scripts directory
tar -czf /tmp/backup_temp/scripts_$DATE.tar.gz /scripts/eve_killmails

# Send backups to the Mac if reachable
if ping -c 1 $MAC_HOST &> /dev/null; then
    scp -r /tmp/backup_temp/* $MAC_USER@$MAC_HOST:~/raspberry_backups/
    echo "Backup successfully sent to Mac Studio"

    # Cleanup old backups on the Mac
    ssh $MAC_USER@$MAC_HOST "
        # Mark files from the first day of each month
        cd ~/raspberry_backups && \
        find . -name '*_[0-9][0-9][0-9][0-9]01_*' -type f -print0 | xargs -0 touch && \

        # Delete files older than RETENTION_DAYS days, except those just touched (first day of month)
        find ~/raspberry_backups -type f -mtime +$RETENTION_DAYS -delete && \

        # Reset the timestamps of first-of-month files to their original dates
        cd ~/raspberry_backups && \
        for f in *_[0-9][0-9][0-9][0-9]01_*; do
            if [ -f \"$f\" ]; then
                touch -t \$(echo $f | grep -o '[0-9]\\{8\\}') \"$f\"
            fi
        done
    "
else
    echo "Mac not accessible, backup failed"
fi

# Remove the temporary backup directory
rm -rf /tmp/backup_temp

echo "Finished backups.sh at $(date)"
