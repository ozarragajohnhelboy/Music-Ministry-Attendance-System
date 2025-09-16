# MMAS Django Project - Deployment Guide

This guide explains how to deploy the MMAS (Music Ministry Assignment System) Django project to AWS EC2 and run it locally.

## Project Structure

- **Local Development**: Uses `MMAS/settings.py` with SQLite database
- **Production**: Uses `MMAS/settings_production.py` with optimized settings for AWS EC2

## Local Development

### Quick Start

```bash
# Run the local development script
./run_local.sh
```

This script will:

- Create a virtual environment
- Install dependencies
- Run migrations
- Create a superuser (admin/admin123)
- Start the development server at http://127.0.0.1:8000

### Manual Local Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## AWS EC2 Deployment

### Prerequisites

- AWS EC2 instance (Ubuntu 20.04 or 22.04 recommended)
- Security group allowing HTTP (port 80) and SSH (port 22) access
- Domain name (optional, can use public IP)

### Deployment Steps

1. **Upload your project to EC2**

   ```bash
   # From your local machine, upload the project
   scp -r /path/to/MMAS ubuntu@your-ec2-ip:/home/ubuntu/
   ```

2. **SSH into your EC2 instance**

   ```bash
   ssh ubuntu@your-ec2-ip
   ```

3. **Run the deployment script**
   ```bash
   cd MMAS
   ./deploy.sh
   ```

The deployment script will:

- Update system packages
- Install Python 3, pip, and nginx
- Set up the application directory
- Create virtual environment and install dependencies
- Configure nginx as reverse proxy
- Set up Gunicorn as WSGI server
- Create systemd service for automatic startup
- Collect static files and run migrations

### Post-Deployment

1. **Create a superuser**

   ```bash
   cd /var/www/mmas
   source venv/bin/activate
   python manage.py createsuperuser --settings=MMAS.settings_production
   ```

2. **Access your application**
   - Visit `http://your-ec2-public-ip` in your browser
   - Admin panel: `http://your-ec2-public-ip/admin`

### Useful Commands

```bash
# Check application status
sudo systemctl status mmas

# Restart application
sudo systemctl restart mmas

# View application logs
sudo journalctl -u mmas -f

# Check nginx status
sudo systemctl status nginx

# Restart nginx
sudo systemctl restart nginx
```

## Configuration Files

### Production Settings (`MMAS/settings_production.py`)

- DEBUG = False
- Uses WhiteNoise for static file serving
- Configured for production security
- Logging setup
- SQLite database (simple deployment)

### WSGI Configuration

- `MMAS/wsgi.py` - Local development
- `MMAS/wsgi_production.py` - Production deployment

## Security Notes

- The production settings include basic security configurations
- For production use, consider:
  - Setting up HTTPS with SSL certificates
  - Using environment variables for SECRET_KEY
  - Implementing proper database backups
  - Setting up monitoring and logging

## Troubleshooting

### Common Issues

1. **Permission errors**

   ```bash
   sudo chown -R $USER:$USER /var/www/mmas
   ```

2. **Port already in use**

   ```bash
   sudo lsof -i :8000
   sudo kill -9 <PID>
   ```

3. **Static files not loading**

   ```bash
   cd /var/www/mmas
   source venv/bin/activate
   python manage.py collectstatic --noinput --settings=MMAS.settings_production
   ```

4. **Database issues**
   ```bash
   cd /var/www/mmas
   source venv/bin/activate
   python manage.py migrate --settings=MMAS.settings_production
   ```

## Environment Variables (Optional)

For enhanced security, you can set environment variables:

```bash
# Set in /etc/environment or .env file
export SECRET_KEY="your-secret-key-here"
export DEBUG=False
```

Then update `settings_production.py` to use:

```python
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-key')
```

## Scaling (Future Considerations)

When your application grows, consider:

- Using PostgreSQL instead of SQLite
- Implementing Redis for caching
- Using AWS RDS for database
- Setting up load balancers
- Implementing auto-scaling groups
