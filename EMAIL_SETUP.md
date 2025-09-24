# Email Setup Guide

## 📧 Gmail Configuration

### Step 1: Enable 2-Factor Authentication

1. Go to your Google Account settings
2. Navigate to Security
3. Enable 2-Step Verification

### Step 2: Generate App Password

1. Go to Google Account settings
2. Navigate to Security → 2-Step Verification
3. Scroll down to "App passwords"
4. Select "Mail" and "Other (custom name)"
5. Enter "JCSGO Worship Team" as the name
6. Copy the generated 16-character password

### Step 3: Update .env File

Edit the `.env` file in your project root:

```env
# Email Settings
EMAIL_HOST_USER=your-actual-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=your-actual-email@gmail.com
```

### Step 4: Test Email Configuration

1. Login as admin
2. Click "Test Email" button on dashboard
3. Check your email inbox

## 🔒 Security Notes

- ✅ `.env` file is in `.gitignore` - credentials won't be committed
- ✅ Use App Password, not your regular Gmail password
- ✅ App Password is 16 characters without spaces
- ✅ Keep your credentials secure

## 📱 Email Features

### Event Assignment Emails

- Sent to **regular members** (Worship Leader, Guitarist, Keys, Drummer, Bassist, Vocalist) when admin assigns to event
- Includes event details, date, time, team members
- Beautiful HTML template with purple theme

### Lineup Approval Emails

- Sent to **technical and dancer members ONLY** when lineup is approved
- Sent to ALL technical and dancer members (regardless of event assignment)
- Includes event details and complete song list
- Beautiful HTML template with green theme

## 🚀 Deployment

For AWS deployment, set environment variables:

```bash
export EMAIL_HOST_USER=your-email@gmail.com
export EMAIL_HOST_PASSWORD=your-app-password
export DEFAULT_FROM_EMAIL=your-email@gmail.com
```

## 🐛 Troubleshooting

### Common Issues:

1. **Authentication failed** - Check App Password is correct
2. **SMTP error** - Verify 2FA is enabled
3. **No emails sent** - Check .env file is in project root
4. **Permission denied** - Ensure App Password has Mail permission

### Test Commands:

```bash
# Test environment variables
python manage.py shell -c "import os; print(os.getenv('EMAIL_HOST_USER'))"

# Test email sending
python manage.py shell -c "from music_ministry.email_service import send_test_email; send_test_email()"
```
