from models.schema import db, User, Company, Job, Profile
from app import app
import pandas as pd
import random
import os
from werkzeug.security import generate_password_hash

def seed_database():
    with app.app_context():
        # Clear existing data for a fresh start
        print("Clearing existing database...")
        db.drop_all()
        db.create_all()
        
        # Create a professional employer
        employer = User(
            name='RozgaarSphere Placements', 
            email='employer@jobportal.com', 
            password=generate_password_hash('employer123'), 
            role='employer'
        )
        db.session.add(employer)
        
        # Also create the admin account here for convenience
        admin = User(
            name='RozgaarSphere Admin', 
            email='admin@rozgaarsphere.com', 
            password=generate_password_hash('admin123'), 
            role='admin'
        )
        db.session.add(admin)
        
        # Create a test seeker with skills to test recommendations
        seeker = User(
            name='Test Seeker', 
            email='seeker@test.com', 
            password=generate_password_hash('seeker123'), 
            role='seeker'
        )
        db.session.add(seeker)
        db.session.commit()
        
        seeker_profile = Profile(
            user_id=seeker.id,
            skills='Python, Flask, SQL, HTML, CSS',
            experience='2 years of junior development experience.',
            headline='Aspiring Backend Developer'
        )
        db.session.add(seeker_profile)
        
        # Create a company profile
        company = Company(
            user_id=employer.id, 
            company_name='RozgaarSphere Placements', 
            description='Pakistan\'s leading talent acquisition and recruitment platform.'
        )
        db.session.add(company)
        db.session.commit()
        
        categories = [
            'Flask Backend', 'Full-Stack Python', 'SQL Architect', 
            'Data Analysis', 'Python Automation', 'Machine Learning',
            'Generative AI', 'NLP Engineer', 'Data Engineering', 'Computer Vision'
        ]
        
        seniority_levels = ['Junior', 'Associate', 'Mid-Level', 'Senior', 'Lead', 'Principal', 'Staff']
        
        # Primary cities (higher probability) and secondary cities
        primary_cities = ['Karachi', 'Lahore', 'Islamabad', 'Remote']
        secondary_cities = ['Faisalabad', 'Multan', 'Peshawar', 'Quetta', 'Sialkot', 'Rawalpindi']
        locations = primary_cities + secondary_cities
        
        keywords = {
            'Flask Backend': ['Flask', 'REST API', 'SQLAlchemy', 'Jinja2', 'Authentication', 'Security'],
            'Full-Stack Python': ['Python', 'HTML5', 'CSS3', 'Bootstrap 5', 'Flask', 'Template Rendering'],
            'SQL Architect': ['SQLAlchemy', 'Database Design', 'Optimization', 'SQLite', 'PostgreSQL'],
            'Data Analysis': ['Pandas', 'NumPy', 'Data Visualization', 'Cleaning', 'Statistics'],
            'Python Automation': ['Scripting', 'Automation', 'Requests', 'Crawling', 'Task Schedulers'],
            'Machine Learning': ['Scikit-Learn', 'TensorFlow', 'Deep Learning', 'Pandas', 'Mathematics'],
            'Generative AI': ['LLMs', 'OpenAI', 'LangChain', 'Prompt Engineering', 'Vector DBs', 'RAG'],
            'NLP Engineer': ['Transformers', 'BERT', 'Tokenization', 'NLTK', 'Entity Recognition', 'Translation'],
            'Data Engineering': ['ETL Pipelines', 'Spark', 'Kafka', 'Data Lakes', 'Airflow', 'BigQuery'],
            'Computer Vision': ['OpenCV', 'PyTorch', 'Object Detection', 'Image Segmentation', 'YOLO', 'Face Recognition']
        }

        jobs_list = []
        
        for category in categories:
            print(f"Generating 30 professional tech jobs for {category}...")
            for i in range(1, 31):
                seniority = random.choice(seniority_levels)
                # Ensure a mix of seniority
                if i <= 5: seniority = 'Junior'
                elif i >= 25: seniority = 'Senior'
                
                title = f"{seniority} {category} Specialist"
                
                # Weighted random selection (higher chance for primary cities like Karachi/Lahore)
                location = random.choices(locations, weights=[30, 25, 20, 15, 5, 5, 5, 3, 2, 2])[0]
                salary = random.randint(70, 450) * 1000 # Realistic tech salaries in PKR/Local context
                job_type = 'remote' if location == 'Remote' else random.choice(['full-time', 'part-time'])
                
                # Create a realistic description with tech keywords
                cat_keywords = keywords[category]
                desc_keywords = ", ".join(random.sample(cat_keywords, 4))
                description = (
                    f"RozgaarSphere is seeking a highly skilled {title} to join our tech hub. "
                    f"Key requirements: {desc_keywords}. "
                    f"You will be responsible for maintaining our core {category} infrastructure. "
                    f"Join our dynamic team and make an impact!"
                )
                
                jobs_list.append({
                    'company_id': company.id,
                    'title': title,
                    'description': description,
                    'salary': salary,
                    'location': location,
                    'category': category,
                    'job_type': job_type
                })
        
        # Use Pandas for data processing
        df_jobs = pd.DataFrame(jobs_list)
        
        # Batch insertion
        for _, row in df_jobs.iterrows():
            job = Job(
                company_id=row['company_id'],
                title=row['title'],
                description=row['description'],
                salary=row['salary'],
                location=row['location'],
                category=row['category'],
                job_type=row['job_type']
            )
            db.session.add(job)
        
        db.session.commit()
        print(f"Successfully seeded {len(jobs_list)} professional jobs across {len(categories)} tech categories.")

if __name__ == '__main__':
    seed_database()
