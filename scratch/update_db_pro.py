import sqlite3
import os

db_path = 'job_portal.db'

def update_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tables and columns to add
    updates = {
        'profiles': [
            ('linkedin_url', 'TEXT'),
            ('portfolio_url', 'TEXT'),
            ('current_location', 'TEXT'),
            ('expected_salary', 'TEXT')
        ],
        'applications': [
            ('linkedin_url', 'TEXT'),
            ('portfolio_url', 'TEXT'),
            ('current_location', 'TEXT'),
            ('expected_salary', 'TEXT')
        ]
    }
    
    for table, columns in updates.items():
        for col_name, col_type in columns:
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                print(f"Added column {col_name} to {table} table.")
            except sqlite3.OperationalError:
                print(f"Column {col_name} already exists in {table} table.")
            
    conn.commit()
    conn.close()
    print("Database professional upgrade complete.")

if __name__ == '__main__':
    update_db()
