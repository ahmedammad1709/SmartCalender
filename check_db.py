import sqlite3
import bcrypt

def check_database():
    conn = sqlite3.connect('smartcal.db')
    cursor = conn.cursor()
    
    # Check if users table exists and has data
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("❌ Users table does not exist!")
        return
    
    # Check table structure
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("📋 Users table columns:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Check existing users
    cursor.execute("SELECT id, name, email, role FROM users")
    users = cursor.fetchall()
    
    print(f"\n👥 Found {len(users)} users:")
    for user in users:
        print(f"  - ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Role: {user[3]}")
    
    # Check if there's an admin user
    cursor.execute("SELECT id, name, email, role FROM users WHERE role = 'admin'")
    admins = cursor.fetchall()
    
    if not admins:
        print("\n⚠️  No admin users found! Creating a default super admin...")
        
        # Create a default super admin
        email = "admin@smartcal.com"
        password = "Admin123!"
        name = "Super Admin"
        alias = "superadmin"
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert admin user
        cursor.execute('''
            INSERT INTO users (name, email, alias, password_hash, role, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (name, email, alias, password_hash, 'admin'))
        
        conn.commit()
        print(f"✅ Created super admin:")
        print(f"  - Email: {email}")
        print(f"  - Password: {password}")
        print(f"  - Role: admin")
    else:
        print(f"\n✅ Found {len(admins)} admin user(s):")
        for admin in admins:
            print(f"  - ID: {admin[0]}, Name: {admin[1]}, Email: {admin[2]}, Role: {admin[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_database() 