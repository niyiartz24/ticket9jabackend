import sys
import os

# Add backend directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import bcrypt
from database.db import execute_query, init_db
from datetime import datetime, timedelta

def seed_database():
    """Seed the database with admin and scanner accounts"""
    print("Seeding database...")
    
    # Initialize database connection
    try:
        init_db()
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        return
    
    # Hash password using bcrypt (matches auth.py)
    password_hash = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create admin user
    print("Creating admin user...")
    try:
        admin = execute_query('''
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
            RETURNING id
        ''', ('admin@ticket9ja.com', password_hash, 'Admin User', 'admin'))
        
        if admin:
            admin_id = admin[0]['id']
            print(f"   Admin created/updated (ID: {admin_id})")
        else:
            admin_result = execute_query('SELECT id FROM users WHERE email = %s', ('admin@ticket9ja.com',))
            admin_id = admin_result[0]['id'] if admin_result else None
            print("   Admin already exists")
    except Exception as e:
        print(f"   Failed to create admin: {e}")
        admin_id = None
    
    # Create scanner user
    print("Creating scanner user...")
    try:
        scanner = execute_query('''
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash
            RETURNING id
        ''', ('scanner@ticket9ja.com', password_hash, 'Scanner User', 'scanner'))
        
        if scanner:
            print(f"   Scanner created/updated")
        else:
            print("   Scanner already exists")
    except Exception as e:
        print(f"   Failed to create scanner: {e}")
    
    # Create sample event (only if admin was created)
    if admin_id:
        print("Creating sample event...")
        try:
            event = execute_query('''
                INSERT INTO events (created_by, name, description, event_date, location, capacity, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                admin_id,
                'Tech Conference 2025',
                'Annual technology and innovation conference',
                datetime.now() + timedelta(days=30),
                'Convention Center, San Francisco, CA',
                5000,
                'active'
            ))
            
            if event:
                event_id = event[0]['id']
                print(f"   Event created (ID: {event_id})")
                
                # Create default ticket types for this event
                print("Creating ticket types...")
                ticket_types_data = [
                    ('Early bird', 50.00, 100),
                    ('Late bird', 80.00, 50),
                    ('VIP', 150.00, 30),
                    ('Table for 4', 300.00, 10),
                    ('Table for 8', 500.00, 5),
                ]
                
                for name, price, quantity in ticket_types_data:
                    try:
                        execute_query('''
                            INSERT INTO ticket_types (event_id, name, price, quantity, quantity_issued, is_custom, description, color)
                            VALUES (%s, %s, %s, %s, 0, false, %s, %s)
                        ''', (event_id, name, price, quantity, f'{name} tickets', '#3B82F6'), fetch=False)
                        print(f"   Created: {name}")
                    except Exception as e:
                        print(f"   Failed to create {name}: {e}")
                
                print(f"   All ticket types created for event {event_id}")
            else:
                print("   Failed to create event")
        except Exception as e:
            print(f"   Failed to create event: {e}")
    
    print("\nDatabase seeded successfully!\n")
    print("="* 60)
    print("Login Accounts:")
    print("=" * 60)
    print("   Admin Dashboard:")
    print("   Email:    admin@ticket9ja.com")
    print("   Password: password123")
    print("")
    print("   Scanner App:")
    print("   Email:    scanner@ticket9ja.com")
    print("   Password: password123")
    print("=" * 60)
    print("\nReady to use!")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    # Verify DATABASE_URL exists
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not found in environment!")
        print("Set DATABASE_URL environment variable first")
        print("Example: export DATABASE_URL='postgres://...'")
    else:
        print(f"Using database: {database_url[:50]}...")
        seed_database()
