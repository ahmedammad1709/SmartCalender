import sqlite3
import bcrypt
import os

def fetch_all_accounts():
    """Fetch all user accounts from the database"""
    try:
        # Check if database file exists
        if not os.path.exists('smartcal.db'):
            print("Error: smartcal.db file not found!")
            return []
        
        print(f"Database file size: {os.path.getsize('smartcal.db')} bytes")
        
        conn = sqlite3.connect('smartcal.db')
        cursor = conn.cursor()
        
        # First, let's check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {[table[0] for table in tables]}")
        
        # Check if users table exists
        if not any('users' in table for table in tables):
            print("Error: 'users' table not found in database!")
            return []
        
        # Get all users with their details
        cursor.execute('''
            SELECT id, name, email, alias, password_hash, role, created_at, banned
            FROM users 
            ORDER BY created_at DESC
        ''')
        
        users = cursor.fetchall()
        print(f"Found {len(users)} users in database")
        conn.close()
        
        if not users:
            print("No users found in the database.")
            return []
        
        print("=" * 80)
        print("SMARTCAL USER ACCOUNTS")
        print("=" * 80)
        print(f"Total accounts found: {len(users)}")
        print()
        
        admin_count = 0
        user_count = 0
        
        for i, user in enumerate(users, 1):
            user_id, name, email, alias, password_hash, role, created_at, banned = user
            
            # Count by role
            if role == 'admin':
                admin_count += 1
            else:
                user_count += 1
            
            status = "BANNED" if banned else "ACTIVE"
            role_display = role.upper() if role else "USER"
            
            print(f"Account #{i}")
            print(f"  ID: {user_id}")
            print(f"  Name: {name}")
            print(f"  Email: {email}")
            print(f"  Alias: {alias}")
            print(f"  Role: {role_display}")
            print(f"  Status: {status}")
            print(f"  Created: {created_at}")
            print(f"  Password Hash: {password_hash[:50]}...")  # Show first 50 chars of hash
            print("-" * 40)
        
        print()
        print("SUMMARY:")
        print(f"  Total Accounts: {len(users)}")
        print(f"  Admin Accounts: {admin_count}")
        print(f"  Regular User Accounts: {user_count}")
        print(f"  Banned Accounts: {sum(1 for user in users if user[7])}")
        print(f"  Active Accounts: {sum(1 for user in users if not user[7])}")
        print("=" * 80)
        
        return users
        
    except Exception as e:
        print(f"Error fetching accounts: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_password_decryption():
    """Test if we can decrypt any passwords (for demonstration only)"""
    print("\n" + "=" * 80)
    print("PASSWORD DECRYPTION TEST")
    print("=" * 80)
    print("Note: Passwords are hashed with bcrypt and cannot be decrypted.")
    print("This is a security feature to protect user passwords.")
    print("=" * 80)

if __name__ == "__main__":
    print("Starting account fetch...")
    accounts = fetch_all_accounts()
    test_password_decryption() 