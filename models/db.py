import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'job_portal.db')

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class SQLiteCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, args=()):
        # Very basic conversion from pymysql %s to sqlite ?
        query = query.replace('%s', '?')
        # Also handle some generic PyMySQL to SQLite SQL translations
        query = query.replace('AUTO_INCREMENT', 'AUTOINCREMENT')
        self.cursor.execute(query, args)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    @property
    def lastrowid(self):
        return self.cursor.lastrowid
        
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()

class SQLiteConnection:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = dict_factory

    def cursor(self):
        return SQLiteCursor(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_db_connection():
    return SQLiteConnection(DB_PATH)

def init_db():
    pass # Managed by SQLAlchemy in app.py now
