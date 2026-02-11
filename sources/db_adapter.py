"""
Database Adapter - Switch between SQLite (local) and Postgres (production)
"""
import os
from typing import Optional

# Detect environment
DATABASE_URL = os.getenv('DATABASE_URL')
IS_PRODUCTION = DATABASE_URL is not None and 'postgres' in DATABASE_URL

if IS_PRODUCTION:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    def get_connection():
        """Get Postgres connection for production."""
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
        return conn
    
    def execute_query(query, params=None):
        """Execute query on Postgres."""
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params or ())
        return cursor
    
else:
    import sqlite3
    from pathlib import Path
    
    DB_PATH = Path(__file__).resolve().parents[1] / "data" / "market_radar.db"
    
    def get_connection():
        """Get SQLite connection for local development."""
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(query, params=None):
        """Execute query on SQLite."""
        # Convert Postgres syntax to SQLite if needed
        query = query.replace('RETURNING', 'RETURNING')  # SQLite 3.35+ supports this
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        return cursor

# Export the detector
__all__ = ['get_connection', 'execute_query', 'IS_PRODUCTION']
