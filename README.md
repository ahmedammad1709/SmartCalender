# SmartCal - Smart Calendar Booking System

A modern calendar booking system with AI-powered scheduling capabilities.

## Features

- User registration and authentication
- Secure login with JWT tokens
- SQLite database for user management
- Responsive dashboard
- Modern UI design

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project files**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Access the application:**
   - Open your web browser
   - Go to `http://localhost:5000`
   - The main page will load with navigation to login and register

## Usage

### Registration
1. Click "Get Started" or "Start Free Trial" from the main page
2. Fill in your details (name, email, username, password)
3. Click "Create Account"
4. You'll be redirected to the login page

### Login
1. Enter your email and password
2. Click "Login"
3. Upon successful login, you'll be redirected to the dashboard

### Dashboard
- View your user information
- Access calendar management features (coming soon)
- Logout functionality

## File Structure

```
Smartcal-FrontEnd/
├── app.py                 # Flask backend server
├── requirements.txt       # Python dependencies
├── smartcal.db          # SQLite database (created automatically)
├── index.html           # Main landing page
├── login.html           # Login page
├── register.html        # Registration page
├── dashboard.html       # User dashboard
├── style.css           # Main stylesheet
└── Assets/             # Images and assets
    ├── logo.png
    ├── clock.png
    └── team.png
```

## API Endpoints

- `POST /users/register` - User registration
- `POST /users/login` - User login
- `GET /users/me` - Get current user info (requires authentication)
- `GET /agendas/` - Get user agendas (requires authentication)

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- SQL injection protection
- CORS enabled for cross-origin requests

## Development

The application uses:
- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Flask (Python)
- **Database**: SQLite
- **Authentication**: JWT tokens with bcrypt password hashing

## Next Steps

Future features to implement:
- Calendar management
- Availability settings
- Booking page creation
- Team collaboration
- Meeting scheduling
- Email notifications 