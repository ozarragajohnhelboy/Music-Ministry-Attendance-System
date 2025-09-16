# AWS EC2 Deployment - Step by Step Guide

## Step 1: Create AWS EC2 Instance

### 1.1 Login to AWS Console

1. Go to [AWS Console](https://aws.amazon.com/console/)
2. Sign in with your AWS account
3. Navigate to **EC2** service

### 1.2 Launch Instance

1. Click **"Launch Instance"**
2. **Name**: `MMAS-Django-App`
3. **Application and OS Images**:
   - Choose **Ubuntu Server 22.04 LTS** (Free tier eligible)
4. **Instance type**:
   - Select **t2.micro** (Free tier eligible)
5. **Key pair**:
   - Click **"Create new key pair"**
   - Name: `mmas-keypair`
   - Key pair type: **RSA**
   - Private key file format: **.pem**
   - Click **"Create key pair"**
   - **IMPORTANT**: Download the .pem file and save it securely

### 1.3 Network Settings

1. **Security group**: Create new security group
2. **Allow SSH traffic from**: My IP
3. **Allow HTTP traffic from**: Anywhere (0.0.0.0/0)
4. **Allow HTTPS traffic from**: Anywhere (0.0.0.0/0) - Optional
5. Click **"Launch instance"**

### 1.4 Wait for Instance

- Wait for instance status to show **"Running"**
- Note down the **Public IPv4 address** (e.g., 3.15.123.45)

## Step 2: Connect to Your EC2 Instance

### 2.1 Set Permissions for Key File

```bash
# Navigate to where you saved the .pem file
cd ~/Downloads  # or wherever you saved it

# Set proper permissions
chmod 400 mmas-keypair.pem
```

### 2.2 SSH into Instance

```bash
# Replace with your actual public IP and key file path
ssh -i mmas-keypair.pem ubuntu@YOUR_PUBLIC_IP

# Example:
# ssh -i mmas-keypair.pem ubuntu@3.15.123.45
```

## Step 3: Upload Your Project to EC2

### 3.1 From Your Local Machine (New Terminal)

```bash
# Navigate to your project directory
cd /Users/jomari/Desktop/MMAS

# Upload the entire project to EC2
scp -i ~/Downloads/mmas-keypair.pem -r . ubuntu@YOUR_PUBLIC_IP:/home/ubuntu/MMAS

# Example:
# scp -i ~/Downloads/mmas-keypair.pem -r . ubuntu@3.15.123.45:/home/ubuntu/MMAS
```

### 3.2 Verify Upload (Back in EC2 SSH)

```bash
# Check if files were uploaded
ls -la /home/ubuntu/MMAS

# You should see your Django project files
```

## Step 4: Deploy the Application

### 4.1 Run Deployment Script

```bash
# Navigate to project directory
cd /home/ubuntu/MMAS

# Make deployment script executable
chmod +x deploy.sh

# Run deployment script
./deploy.sh
```

**The deployment script will:**

- Update system packages
- Install Python 3, pip, nginx
- Set up virtual environment
- Install Python dependencies
- Configure nginx as reverse proxy
- Set up Gunicorn as WSGI server
- Create systemd service
- Run database migrations
- Collect static files

### 4.2 Wait for Deployment

- The script will take 5-10 minutes to complete
- You'll see various installation and configuration messages
- Wait for "Deployment completed!" message

## Step 5: Create Superuser

### 5.1 Create Admin User

```bash
# Navigate to application directory
cd /var/www/mmas

# Activate virtual environment
source venv/bin/activate

# Create superuser
python manage.py createsuperuser --settings=MMAS.settings_production

# Follow prompts:
# Username: admin
# Email: admin@example.com
# Password: (create a strong password)
# Password (again): (confirm password)
```

## Step 6: Test Your Deployment

### 6.1 Check Service Status

```bash
# Check if application is running
sudo systemctl status mmas

# Check if nginx is running
sudo systemctl status nginx
```

### 6.2 Access Your Application

1. Open web browser
2. Go to: `http://YOUR_PUBLIC_IP`
3. You should see your MMAS application
4. Admin panel: `http://YOUR_PUBLIC_IP/admin`

## Step 7: Useful Commands for Management

### 7.1 Service Management

```bash
# Restart application
sudo systemctl restart mmas

# Stop application
sudo systemctl stop mmas

# Start application
sudo systemctl start mmas

# Check application logs
sudo journalctl -u mmas -f
```

### 7.2 Update Application

```bash
# When you make changes to your code
cd /var/www/mmas
./update.sh
```

### 7.3 View Logs

```bash
# Application logs
sudo journalctl -u mmas -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Step 8: Optional - Set Up Domain Name

### 8.1 If You Have a Domain

1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Create an A record pointing to your EC2 public IP
3. Update nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/mmas
```

4. Change `server_name _;` to `server_name yourdomain.com www.yourdomain.com;`
5. Restart nginx:

```bash
sudo systemctl restart nginx
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Cannot SSH to Instance

```bash
# Check security group allows SSH from your IP
# Verify key file permissions
chmod 400 mmas-keypair.pem
```

#### 2. Application Not Loading

```bash
# Check service status
sudo systemctl status mmas

# Check nginx status
sudo systemctl status nginx

# Restart services
sudo systemctl restart mmas nginx
```

#### 3. Permission Errors

```bash
# Fix ownership
sudo chown -R ubuntu:ubuntu /var/www/mmas
```

#### 4. Static Files Not Loading

```bash
# Collect static files again
cd /var/www/mmas
source venv/bin/activate
python manage.py collectstatic --noinput --settings=MMAS.settings_production
```

## Cost Estimation

### Free Tier (First 12 months)

- **t2.micro instance**: Free (750 hours/month)
- **Storage**: 30 GB free
- **Data transfer**: 1 GB free

### After Free Tier

- **t2.micro**: ~$8-10/month
- **Storage**: ~$3/month for 30GB
- **Data transfer**: $0.09/GB

## Security Recommendations

1. **Change default SSH port** (optional)
2. **Set up firewall rules**
3. **Regular security updates**
4. **Backup your database regularly**
5. **Use environment variables for sensitive data**

## Summary

Your MMAS Django application is now deployed on AWS EC2!

**Access URLs:**

- Main app: `http://YOUR_PUBLIC_IP`
- Admin panel: `http://YOUR_PUBLIC_IP/admin`

**Key files location on server:**

- Application: `/var/www/mmas`
- Logs: `sudo journalctl -u mmas -f`
- Nginx config: `/etc/nginx/sites-available/mmas`
