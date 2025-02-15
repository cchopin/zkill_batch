#!/bin/bash

# Configuration variables
MAC_USER=""          # Mac username
MAC_HOST=""          # Mac hostname or IP
RETENTION_DAYS=10    # Number of days to keep backups (in addition to first of month)

# Get current date
DATE=$(date +%Y%m%d)

# Create local temporary backup
mkdir -p /tmp/backup_temp

# Backup DB with postgres user and direct gzip compression
sudo -u postgres pg_dump eve_killmails | gzip > /tmp/backup_temp/eve_killmails_$DATE.sql.gz

# Backup scripts
tar -czf /tmp/backup_temp/scripts_$DATE.tar.gz /scripts/eve_killmails

# Send to Mac
if ping -c 1 $MAC_HOST &> /dev/null; then
    scp -r /tmp/backup_temp/* $MAC_USER@$MAC_HOST:~/raspberry_backups/
    echo "Backup successfully sent to Mac Studio"

    # Cleanup old backups on Mac
    ssh $MAC_USER@$MAC_HOST "
        # Keep first day of each month
        cd ~/raspberry_backups && \
        find . -name '*_[0-9][0-9][0-9][0-9]01_*' -type f -print0 | xargs -0 touch && \

        # Delete files older than RETENTION_DAYS days, except those we just touched (first of month)
        find ~/raspberry_backups -type f -mtime +$RETENTION_DAYS -delete

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

# Cleanup
rm -rf /tmp/backup_temp