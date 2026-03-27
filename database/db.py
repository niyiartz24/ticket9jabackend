import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

connection_pool = None

def init_db():
    """Initialize database connection pool"""
    global connection_pool
    
    try:
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            raise Exception("DATABASE_URL not found")
        
        print(f"Connecting to database...")
        
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,
            database_url
        )
        
        if connection_pool:
            print("Database connection pool created")
        
    except Exception as e:
        print(f"Database connection failed: {e}")
        raise

def get_db_connection():
    """Get a connection from the pool"""
    global connection_pool
    
    if connection_pool is None:
        init_db()
    
    if connection_pool:
        try:
            conn = connection_pool.getconn()
            conn.autocommit = False
            return conn
        except Exception as e:
            print(f"Failed to get connection: {e}")
            raise
    else:
        raise Exception("Connection pool not initialized")

def release_db_connection(conn):
    """Return connection to the pool"""
    global connection_pool
    
    if connection_pool and conn:
        connection_pool.putconn(conn)

def execute_query(query, params=None, fetch=True):
    """Execute a query and return results"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or ())
            
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                conn.commit()
            
            if fetch:
                if query.strip().upper().startswith('SELECT') or 'RETURNING' in query.upper():
                    result = cur.fetchall()
                else:
                    result = None
            else:
                result = None
                
            return result
    except Exception as e:
        conn.rollback()
        print(f"Query error: {e}")
        raise e
    finally:
        release_db_connection(conn)
