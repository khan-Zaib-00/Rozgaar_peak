import sqlite3
import os

db_paths = [
    'job_portal.db',
    'instance/job_portal.db'
]

for path in db_paths:
    print(f"\nChecking {path}...")
    if not os.path.exists(path):
        print("File does not exist.")
        continue
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(jobs);")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
    conn.close()
