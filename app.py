from flask import Flask, request, jsonify, send_from_directory, render_template, session, redirect, url_for
from flask_cors import CORS
from flask_mail import Mail, Message
import sqlite3
import bcrypt
import jwt
import datetime
import os
import json
import random
import string
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ttorfidoo001@gmail.com'
app.config['MAIL_PASSWORD'] = 'eole tcbx joek wouf'
app.config['MAIL_DEFAULT_SENDER'] = 'ttorfidoo001@gmail.com'

mail = Mail(app)
CORS(app)

# In-memory storage for verification codes (in production, use Redis or database)
verification_codes = {}

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code):
    """Send verification email using Flask-Mail"""
    try:
        msg = Message(
            subject='SmartCal - Email Verification',
            recipients=[email],
            body=f'''
Hello!

Thank you for signing up for SmartCal. Please use the following verification code to complete your registration:

{code}

This code will expire in 5 minutes.

If you didn't create an account with SmartCal, please ignore this email.

Best regards,
The SmartCal Team
            ''',
            html=f'''
<html>
<body>
    <h2>SmartCal - Email Verification</h2>
    <p>Hello!</p>
    <p>Thank you for signing up for SmartCal. Please use the following verification code to complete your registration:</p>
    <h3 style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; font-size: 24px; letter-spacing: 5px;">{code}</h3>
    <p><strong>This code will expire in 5 minutes.</strong></p>
    <p>If you didn't create an account with SmartCal, please ignore this email.</p>
    <br>
    <p>Best regards,<br>The SmartCal Team</p>
</body>
</html>
            '''
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_booking_confirmation_visitor(visitor_email, visitor_name, agenda_title, host_name, booking_date, time_slot, duration, alias_name):
    """Send booking confirmation email to visitor"""
    try:
        # Format date and time
        from datetime import datetime
        date_obj = datetime.strptime(booking_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Format time
        time_obj = datetime.strptime(time_slot, '%H:%M')
        formatted_time = time_obj.strftime('%I:%M %p')
        
        msg = Message(
            subject=f'✅ Meeting Confirmed: {agenda_title}',
            recipients=[visitor_email],
            body=f'''
Hello {visitor_name}!

Your meeting has been successfully booked with {host_name}.

Meeting Details:
- Agenda: {agenda_title}
- Date: {formatted_date}
- Time: {formatted_time}
- Duration: {duration} minutes
- Host: {host_name}

Please make sure to join the meeting on time. If you need to reschedule or cancel, please contact {host_name} directly.

Best regards,
The SmartCal Team
            ''',
            html=f'''
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #28a745; margin-bottom: 10px;">✅ Meeting Confirmed!</h1>
            <p style="font-size: 18px; color: #666;">Your meeting has been successfully booked</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
            <h2 style="color: #333; margin-bottom: 20px;">Meeting Details</h2>
            <div style="margin-bottom: 15px;">
                <strong style="color: #555;">Agenda:</strong> {agenda_title}
            </div>
            <div style="margin-bottom: 15px;">
                <strong style="color: #555;">Date:</strong> {formatted_date}
            </div>
            <div style="margin-bottom: 15px;">
                <strong style="color: #555;">Time:</strong> {formatted_time}
            </div>
            <div style="margin-bottom: 15px;">
                <strong style="color: #555;">Duration:</strong> {duration} minutes
            </div>
            <div style="margin-bottom: 15px;">
                <strong style="color: #555;">Host:</strong> {host_name}
            </div>
        </div>
        
        <div style="background: #e7f3ff; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff;">
            <p style="margin: 0; color: #0056b3;">
                <strong>Important:</strong> Please make sure to join the meeting on time. 
                If you need to reschedule or cancel, please contact {host_name} directly.
            </p>
        </div>
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
            <p style="color: #666; margin: 0;">
                Best regards,<br>
                <strong>The SmartCal Team</strong>
            </p>
        </div>
    </div>
</body>
</html>
            '''
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending visitor confirmation email: {e}")
        return False

def send_booking_notification_host(host_email, host_name, visitor_name, visitor_email, agenda_title, booking_date, time_slot, duration):
    """Send booking notification email to host"""
    try:
        # Format date and time
        from datetime import datetime
        date_obj = datetime.strptime(booking_date, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%A, %B %d, %Y')
        
        # Format time
        time_obj = datetime.strptime(time_slot, '%H:%M')
        formatted_time = time_obj.strftime('%I:%M %p')
        
        msg = Message(
            subject=f'📅 New Meeting Booking: {agenda_title}',
            recipients=[host_email],
            body=f'''
Hello {host_name}!

You have a new meeting booking for your agenda "{agenda_title}".

Booking Details:
- Visitor: {visitor_name} ({visitor_email})
- Date: {formatted_date}
- Time: {formatted_time}
- Duration: {duration} minutes
- Agenda: {agenda_title}

Please make sure to be available for this meeting. You can contact the visitor at {visitor_email} if needed.

Best regards,
The SmartCal Team
            ''',
            html=f'''
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #007bff; margin-bottom: 10px;">📅 New Meeting Booking</h1>
            <p style="font-size: 18px; color: #666;">Someone has booked a meeting with you</p>
        </div>
        
        <div style="background: #f8f9fa; padding: 25px; border-radius: 10px; margin-bottom: 25px;">
            <h2 style="color: #333; margin-bottom: 20px;">Booking Details</h2>
            <div style="margin-bottom: 15px;">
                <strong style="color: #555;">Visitor:</strong> {visitor_name}
            </div>
            <div style="margin-bottom: 15px;">
                <strong style="color: #555;">Email:</strong> {visitor_email}
            </div>
            <div style="margin-bottom: 15px;">
                <strong style="color: #555;">Date:</strong> {formatted_date}
            </div>
            <div style="margin-bottom: 15px;">
                <strong style="color: #555;">Time:</strong> {formatted_time}
            </div>
            <div style="margin-bottom: 15px;">
                <strong style="color: #555;">Duration:</strong> {duration} minutes
            </div>
            <div style="margin-bottom: 15px;">
                <strong style="color: #555;">Agenda:</strong> {agenda_title}
            </div>
        </div>
        
        <div style="background: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107;">
            <p style="margin: 0; color: #856404;">
                <strong>Reminder:</strong> Please make sure to be available for this meeting. 
                You can contact the visitor at <a href="mailto:{visitor_email}" style="color: #007bff;">{visitor_email}</a> if needed.
            </p>
        </div>
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
            <p style="color: #666; margin: 0;">
                Best regards,<br>
                <strong>The SmartCal Team</strong>
            </p>
        </div>
    </div>
</body>
</html>
            '''
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending host notification email: {e}")
        return False

# Database initialization
def init_db():
    conn = sqlite3.connect('smartcal.db')
    cursor = conn.cursor()
    
    # Check if role column exists, if not add it
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'role' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN role TEXT DEFAULT "user"')
    
    # Check if banned column exists, if not add it
    if 'banned' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN banned BOOLEAN DEFAULT 0')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            alias TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT "user",
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timezone TEXT DEFAULT 'UTC',
            coverage_band INTEGER DEFAULT 30,
            max_bookings INTEGER DEFAULT 3,
            daily_email BOOLEAN DEFAULT 0,
            send_time TEXT DEFAULT '08:00',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            alias_name TEXT UNIQUE NOT NULL,
            duration INTEGER NOT NULL,
            max_bookings_per_day INTEGER DEFAULT 5,
            availability TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            availability TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agenda_id INTEGER NOT NULL,
            visitor_name TEXT NOT NULL,
            visitor_email TEXT NOT NULL,
            booking_date DATE NOT NULL,
            time_slot TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (agenda_id) REFERENCES agendas (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# JWT token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user_id']
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Routes
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/login.html')
def login_page():
    return send_from_directory('.', 'login.html')

@app.route('/register.html')
def register_page():
    return send_from_directory('.', 'register.html')

@app.route('/verify.html')
def verify_page():
    return send_from_directory('.', 'verify.html')

@app.route('/dashboard.html')
def dashboard_page():
    return send_from_directory('.', 'dashboard.html')

@app.route('/SAdashboard.html')
def sa_dashboard_page():
    return send_from_directory('.', 'SAdashboard.html')

@app.route('/agenda_booking_link.html')
def agenda_booking_link():
    return send_from_directory('.', 'agenda_booking_link.html')

@app.route('/booking_page.html')
def booking_page():
    return send_from_directory('.', 'booking_page.html')

@app.route('/forgot-password.html')
def forgot_password_page():
    return send_from_directory('.', 'forgot-password.html')

@app.route('/style.css')
def style_css():
    return send_from_directory('.', 'style.css')

@app.route('/Assets/<path:filename>')
def assets(filename):
    return send_from_directory('Assets', filename)

# API Routes
@app.route('/users/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        alias = data.get('alias')
        password = data.get('password')
        
        if not all([name, email, alias, password]):
            return jsonify({'detail': 'All fields are required'}), 400
        
        # Check if email already exists
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ? OR alias = ?', (email, alias))
        existing_user = cursor.fetchone()
        conn.close()
        
        if existing_user:
            return jsonify({'detail': 'Email or alias already exists'}), 400
        
        # Generate verification code
        verification_code = generate_verification_code()
        
        # Store user data and verification code temporarily
        verification_codes[email] = {
            'code': verification_code,
            'timestamp': datetime.datetime.now(),
            'user_data': {
                'name': name,
                'email': email,
                'alias': alias,
                'password': password
            }
        }
        
        # Send verification email
        if send_verification_email(email, verification_code):
            return jsonify({
                'message': 'Verification code sent to your email',
                'email': email
            }), 200
        else:
            return jsonify({'detail': 'Failed to send verification email'}), 500
            
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/users/verify', methods=['POST'])
def verify_code():
    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')
        
        if not email or not code:
            return jsonify({'detail': 'Email and verification code are required'}), 400
        
        # Check if verification code exists and is valid
        if email not in verification_codes:
            return jsonify({'detail': 'No verification code found for this email'}), 400
        
        stored_data = verification_codes[email]
        stored_code = stored_data['code']
        timestamp = stored_data['timestamp']
        
        # Check if code has expired (5 minutes)
        time_diff = datetime.datetime.now() - timestamp
        if time_diff.total_seconds() > 300:  # 5 minutes = 300 seconds
            # Remove expired code
            del verification_codes[email]
            return jsonify({'detail': 'Verification code has expired. Please sign up again.'}), 400
        
        # Check if code matches
        if code != stored_code:
            return jsonify({'detail': 'Invalid verification code'}), 400
        
        # Code is valid, create the user account
        user_data = stored_data['user_data']
        
        # Hash password
        password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt())
        
        # Save user to database
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, email, alias, password_hash, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_data['name'], user_data['email'], user_data['alias'], password_hash, 'user'))
            conn.commit()
            conn.close()
            
            # Remove verification code from memory
            del verification_codes[email]
            
            return jsonify({'message': 'Account created successfully'}), 201
            
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'detail': 'Email or alias already exists'}), 400
            
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/users/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'detail': 'Email and password are required'}), 400
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user[4]):
            # Check if user is banned
            user_banned = user[7] if len(user) > 7 else False
            if user_banned:
                return jsonify({'detail': 'Your account has been banned. Please contact the administrator.'}), 403
            
            user_role = user[6] if len(user) > 6 else 'user'
            
            token = jwt.encode({
                'user_id': user[0],
                'email': user[2],
                'role': user_role,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            
            response_data = {
                'access_token': token,
                'token_type': 'bearer',
                'user': {
                    'id': user[0],
                    'name': user[1],
                    'email': user[2],
                    'alias': user[3],
                    'role': user_role
                }
            }
            
            print(f"🔐 Login successful for {user[2]} with role: {user_role}")
            
            return jsonify(response_data), 200
        else:
            return jsonify({'detail': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/users/me', methods=['GET'])
@token_required
def get_user_info(current_user):
    try:
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, alias, role FROM users WHERE id = ?', (current_user,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            user_data = {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'alias': user[3],
                'role': user[4] if len(user) > 4 else 'user'
            }
            print(f"👤 User info requested for ID {current_user}")
            return jsonify(user_data), 200
        else:
            return jsonify({'detail': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/agendas/', methods=['GET'])
@token_required
def get_agendas(current_user):
    try:
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, alias_name, duration, max_bookings_per_day, created_at
            FROM agendas WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (current_user,))
        agendas = cursor.fetchall()
        conn.close()
        
        agenda_list = []
        for agenda in agendas:
            agenda_list.append({
                'id': agenda[0],
                'title': agenda[1],
                'aliasName': agenda[2],
                'duration': agenda[3],
                'maxBookingsPerDay': agenda[4],
                'createdAt': agenda[5]
            })
        
        return jsonify(agenda_list), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/users/preferences', methods=['GET'])
@token_required
def get_user_preferences(current_user):
    try:
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timezone, coverage_band, max_bookings, daily_email, send_time
            FROM user_preferences WHERE user_id = ?
        ''', (current_user,))
        preferences = cursor.fetchone()
        conn.close()
        
        if preferences:
            return jsonify({
                'timezone': preferences[0],
                'coverageBand': preferences[1],
                'maxBookings': preferences[2],
                'dailyEmail': bool(preferences[3]),
                'sendTime': preferences[4]
            }), 200
        else:
            # Return default preferences if none exist
            return jsonify({
                'timezone': 'UTC',
                'coverageBand': 30,
                'maxBookings': 3,
                'dailyEmail': False,
                'sendTime': '08:00'
            }), 200
            
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/users/preferences', methods=['POST'])
@token_required
def save_user_preferences(current_user):
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Check if preferences exist for this user
        cursor.execute('SELECT id FROM user_preferences WHERE user_id = ?', (current_user,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing preferences
            cursor.execute('''
                UPDATE user_preferences 
                SET timezone = ?, coverage_band = ?, max_bookings = ?, 
                    daily_email = ?, send_time = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (
                data.get('timezone', 'UTC'),
                data.get('coverageBand', 30),
                data.get('maxBookings', 3),
                data.get('dailyEmail', False),
                data.get('sendTime', '08:00'),
                current_user
            ))
        else:
            # Insert new preferences
            cursor.execute('''
                INSERT INTO user_preferences 
                (user_id, timezone, coverage_band, max_bookings, daily_email, send_time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                current_user,
                data.get('timezone', 'UTC'),
                data.get('coverageBand', 30),
                data.get('maxBookings', 3),
                data.get('dailyEmail', False),
                data.get('sendTime', '08:00')
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Preferences saved successfully'}), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/agendas/create', methods=['POST'])
@token_required
def create_agenda(current_user):
    try:
        data = request.get_json()
        title = data.get('title')
        duration = data.get('duration')
        max_bookings_per_day = data.get('maxBookingsPerDay', 5)
        availability = data.get('availability', {})
        
        if not title or not duration:
            return jsonify({'detail': 'Title and duration are required'}), 400
        
        # Generate unique alias name
        import re
        alias_base = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
        alias_name = alias_base
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Check if alias already exists and make it unique
        counter = 1
        while True:
            cursor.execute('SELECT id FROM agendas WHERE alias_name = ?', (alias_name,))
            if not cursor.fetchone():
                break
            alias_name = f"{alias_base}{counter}"
            counter += 1
        
        # Insert new agenda
        cursor.execute('''
            INSERT INTO agendas (user_id, title, alias_name, duration, max_bookings_per_day, availability)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            current_user,
            title,
            alias_name,
            duration,
            max_bookings_per_day,
            json.dumps(availability)
        ))
        
        conn.commit()
        conn.close()
        
        # Generate booking URL
        booking_url = f"smartcal.one/{alias_name}"
        
        return jsonify({
            'message': 'Agenda created successfully',
            'bookingUrl': booking_url,
            'aliasName': alias_name
        }), 201
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/users/availability', methods=['POST'])
@token_required
def save_user_availability(current_user):
    try:
        data = request.get_json()
        availability = data.get('availability', {})
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Check if availability exists for this user
        cursor.execute('SELECT id FROM user_availability WHERE user_id = ?', (current_user,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing availability
            cursor.execute('''
                UPDATE user_availability 
                SET availability = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (json.dumps(availability), current_user))
        else:
            # Insert new availability
            cursor.execute('''
                INSERT INTO user_availability (user_id, availability)
                VALUES (?, ?)
            ''', (current_user, json.dumps(availability)))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Availability saved successfully'}), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

# Super Admin API Endpoints
@app.route('/admin/stats', methods=['GET'])
@token_required
def get_admin_stats(current_user):
    """Get admin dashboard statistics"""
    try:
        print(f"🔍 Admin stats requested for user ID: {current_user}")
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Get total users
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        # Get total agendas (only valid ones with existing users)
        cursor.execute('''
            SELECT COUNT(*) 
            FROM agendas a
            JOIN users u ON a.user_id = u.id
        ''')
        total_agendas = cursor.fetchone()[0]
        
        # Get pending verifications (users created today)
        cursor.execute('SELECT COUNT(*) FROM users WHERE DATE(created_at) = DATE("now")')
        pending_verifications = cursor.fetchone()[0]
        
        # Get last broadcast sent (placeholder for now)
        last_broadcast = "Jul 25, 2024"
        
        conn.close()
        
        stats = {
            'totalUsers': total_users,
            'totalAgendas': total_agendas,
            'pendingVerifications': pending_verifications,
            'lastBroadcast': last_broadcast
        }
        
        print(f"📊 Admin stats: {stats}")
        return jsonify(stats), 200
        
    except Exception as e:
        print(f"❌ Error in admin stats: {e}")
        return jsonify({'detail': str(e)}), 500

@app.route('/admin/users', methods=['GET'])
@token_required
def get_all_users(current_user):
    """Get all users for admin management"""
    try:
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, email, alias, role, created_at, banned
            FROM users 
            ORDER BY created_at DESC
        ''')
        users = cursor.fetchall()
        conn.close()
        
        user_list = []
        for user in users:
            # Determine status based on banned status and creation date
            if user[6]:  # banned
                status = "Banned"
            else:
                status = "Active" if user[5] else "Pending"
            
            user_list.append({
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'username': user[3],
                'role': user[4],
                'status': status,
                'banned': bool(user[6]),
                'createdAt': user[5]
            })
        
        return jsonify(user_list), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/admin/agendas', methods=['GET'])
@token_required
def get_all_agendas(current_user):
    """Get all agendas for admin management"""
    try:
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.id, a.title, a.alias_name, a.duration, a.max_bookings_per_day, 
                   a.created_at, u.name as creator_name, u.alias as creator_alias
            FROM agendas a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
        ''')
        agendas = cursor.fetchall()
        conn.close()
        
        agenda_list = []
        for agenda in agendas:
            agenda_list.append({
                'id': agenda[0],
                'title': agenda[1],
                'aliasName': agenda[2],
                'duration': agenda[3],
                'maxBookingsPerDay': agenda[4],
                'createdAt': agenda[5],
                'creatorName': agenda[6],
                'creatorAlias': agenda[7]
            })
        
        return jsonify(agenda_list), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/admin/notifications', methods=['POST'])
@token_required
def send_notification(current_user):
    """Send notification to users"""
    try:
        data = request.get_json()
        subject = data.get('subject')
        message = data.get('message')
        recipients = data.get('recipients', 'all')
        selected_users = data.get('selectedUsers', [])
        urgent = data.get('urgent', False)
        
        if not subject or not message:
            return jsonify({'detail': 'Subject and message are required'}), 400
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Create notifications table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                recipients TEXT NOT NULL,
                urgent BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert notification
        cursor.execute('''
            INSERT INTO notifications (subject, message, recipients, urgent)
            VALUES (?, ?, ?, ?)
        ''', (subject, message, recipients, urgent))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Notification sent successfully'}), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/admin/change-password', methods=['POST'])
@token_required
def change_admin_password(current_user):
    """Change admin password"""
    try:
        data = request.get_json()
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        confirm_password = data.get('confirmPassword')
        
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'detail': 'All password fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'detail': 'New passwords do not match'}), 400
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Get current user's password hash
        cursor.execute('SELECT password_hash FROM users WHERE id = ?', (current_user,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'detail': 'User not found'}), 404
        
        # Verify current password
        if not bcrypt.checkpw(current_password.encode('utf-8'), user[0]):
            conn.close()
            return jsonify({'detail': 'Current password is incorrect'}), 400
        
        # Hash new password
        new_password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Update password
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_password_hash, current_user))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/admin/ban-user', methods=['POST'])
@token_required
def ban_user(current_user):
    """Ban a user"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'detail': 'User ID is required'}), 400
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Check if user exists and is not already banned
        cursor.execute('SELECT id, name, email, role, banned FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'detail': 'User not found'}), 404
        
        if user[4]:  # banned field
            conn.close()
            return jsonify({'detail': 'User is already banned'}), 400
        
        # Ban the user
        cursor.execute('UPDATE users SET banned = 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        print(f"🔨 User {user[2]} (ID: {user_id}) banned by admin {current_user}")
        return jsonify({'message': f'User {user[1]} has been banned successfully'}), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/admin/unban-user', methods=['POST'])
@token_required
def unban_user(current_user):
    """Unban a user"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({'detail': 'User ID is required'}), 400
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Check if user exists and is banned
        cursor.execute('SELECT id, name, email, role, banned FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'detail': 'User not found'}), 404
        
        if not user[4]:  # banned field
            conn.close()
            return jsonify({'detail': 'User is not banned'}), 400
        
        # Unban the user
        cursor.execute('UPDATE users SET banned = 0 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        print(f"🔓 User {user[2]} (ID: {user_id}) unbanned by admin {current_user}")
        return jsonify({'message': f'User {user[1]} has been unbanned successfully'}), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/admin/delete-agenda', methods=['POST'])
@token_required
def delete_agenda(current_user):
    """Delete an agenda"""
    try:
        data = request.get_json()
        agenda_id = data.get('agendaId')
        
        if not agenda_id:
            return jsonify({'detail': 'Agenda ID is required'}), 400
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Check if agenda exists
        cursor.execute('SELECT id, title, user_id FROM agendas WHERE id = ?', (agenda_id,))
        agenda = cursor.fetchone()
        
        if not agenda:
            conn.close()
            return jsonify({'detail': 'Agenda not found'}), 404
        
        # Get user info for logging
        cursor.execute('SELECT name, email FROM users WHERE id = ?', (agenda[2],))
        user = cursor.fetchone()
        user_name = user[0] if user else 'Unknown User'
        
        # Delete the agenda
        cursor.execute('DELETE FROM agendas WHERE id = ?', (agenda_id,))
        conn.commit()
        conn.close()
        
        print(f"🗑️ Agenda '{agenda[1]}' (ID: {agenda_id}) deleted by admin {current_user}. Created by: {user_name}")
        return jsonify({'message': f'Agenda "{agenda[1]}" has been deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/notifications', methods=['GET'])
@token_required
def get_user_notifications(current_user):
    """Get notifications for current user"""
    try:
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Create notifications table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                recipients TEXT NOT NULL,
                urgent BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Get notifications for this user
        cursor.execute('''
            SELECT id, subject, message, urgent, created_at
            FROM notifications 
            WHERE recipients = 'all' OR recipients LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{current_user}%',))
        
        notifications = cursor.fetchall()
        conn.close()
        
        notification_list = []
        for notification in notifications:
            notification_list.append({
                'id': notification[0],
                'subject': notification[1],
                'message': notification[2],
                'urgent': bool(notification[3]),
                'createdAt': notification[4]
            })
        
        return jsonify(notification_list), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/agenda/<int:agenda_id>/availability', methods=['GET'])
def get_agenda_availability(agenda_id):
    """Get agenda availability schedule"""
    try:
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Get agenda details including availability
        cursor.execute('''
            SELECT id, title, duration, max_bookings_per_day, user_id, availability
            FROM agendas WHERE id = ?
        ''', (agenda_id,))
        agenda = cursor.fetchone()
        
        if not agenda:
            conn.close()
            return jsonify({'detail': 'Agenda not found'}), 404
        
        # Parse the availability data from JSON
        availability_data = json.loads(agenda[5]) if agenda[5] else {}
        
        conn.close()
        
        return jsonify({
            'agendaId': agenda[0],
            'title': agenda[1],
            'duration': agenda[2],
            'maxBookingsPerDay': agenda[3],
            'availability': availability_data
        }), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/agenda/<int:agenda_id>/slots/<date>', methods=['GET'])
def get_available_slots(agenda_id, date):
    """Get available time slots for a specific date"""
    try:
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Get agenda details including availability
        cursor.execute('''
            SELECT id, title, duration, max_bookings_per_day, availability
            FROM agendas WHERE id = ?
        ''', (agenda_id,))
        agenda = cursor.fetchone()
        
        if not agenda:
            conn.close()
            return jsonify({'detail': 'Agenda not found'}), 404
        
        # Parse availability data
        availability_data = json.loads(agenda[4]) if agenda[4] else {}
        
        # Check if date is an available day based on the agenda's availability schedule
        from datetime import datetime
        selected_date = datetime.strptime(date, '%Y-%m-%d')
        day_name = selected_date.strftime('%A').lower()
        
        # Check if this day is available in the agenda's schedule
        if day_name not in availability_data:
            conn.close()
            return jsonify({
                'available': False,
                'message': 'No slots available for this date. Please choose another day.'
            }), 200
        
        # Get the time range for this day
        day_schedule = availability_data[day_name]
        start_time = day_schedule.get('start', '09:00')
        end_time = day_schedule.get('end', '17:00')
        
        # Convert time strings to minutes for easier calculation
        def time_to_minutes(time_str):
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        
        start_minutes = time_to_minutes(start_time)
        end_minutes = time_to_minutes(end_time)
        duration = agenda[2]  # minutes
        
        # Get booked slots for this date
        cursor.execute('''
            SELECT time_slot FROM bookings 
            WHERE agenda_id = ? AND booking_date = ?
        ''', (agenda_id, date))
        booked_slots = [row[0] for row in cursor.fetchall()]
        
        # Generate time slots within the available time range
        available_slots = []
        current_time = start_minutes
        
        while current_time + duration <= end_minutes:
            time_str = f"{current_time // 60:02d}:{current_time % 60:02d}"
            time_display = f"{current_time // 60:02d}:{current_time % 60:02d} {'AM' if current_time < 12 * 60 else 'PM'}"
            
            if time_str not in booked_slots:
                available_slots.append({
                    'time': time_str,
                    'display': time_display,
                    'available': True
                })
            else:
                available_slots.append({
                    'time': time_str,
                    'display': time_display,
                    'available': False
                })
            
            current_time += duration
        
        conn.close()
        
        return jsonify({
            'available': True,
            'slots': available_slots,
            'date': date
        }), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/booking/create', methods=['POST'])
def create_booking():
    """Create a new booking"""
    try:
        data = request.get_json()
        agenda_id = data.get('agendaId')
        visitor_name = data.get('visitorName')
        visitor_email = data.get('visitorEmail')
        booking_date = data.get('bookingDate')
        time_slot = data.get('timeSlot')
        
        if not all([agenda_id, visitor_name, visitor_email, booking_date, time_slot]):
            return jsonify({'detail': 'All booking details are required'}), 400
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Check if slot is still available
        cursor.execute('''
            SELECT id FROM bookings 
            WHERE agenda_id = ? AND booking_date = ? AND time_slot = ?
        ''', (agenda_id, booking_date, time_slot))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'detail': 'This slot is no longer available. Please select another.'}), 400
        
        # Get agenda and user details for email notifications
        cursor.execute('''
            SELECT a.title, a.duration, a.alias_name, u.name, u.email
            FROM agendas a
            JOIN users u ON a.user_id = u.id
            WHERE a.id = ?
        ''', (agenda_id,))
        
        agenda_info = cursor.fetchone()
        if not agenda_info:
            conn.close()
            return jsonify({'detail': 'Agenda not found'}), 404
        
        agenda_title, duration, alias_name, host_name, host_email = agenda_info
        
        # Create booking
        cursor.execute('''
            INSERT INTO bookings (agenda_id, visitor_name, visitor_email, booking_date, time_slot, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (agenda_id, visitor_name, visitor_email, booking_date, time_slot))
        
        booking_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Send confirmation email to visitor
        send_booking_confirmation_visitor(
            visitor_email, visitor_name, agenda_title, host_name, 
            booking_date, time_slot, duration, alias_name
        )
        
        # Send notification email to host
        send_booking_notification_host(
            host_email, host_name, visitor_name, visitor_email,
            agenda_title, booking_date, time_slot, duration
        )
        
        return jsonify({
            'message': 'Booking created successfully! Check your email for confirmation.',
            'bookingId': booking_id
        }), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

@app.route('/meetings/upcoming', methods=['GET'])
@token_required
def get_upcoming_meetings(current_user):
    """Get upcoming meetings for the current user"""
    try:
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # Get all upcoming meetings for the user's agendas
        cursor.execute('''
            SELECT 
                b.id,
                b.visitor_name,
                b.visitor_email,
                b.booking_date,
                b.time_slot,
                b.created_at,
                a.title as agenda_title,
                a.duration,
                a.alias_name
            FROM bookings b
            JOIN agendas a ON b.agenda_id = a.id
            WHERE a.user_id = ? AND b.booking_date >= DATE('now')
            ORDER BY b.booking_date ASC, b.time_slot ASC
        ''', (current_user,))
        
        meetings = []
        for row in cursor.fetchall():
            booking_id, visitor_name, visitor_email, booking_date, time_slot, created_at, agenda_title, duration, alias_name = row
            
            # Format date and time
            from datetime import datetime
            date_obj = datetime.strptime(booking_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
            
            time_obj = datetime.strptime(time_slot, '%H:%M')
            formatted_time = time_obj.strftime('%I:%M %p')
            
            meetings.append({
                'id': booking_id,
                'visitor_name': visitor_name,
                'visitor_email': visitor_email,
                'booking_date': booking_date,
                'formatted_date': formatted_date,
                'time_slot': time_slot,
                'formatted_time': formatted_time,
                'agenda_title': agenda_title,
                'duration': duration,
                'alias_name': alias_name,
                'created_at': created_at
            })
        
        conn.close()
        
        return jsonify({
            'meetings': meetings,
            'count': len(meetings)
        }), 200
        
    except Exception as e:
        return jsonify({'detail': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000) 