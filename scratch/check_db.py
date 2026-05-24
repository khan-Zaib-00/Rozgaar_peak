import sqlite3

conn = sqlite3.connect('job_portal.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(jobs);")
columns = cursor.fetchall()
for col in columns:
    print(col)
conn.close()
