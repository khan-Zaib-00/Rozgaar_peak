import sqlite3
import os

db_path = 'job_portal.db'

def update_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Update profiles table
    columns_to_add_profiles = [
        ('education', 'TEXT'),
        ('bio', 'TEXT'),
        ('phone', 'TEXT')
    ]
    
    for col_name, col_type in columns_to_add_profiles:
        try:
            cursor.execute(f"ALTER TABLE profiles ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to profiles table.")
        except sqlite3.OperationalError:
            print(f"Column {col_name} already exists in profiles table.")
            
    # Update applications table
    columns_to_add_apps = [
        ('phone', 'TEXT'),
        ('bio', 'TEXT'),
        ('education', 'TEXT'),
        ('skills', 'TEXT'),
        ('experience', 'TEXT')
    ]
    
    for col_name, col_type in columns_to_add_apps:
        try:
            cursor.execute(f"ALTER TABLE applications ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to applications table.")
        except sqlite3.OperationalError:
            print(f"Column {col_name} already exists in applications table.")
            
    conn.commit()
    conn.close()
    print("Database update complete.")

if __name__ == '__main__':
    update_db()
