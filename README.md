# Music Ministry Attendance System (MMAS)

A comprehensive Django-based web application designed to manage worship team schedules, event assignments, song lineups, and team coordination for music ministry organizations.

## 🎵 Overview

The Music Ministry Attendance System (MMAS) is a full-featured web application that streamlines the management of worship team activities. It provides tools for event scheduling, member assignments, song lineup creation, notifications, and even includes an AI-powered Bible chatbot for spiritual guidance.

## ✨ Key Features

### 🎯 Core Functionality
- **Event Management**: Create, edit, and manage worship events with detailed scheduling
- **Member Assignment**: Assign worship team members to specific roles for each event
- **Song Lineup Management**: Create and approve song lineups with different set list types
- **Role-Based Access**: Admin and member roles with appropriate permissions
- **Real-time Notifications**: In-app notifications and email alerts for assignments and approvals

### 🎼 Worship Team Roles
- **Worship Leader** (Primary & Backup)
- **Guitarist**
- **Keys Player**
- **Drummer**
- **Bassist**
- **Vocalist**
- **Technical Support**
- **Dancer**

### 📅 Event Management
- **Calendar View**: Visual calendar interface for event scheduling
- **Event Details**: Title, date, time, description, and admin notes
- **Team Assignment**: Assign multiple members to each role with backup options
- **Event Deletion**: Admin can remove events when needed

### 🎵 Song Lineup System
- **Set List Types**:
  - 1 Praise, 1 Worship, 1 Fellowship
  - 2 Praise, 1 Worship, 1 Fellowship
  - 2 Praise, 2 Worship, 1 Fellowship
  - Custom lineups
- **Song Categories**: Praise, High Praise, Worship, High Worship, Fellowship
- **Approval Workflow**: Lineups require admin approval before being finalized
- **Song Links**: Optional YouTube or other music links for each song

### 📧 Communication Features
- **Email Notifications**: Automatic emails for event assignments and lineup approvals
- **In-App Notifications**: Real-time notification system with read/unread status
- **Gmail Integration**: SMTP email service with HTML templates

### 🤖 AI Bible Assistant
- **OpenAI Integration**: AI-powered Bible chatbot for spiritual guidance
- **Conversational Event Creation**: Create events through natural language conversation
- **Daily Verse**: Automatically generated daily Bible verses
- **Bible Database**: Complete Bible text with search capabilities

### 📱 User Interface
- **Modern Design**: Clean, purple-themed interface with responsive design
- **Dashboard**: Centralized view of events, lineups, and notifications
- **Tabbed Interface**: Organized sections for Calendar, Events, and Lineups
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices

## 🛠️ Technology Stack

### Backend
- **Django 5.2.6**: Web framework
- **Python 3.12**: Programming language
- **SQLite**: Database (simple, no external dependencies)
- **Gunicorn**: WSGI server for production
- **WhiteNoise**: Static file serving

### Frontend
- **HTML5/CSS3**: Modern web standards
- **JavaScript**: Interactive features and AJAX
- **Bootstrap-inspired**: Custom CSS framework
- **SVG Icons**: Scalable vector graphics

### External Services
- **OpenAI API**: AI-powered Bible chatbot
- **Gmail SMTP**: Email notifications
- **AWS EC2**: Production deployment option

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Music-Ministry-Attendance-System
   ```

2. **Run the setup script**
   ```bash
   ./run_local.sh
   ```

3. **Access the application**
   - Open: http://127.0.0.1:8000
   - Admin: http://127.0.0.1:8000/admin
   - Default credentials: `admin` / `admin123`

### Manual Setup

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

## 📋 Prerequisites

- Python 3.8+
- pip
- Git

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Debug Mode
DEBUG=True

# Email Configuration (Optional)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# OpenAI API (Optional)
OPENAI_API_KEY=your-openai-api-key
```

### Email Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password for "JCSGO Worship Team"
3. Add credentials to `.env` file
4. See `EMAIL_SETUP.md` for detailed instructions

### OpenAI Integration

1. Get API key from OpenAI
2. Add to `.env` file
3. See `OPENAI_SETUP.md` for detailed instructions

## 📁 Project Structure

```
Music-Ministry-Attendance-System/
├── MMAS/                          # Django project settings
│   ├── settings.py                # Development settings
│   ├── settings_production.py     # Production settings
│   ├── urls.py                   # Main URL configuration
│   └── wsgi.py                   # WSGI configuration
├── music_ministry/               # Main Django app
│   ├── models.py                 # Database models
│   ├── views.py                  # View functions
│   ├── urls.py                   # App URL patterns
│   ├── forms.py                  # Django forms
│   ├── admin.py                  # Admin interface
│   ├── templates/                # HTML templates
│   ├── static/                   # CSS, JS, images
│   ├── migrations/               # Database migrations
│   ├── management/               # Custom commands
│   ├── bible_service.py          # Local Bible chatbot
│   ├── openai_bible_service.py   # OpenAI integration
│   ├── email_service.py          # Email functionality
│   └── notifications.py          # Notification system
├── staticfiles/                   # Collected static files
├── requirements.txt              # Python dependencies
├── run_local.sh                  # Local development script
├── deploy.sh                     # AWS deployment script
├── update.sh                     # Update script
├── env.example                   # Environment variables template
└── README.md                     # This file
```

## 🎯 User Roles

### Admin
- Create and manage events
- Assign team members to events
- Approve/reject song lineups
- Access all features
- Create events via AI chatbot

### Member
- View assigned events
- Create song lineups for assigned events
- Edit lineups (if assigned to event)
- View notifications
- Use Bible chatbot

## 📊 Database Models

### Core Models
- **User**: Authentication and role management
- **Member**: Team member profiles with roles
- **Event**: Worship events with scheduling
- **EventAssignment**: Links members to events
- **Lineup**: Song lineups for events
- **Song**: Individual songs in lineups
- **Notification**: In-app notifications
- **BibleBook/BibleVerse**: Complete Bible text
- **DailyVerse**: Daily verse generation
- **ChatMessage**: AI chatbot conversations

## 🌐 API Endpoints

### Event Management
- `GET /api/events/` - Calendar events data
- `POST /api/create-event-from-chat/` - Create event via AI

### Notifications
- `GET /api/notifications/` - User notifications
- `POST /api/notifications/{id}/read/` - Mark as read
- `DELETE /api/notifications/{id}/delete/` - Delete notification

### Bible Features
- `POST /api/bible-chat/` - AI Bible chatbot
- `GET /api/daily-verse/` - Today's Bible verse

## 🚀 Deployment

### AWS EC2 Deployment

1. **Upload project to EC2**
   ```bash
   scp -r MMAS ubuntu@your-ec2-ip:/home/ubuntu/
   ```

2. **SSH and deploy**
   ```bash
   ssh ubuntu@your-ec2-ip
   cd MMAS
   ./deploy.sh
   ```

3. **Create superuser**
   ```bash
   python manage.py createsuperuser --settings=MMAS.settings_production
   ```

4. **Access application**
   - URL: http://your-ec2-ip
   - Admin: http://your-ec2-ip/admin

### Production Features
- **nginx**: Reverse proxy and static file serving
- **Gunicorn**: WSGI server for Django
- **Systemd**: Auto-start service
- **Logging**: Application and error logs
- **Security**: Production security settings

## 🔒 Security Features

- **CSRF Protection**: Cross-site request forgery protection
- **XSS Protection**: Cross-site scripting prevention
- **Session Security**: Secure session management
- **Password Validation**: Strong password requirements
- **Environment Variables**: Secure credential management
- **Production Settings**: Debug disabled, security headers

## 📧 Email Features

### Event Assignment Emails
- Sent to assigned members when added to events
- Includes event details and team information
- Beautiful HTML templates with purple theme

### Lineup Approval Emails
- Sent to technical/dancer members when lineups approved
- Includes complete song list and event details
- Green-themed HTML templates

## 🤖 AI Bible Assistant

### Features
- **Conversational Interface**: Natural language Bible discussions
- **Event Creation**: Create events through conversation
- **Daily Verses**: Automatically generated daily Bible verses
- **Bible Search**: Search through complete Bible text
- **Spiritual Guidance**: AI-powered spiritual conversations

### Usage
1. Navigate to Bible Chatbot page
2. Start conversation with AI
3. Ask Bible questions or request event creation
4. View conversation history

## 📱 Mobile Support

- **Responsive Design**: Works on all device sizes
- **Touch-Friendly**: Optimized for mobile interactions
- **Progressive Web App**: Can be installed on mobile devices
- **Offline Capable**: Basic functionality works offline

## 🔄 Updates and Maintenance

### Update Application
```bash
./update.sh
```

### Backup Database
```bash
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3
```

### View Logs
```bash
# Application logs
tail -f /var/log/mmas/app.log

# Error logs
tail -f /var/log/mmas/error.log
```

## 🐛 Troubleshooting

### Common Issues

1. **Email not sending**
   - Check Gmail App Password
   - Verify 2FA is enabled
   - Check `.env` file configuration

2. **OpenAI API errors**
   - Verify API key is correct
   - Check API usage limits
   - Ensure internet connectivity

3. **Static files not loading**
   - Run `python manage.py collectstatic`
   - Check WhiteNoise configuration
   - Verify file permissions

4. **Database errors**
   - Run `python manage.py migrate`
   - Check database file permissions
   - Verify SQLite installation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Django Community**: For the excellent web framework
- **OpenAI**: For AI capabilities
- **JCSGO Worship Team**: For inspiration and requirements
- **Contributors**: All those who helped build this system

## 📞 Support

For support, questions, or feature requests:
- Create an issue in the repository
- Contact the development team
- Check the documentation files

---

**Built with ❤️ for worship teams everywhere**
