from flask import Blueprint, render_template, request, session
from models.schema import db, Job, Company, Profile
import pandas as pd
from fuzzywuzzy import process, fuzz

jobs_bp = Blueprint('jobs', __name__, url_prefix='/jobs')

@jobs_bp.route('/')
def list_jobs():
    try:
        # Fetch all jobs with company info using SQLAlchemy
        jobs_query = Job.query.order_by(Job.created_at.desc()).all()
        
        # Convert to list of dicts for Pandas
        jobs_data = []
        for j in jobs_query:
            jobs_data.append({
                'id': j.id,
                'title': j.title,
                'description': j.description,
                'salary': j.salary,
                'location': j.location,
                'job_type': j.job_type,
                'category': j.category,
                'company_name': j.company.company_name,
                'created_at': j.created_at
            })
            
        # Get unique locations for filter
        locations = sorted(list(set([j.location for j in jobs_query if j.location])))
        
        if not jobs_data:
            return render_template('jobs/list.html', jobs=[], locations=[])

        # Pandas Search and Filtering
        df = pd.DataFrame(jobs_data)
        
        keyword = request.args.get('keyword', '').lower()
        location = request.args.get('location', '')
        min_salary = request.args.get('min_salary', type=float)
        job_type = request.args.get('job_type', '')
        
        if keyword:
            # Smart Search with Fuzzy Matching
            choices = df['title'].tolist() + df['description'].tolist()
            matches = process.extract(keyword, choices, limit=50, scorer=fuzz.partial_ratio)
            matched_texts = [m[0] for m in matches if m[1] > 60]
            
            mask_fuzzy = df['title'].isin(matched_texts) | df['description'].isin(matched_texts)
            mask_contains = df['title'].str.contains(keyword, case=False, na=False) | \
                            df['description'].str.contains(keyword, case=False, na=False)
            
            df = df[mask_fuzzy | mask_contains]
            
        if location:
            df = df[df['location'] == location]
            
        if job_type:
            df = df[df['job_type'] == job_type]
            
        if min_salary is not None:
            df['salary'] = pd.to_numeric(df['salary'], errors='coerce')
            df = df[df['salary'] >= min_salary]
            
        filtered_jobs = df.to_dict('records')
        
        # Manual Pagination for Filtered Results
        page = request.args.get('page', 1, type=int)
        per_page = 10
        total_jobs = len(filtered_jobs)
        total_pages = (total_jobs + per_page - 1) // per_page
        
        start = (page - 1) * per_page
        end = start + per_page
        paged_jobs = filtered_jobs[start:end]
        
        return render_template('jobs/list.html', 
                               jobs=paged_jobs, 
                               locations=locations, 
                               keyword=keyword, 
                               selected_location=location, 
                               min_salary=min_salary, 
                               selected_job_type=job_type,
                               page=page,
                               total_pages=total_pages)
    except Exception as e:
        print(f"Jobs list error: {e}")
        return render_template('jobs/list.html', jobs=[], locations=[])

@jobs_bp.route('/<int:job_id>')
def job_details(job_id):
    try:
        job = Job.query.get(job_id)
        if not job:
            return "Job not found", 404
            
        # If user is logged in as a seeker, calculate skill match
        skill_match = None
        if session.get('role') == 'seeker':
            profile = Profile.query.filter_by(user_id=session.get('user_id')).first()
            if profile and profile.skills:
                user_skills = [s.strip().lower() for s in profile.skills.split(',') if s.strip()]
                job_text = (str(job.title) + " " + str(job.description)).lower()
                matched_skills = [skill for skill in user_skills if skill in job_text]
                
                if user_skills:
                    match_percent = int((len(matched_skills) / len(user_skills)) * 100)
                    skill_match = {
                        'percent': match_percent,
                        'matched': matched_skills[:5],
                        'missing': list(set(user_skills) - set(matched_skills))[:3]
                    }
                    
        return render_template('jobs/details.html', job=job, skill_match=skill_match)
    except Exception as e:
        print(f"Job details error: {e}")
        return "Internal server error", 500
