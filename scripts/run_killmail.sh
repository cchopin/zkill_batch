#!/bin/bash

# Set working directory
cd /scripts/eve_killmails

# Activate virtual environment
source /scripts/eve_env/bin/activate

# Execute script with full Python path
python /scripts/eve_killmails/eve_killmails.py

# Deactivate virtual environment
deactivate