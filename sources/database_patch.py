"""
Patch for database.py to support Postgres in production
Import this BEFORE importing database module
"""
import os
import sys

# Check if we're in production (Vercel)
DATABASE_URL = os.getenv('DATABASE_URL')
IS_POSTGRES = DATABASE_URL and 'postgres' in DATABASE_URL

if IS_POSTGRES:
    # We're in production, use Postgres
    import psycopg2
    from psycopg2.extras import RealDictCursor
    import sqlite3
    
    # Monkey patch sqlite3.connect to use Postgres instead
    original_connect = sqlite3.connect
    
    class PostgresConnection:
        def __init__(self):
            self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
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
    sqlite3.connect = postgres_connect
    
    print("[database_patch] ✅ Using Postgres (Supabase)")
else:
    print("[database_patch] ℹ️  Using SQLite (local development)")
