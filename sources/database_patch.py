"""
Patch for database.py to support Postgres in production
Import this BEFORE importing database module
"""
import os
import sys
from urllib.parse import urlparse, unquote

# Check if we're in production (Vercel)
DATABASE_URL = os.getenv('DATABASE_URL')
IS_POSTGRES = DATABASE_URL and 'postgres' in DATABASE_URL

if IS_POSTGRES:
    # We're in production, use Postgres
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import sqlite3
    
    # Parse DATABASE_URL to handle special characters correctly
    parsed = urlparse(DATABASE_URL)
    
    # Build connection parameters safely
    conn_params = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/'),
        'user': unquote(parsed.username) if parsed.username else None,
        'password': unquote(parsed.password) if parsed.password else None,
        'sslmode': 'require'
    }
    
    # Monkey patch sqlite3.connect to use Postgres instead
    original_connect = sqlite3.connect
    
    class PostgresConnection:
        def __init__(self):
            self.conn = psycopg2.connect(**conn_params)
            self.row_factory = None
            
        def cursor(self):
            return self.conn.cursor(cursor_factory=RealDictCursor)
        
        def commit(self):
            self.conn.commit()
            
        def close(self):
            self.conn.close()
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            self.close()
    
    def postgres_connect(*args, **kwargs):
        """Replace SQLite connect with Postgres."""
        return PostgresConnection()
    
    # Monkey patch!
    import sqlite3
    sqlite3.connect = postgres_connect
    
    print(f"[database_patch] ✅ Using Postgres (Supabase) - Host: {conn_params['host']}")
else:
    print("[database_patch] ℹ️  Using SQLite (local development)")
