import sqlite3
import bcrypt
import datetime

def create_initial_admin():
    """Create an initial admin user for testing"""
    conn = sqlite3.connect('smartcal.db')
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            alias TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT "user",
            banned BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if admin already exists
    cursor.execute('SELECT id FROM users WHERE email = ?', ('admin@smartcal.com',))
    if cursor.fetchone():
        print("Admin user already exists!")
        conn.close()
        return
    
    # Create admin user
    admin_email = 'admin@smartcal.com'
    admin_password = 'Admin123!'
    admin_name = 'Super Admin'
    admin_alias = 'admin'
    
    # Hash password
    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
    
    # Insert admin user
    cursor.execute('''
        INSERT INTO users (name, email, alias, password_hash, role, created_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ''', (admin_name, admin_email, admin_alias, password_hash, 'admin'))
    
    conn.commit()
    conn.close()
    
    print("✅ Initial admin user created successfully!")
    print(f"Email: {admin_email}")
    print(f"Password: {admin_password}")
    print("You can now login to the admin dashboard with these credentials.")

if __name__ == '__main__':
    create_initial_admin() 