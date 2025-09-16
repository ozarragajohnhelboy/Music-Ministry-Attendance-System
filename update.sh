#!/bin/bash

# MMAS Django Project Update Script
# Use this script to update your deployed application

echo "Updating MMAS application..."

# Navigate to application directory
cd /var/www/mmas

# Activate virtual environment
source venv/bin/activate

# Pull latest changes (if using git)
# git pull origin main

# Install/update dependencies
echo "Updating dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate --settings=MMAS.settings_production

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=MMAS.settings_production

# Restart the application
echo "Restarting application..."
sudo systemctl restart mmas

# Check status
echo "Checking application status..."
sudo systemctl status mmas --no-pager

echo "Update completed!"
echo "Your application should be running at http://your-server-ip"
