import sqlite3
import os
import io

class PostgreSQLAdapter:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return PostgreSQLCursor(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

    @property
    def row_factory(self):
        return getattr(self, "_row_factory", None)

    @row_factory.setter
    def row_factory(self, value):
        self._row_factory = value


class PostgreSQLCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, sql, parameters=()):
        # Translate SQLite-specific syntax to PostgreSQL
        sql = sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        sql = sql.replace("DATETIME DEFAULT CURRENT_TIMESTAMP", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        # Generic fallback for bare DATETIME types (common in ADD COLUMN)
        # Note: We create a simplistic regex or just replace " DATETIME" -> " TIMESTAMP"
        # Be careful not to break strings, but for this simple schema it's fine.
        if " DATETIME" in sql:
            sql = sql.replace(" DATETIME", " TIMESTAMP")
            
        sql = sql.replace("?","%s")
        sql = sql.replace("INSERT OR IGNORE", "INSERT") # Rough approx
        sql = sql.replace("RETURNING id", "RETURNING id") 

        
        # Handle "ON CONFLICT" syntax (SQLite is similar to Postgres, but not identical)
        # We rely on psycopg2 to handle %s parameter binding
        try:
            return self.cursor.execute(sql, parameters)
        except Exception as e:
            # Fallback or logging could go here
            raise e

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    @property
    def description(self):
        return self.cursor.description


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# MONKEY PATCH sqlite3 if DATABASE_URL is present (Production Environment)
if os.environ.get("DATABASE_URL") and "postgres" in os.environ.get("DATABASE_URL"):
    print("[database] 🐘 Detected PostgreSQL environment. Patching sqlite3...")
    try:
        import psycopg2
        import psycopg2.extras
        import urllib.parse as urlparse

        def connect(db_path, **kwargs):
            url = urlparse.urlparse(os.environ["DATABASE_URL"])
            dbname = url.path[1:]
            user = url.username
            password = url.password
            host = url.hostname
            port = url.port
            
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            return PostgreSQLAdapter(conn)

        # Override sqlite3.connect
        sqlite3.connect_original = sqlite3.connect
        sqlite3.connect = connect
        
        # Override Row Factory
        sqlite3.Row = dict_factory 
        
    except ImportError:
        print("[warn] psycopg2 not found. Falling back to SQLite.")
