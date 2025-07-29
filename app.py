from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import bcrypt
import jwt
import datetime
import os
import json
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)

# Database initialization
def init_db():
    conn = sqlite3.connect('smartcal.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            alias TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
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

@app.route('/dashboard.html')
def dashboard_page():
    return send_from_directory('.', 'dashboard.html')

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
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, email, alias, password_hash)
                VALUES (?, ?, ?, ?)
            ''', (name, email, alias, password_hash))
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'User registered successfully'}), 201
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
            token = jwt.encode({
                'user_id': user[0],
                'email': user[2],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            
            return jsonify({
                'access_token': token,
                'token_type': 'bearer',
                'user': {
                    'id': user[0],
                    'name': user[1],
                    'email': user[2],
                    'alias': user[3]
                }
            }), 200
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
        cursor.execute('SELECT id, name, email, alias FROM users WHERE id = ?', (current_user,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'alias': user[3]
            }), 200
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

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000) 