#!/bin/bash

# MMAS Django Project Deployment Script for AWS EC2
# Simple deployment without Docker or complex services

echo "Starting MMAS deployment..."

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip if not already installed
echo "Installing Python 3 and pip..."
sudo apt install -y python3 python3-pip python3-venv

# Install nginx
echo "Installing nginx..."
sudo apt install -y nginx

# Create application directory
echo "Setting up application directory..."
sudo mkdir -p /var/www/mmas
sudo chown -R $USER:$USER /var/www/mmas

# Copy project files (assuming you're running this from the project directory)
echo "Copying project files..."
cp -r . /var/www/mmas/

# Navigate to project directory
cd /var/www/mmas

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=MMAS.settings_production

# Run migrations
echo "Running database migrations..."
python manage.py migrate --settings=MMAS.settings_production

# Create superuser (optional - you can do this manually)
echo "Creating superuser (optional)..."
echo "You can create a superuser manually by running:"
echo "python manage.py createsuperuser --settings=MMAS.settings_production"

# Set up nginx configuration
echo "Setting up nginx configuration..."
sudo tee /etc/nginx/sites-available/mmas > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location /static/ {
        alias /var/www/mmas/staticfiles/;
    }

    location /media/ {
        alias /var/www/mmas/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/mmas /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# Create systemd service for Gunicorn
echo "Creating systemd service for Gunicorn..."
sudo tee /etc/systemd/system/mmas.service > /dev/null <<EOF
[Unit]
Description=MMAS Django Application
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=/var/www/mmas
Environment="PATH=/var/www/mmas/venv/bin"
ExecStart=/var/www/mmas/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 MMAS.wsgi_production:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start the service
sudo systemctl daemon-reload
sudo systemctl start mmas
sudo systemctl enable mmas

# Check service status
sudo systemctl status mmas

echo "Deployment completed!"
echo "Your application should now be running at http://your-server-ip"
echo ""
echo "Useful commands:"
echo "  Check service status: sudo systemctl status mmas"
echo "  Restart service: sudo systemctl restart mmas"
echo "  View logs: sudo journalctl -u mmas -f"
echo "  Check nginx status: sudo systemctl status nginx"
echo ""
echo "To create a superuser, run:"
echo "  cd /var/www/mmas && source venv/bin/activate"
echo "  python manage.py createsuperuser --settings=MMAS.settings_production"
