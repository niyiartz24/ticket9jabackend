import os
from dotenv import load_dotenv
from db import get_db_connection, release_db_connection

load_dotenv()

def create_tables():
    """Create all database tables"""
    conn = get_db_connection()
    conn.autocommit = False
    
    try:
        cur = conn.cursor()
        
        print("Creating tables...")
        
        # Users table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'scanner')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Events table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                event_date TIMESTAMP NOT NULL,
                location VARCHAR(255) NOT NULL,
                capacity INTEGER NOT NULL,
                status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'closed')),
                banner_image TEXT,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Ticket types table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS ticket_types (
                id SERIAL PRIMARY KEY,
                event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10, 2) DEFAULT 0,
                quantity INTEGER NOT NULL,
                quantity_issued INTEGER DEFAULT 0,
                is_custom BOOLEAN DEFAULT FALSE,
                description TEXT,
                color VARCHAR(7),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tickets table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id SERIAL PRIMARY KEY,
                event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,
                ticket_type_id INTEGER REFERENCES ticket_types(id),
                qr_code TEXT NOT NULL,
                ticket_number VARCHAR(50) UNIQUE NOT NULL,
                recipient_name VARCHAR(255) NOT NULL,
                recipient_email VARCHAR(255) NOT NULL,
                recipient_phone VARCHAR(50),
                ticket_bg_image TEXT,
                status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'used', 'cancelled')),
                email_sent BOOLEAN DEFAULT FALSE,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check-ins table
        cur.execute('''
            CREATE TABLE IF NOT EXISTS check_ins (
                id SERIAL PRIMARY KEY,
                ticket_id INTEGER REFERENCES tickets(id) ON DELETE CASCADE,
                scanner_id INTEGER REFERENCES users(id),
                check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Commit
        conn.commit()
        cur.close()
        
        print("All tables created successfully")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise e
        
    finally:
        release_db_connection(conn)

if __name__ == '__main__':
    db_url = os.getenv('DATABASE_URL', '')
    if db_url:
        print(f"Using database: {db_url[:50]}...")
    else:
        print("DATABASE_URL not found in environment!")
        exit(1)
    
    create_tables()
