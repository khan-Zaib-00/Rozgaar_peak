import pandas as pd
from sqlalchemy import create_engine
from faker import Faker
import random
from models.db import get_db_connection

def seed_jobs():
    print("Starting seed script...")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE role = 'employer' LIMIT 1")
            employer_user = cursor.fetchone()
            
            if not employer_user:
                cursor.execute("INSERT INTO users (name, email, password, role) VALUES ('System Employer', 'sys@employers.com', 'pass', 'employer')")
                conn.commit()
                employer_id = cursor.lastrowid
            else:
                employer_id = employer_user['id']
                
            cursor.execute("SELECT id FROM companies WHERE user_id = ? LIMIT 1", (employer_id,))
            company = cursor.fetchone()
            
            if not company:
                cursor.execute("INSERT INTO companies (user_id, company_name, description) VALUES (?, 'Tech Data Corp', 'An AI & Data Science leading firm.')", (employer_id,))
                conn.commit()
                company_id = cursor.lastrowid
            else:
                company_id = company['id']
    except Exception as e:
        print(f"Error accessing DB: {e}")
        return
    finally:
        conn.close()

    jobs_data = []
    titles = ['Data Analyst', 'Data Scientist', 'Machine Learning Engineer', 'AI Researcher', 'Deep Learning Specialist',
              'Data Engineer', 'NLP Engineer', 'Computer Vision Expert', 'Big Data Architect', 'Business Intelligence Analyst']
    locations = ['Karachi', 'Lahore', 'Islamabad', 'Remote', 'Remote']
    job_types = ['full-time', 'full-time', 'remote', 'part-time']
    fake = Faker()
    
    for i in range(15):
        title = random.choice(titles)
        if i == 0: title = 'Data Analyst'
        elif i == 1: title = 'Machine Learning Engineer'
        elif i == 2: title = 'AI Researcher'
            
        jobs_data.append({
            'company_id': company_id,
            'title': title,
            'description': f"We are looking for a skilled {title}. Requirements: Python, Pandas, Machine Learning, Data Analytics, Python scripting. {fake.paragraph()}",
            'salary': random.randint(50000, 300000),
            'location': random.choice(locations),
            'job_type': random.choice(job_types)
        })
        
    df = pd.DataFrame(jobs_data)
    engine = create_engine('sqlite:///job_portal.db')
    
    try:
        df.to_sql('jobs', con=engine, if_exists='append', index=False)
        print("Success! 15 Data Science jobs have been inserted into the database via Pandas.")
    except Exception as e:
        print("Failed to insert via Pandas:", e)

if __name__ == "__main__":
    seed_jobs()
