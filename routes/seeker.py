from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, send_from_directory
from werkzeug.utils import secure_filename
from models.schema import db, User, Profile, Company, Job, Application, Notification
import os

seeker_bp = Blueprint('seeker', __name__, url_prefix='/seeker')

def is_seeker():
    return session.get('role') == 'seeker'

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@seeker_bp.route('/dashboard')
def seeker_dashboard():
    if not is_seeker():
        return redirect(url_for('auth.login'))
        
    try:
        profile = Profile.query.filter_by(user_id=session['user_id']).first()
        
        # Calculate Profile Completion
        completion_percent = 0
        missing_fields = []
        if profile:
            fields_map = {
                'Skills': profile.skills, 'Detailed Experience': profile.experience, 
                'Education': profile.education, 'Bio': profile.bio, 
                'Phone': profile.phone, 'LinkedIn URL': profile.linkedin_url,
                'Portfolio URL': profile.portfolio_url, 'Current Location': profile.current_location, 
                'Expected Salary': profile.expected_salary, 'Notice Period': profile.notice_period
            }
            filled_fields = [k for k, v in fields_map.items() if v and str(v).strip()]
            missing_fields = [k for k, v in fields_map.items() if not (v and str(v).strip())]
            completion_percent = len(filled_fields) * 10
            
        # Fetch applications using SQLAlchemy relationships or explicit queries
        applications = db.session.query(Application, Job, Company)\
            .join(Job, Application.job_id == Job.id)\
            .join(Company, Job.company_id == Company.id)\
            .filter(Application.user_id == session['user_id'])\
            .order_by(Application.applied_at.desc()).all()
            
        # Format for template
        apps_formatted = []
        for app, job, comp in applications:
            apps_formatted.append({
                'id': app.id,
                'status': app.status,
                'applied_at': app.applied_at,
                'status_updated_at': app.status_updated_at,
                'title': job.title,
                'company_name': comp.company_name
            })
            
        # Recommendations
        applied_job_ids = [a.job_id for a in Application.query.filter_by(user_id=session['user_id']).all()]
        available_jobs = Job.query.filter(~Job.id.in_(applied_job_ids) if applied_job_ids else True).all()
        
        recommended_jobs = []
        if profile and profile.skills and available_jobs:
            from utils.ai_tools import ResumeParser
            processed_jobs = []
            for job in available_jobs:
                job_text = f"{job.title} {job.description} {job.category}"
                match_percent = ResumeParser.calculate_match_score(profile.skills, job_text)
                
                if match_percent > 30: # 30% threshold for relevance
                    # Extract a few matched skills for the UI
                    user_skills = [s.strip().lower() for s in profile.skills.split(',') if s.strip()]
                    matched_list = [s.title() for s in user_skills if s in job_text.lower()][:3]
                    
                    processed_jobs.append({
                        'id': job.id,
                        'title': job.title,
                        'company_name': job.company.company_name,
                        'match_percent': match_percent,
                        'matched_skills_list': matched_list
                    })
            
            if processed_jobs:
                recommended_jobs = sorted(processed_jobs, key=lambda x: x['match_percent'], reverse=True)[:3]
                    
        return render_template('seeker/dashboard.html', 
                               profile=profile, 
                               applications=apps_formatted, 
                               recommended_jobs=recommended_jobs,
                               completion_percent=completion_percent)
    except Exception as e:
        flash(f"Dashboard error: {str(e)}", "error")
        return redirect(url_for('index'))

@seeker_bp.route('/profile', methods=['GET', 'POST'])
def seeker_profile():
    if not is_seeker():
        return redirect(url_for('auth.login'))
        
    try:
        profile = Profile.query.filter_by(user_id=session['user_id']).first()
        if request.method == 'POST':
            profile.skills = request.form.get('skills')
            profile.experience = request.form.get('experience')
            profile.education = request.form.get('education')
            profile.bio = request.form.get('bio')
            profile.phone = request.form.get('phone')
            profile.linkedin_url = request.form.get('linkedin_url')
            profile.portfolio_url = request.form.get('portfolio_url')
            profile.current_location = request.form.get('current_location')
            profile.expected_salary = request.form.get('expected_salary')
            profile.notice_period = request.form.get('notice_period')
            profile.total_exp = request.form.get('total_exp')
            profile.contact_email = request.form.get('contact_email') # Assuming adding to profile edit too
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('seeker.seeker_dashboard'))
            
        return render_template('seeker/profile.html', profile=profile)
    except Exception as e:
        db.session.rollback()
        flash(f"Profile error: {str(e)}", "error")
        return redirect(url_for('seeker.seeker_dashboard'))

@seeker_bp.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply_job(job_id):
    if not is_seeker():
        flash('You must be logged in as a job seeker to apply.', 'error')
        return redirect(url_for('auth.login'))
        
    try:
        job = Job.query.get(job_id)
        if not job:
            flash('Job not found.', 'error')
            return redirect(url_for('jobs.list_jobs'))
            
        existing_app = Application.query.filter_by(user_id=session['user_id'], job_id=job_id).first()
        if existing_app:
            flash('You have already applied for this job.', 'info')
            return redirect(url_for('seeker.seeker_dashboard'))
            
        if request.method == 'POST':
            if 'cv' not in request.files:
                flash('No file part', 'error')
                return redirect(request.url)
            file = request.files['cv']
            
            if file.filename == '':
                flash('No selected file', 'error')
                return redirect(request.url)
                
            if file and allowed_file(file.filename):
                # Check file size (2MB limit)
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > 2 * 1024 * 1024:
                    flash('File size exceeds 2MB limit.', 'error')
                    return redirect(request.url)
                    
                safe_name = secure_filename(file.filename)
                if len(safe_name) > 50:
                    name_part, ext = os.path.splitext(safe_name)
                    safe_name = name_part[:50-len(ext)] + ext
                filename = f"{session['user_id']}_{job_id}_{safe_name}"
                upload_folder = current_app.config['UPLOAD_FOLDER']
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                
                # Get form data
                name = request.form.get('name')
                email = request.form.get('email')
                phone = request.form.get('phone')
                bio = request.form.get('bio')
                education = request.form.get('education')
                skills = request.form.get('skills')
                experience = request.form.get('experience')
                linkedin_url = request.form.get('linkedin_url')
                portfolio_url = request.form.get('portfolio_url')
                current_location = request.form.get('current_location')
                expected_salary = request.form.get('expected_salary')
                notice_period = request.form.get('notice_period')
                total_exp = request.form.get('total_exp')
                
                new_app = Application(
                    user_id=session['user_id'], 
                    job_id=job_id, 
                    cv_path=filename,
                    full_name=name,
                    contact_email=email,
                    phone=phone,
                    bio=bio,
                    education=education,
                    skills=skills,
                    experience=experience,
                    linkedin_url=linkedin_url,
                    portfolio_url=portfolio_url,
                    current_location=current_location,
                    expected_salary=expected_salary,
                    notice_period=notice_period,
                    total_exp=total_exp
                )
                db.session.add(new_app)
                
                # Update seeker's profile automatically
                profile = Profile.query.filter_by(user_id=session['user_id']).first()
                if profile:
                    profile.phone = phone
                    profile.contact_email = email
                    profile.bio = bio
                    profile.education = education
                    profile.skills = skills
                    profile.experience = experience
                    profile.linkedin_url = linkedin_url
                    profile.portfolio_url = portfolio_url
                    profile.current_location = current_location
                    profile.expected_salary = expected_salary
                    profile.notice_period = notice_period
                    profile.total_exp = total_exp
                    
                    # Also update user's name if changed
                    user = User.query.get(session['user_id'])
                    if user:
                        user.name = name
                        session['name'] = name # Update session too
                
                # Notify the employer
                employer_user_id = job.company.user_id
                notif_msg = f"New application received for your job: {job.title} from {session['name']}"
                new_notif = Notification(user_id=employer_user_id, message=notif_msg[:490])
                db.session.add(new_notif)
                
                db.session.commit()
                flash('Application submitted successfully!', 'success')
                return redirect(url_for('seeker.seeker_dashboard'))
            else:
                flash('Only PDF and DOCX files are allowed for CV.', 'error')
                
        profile = Profile.query.filter_by(user_id=session['user_id']).first()
        return render_template('seeker/apply.html', job=job, job_id=job_id, profile=profile)
    except Exception as e:
        db.session.rollback()
        flash(f"Application error: {str(e)}", "error")
        return redirect(request.url)

@seeker_bp.route('/parse_resume', methods=['POST'])
def parse_resume_ajax():
    if 'user_id' not in session:
        return {'error': 'Unauthorized'}, 401
    
    if 'cv' not in request.files:
        return {'error': 'No file'}, 400
        
    file = request.files['cv']
    if file.filename == '' or not allowed_file(file.filename):
        return {'error': 'Invalid file type'}, 400
        
    try:
        from utils.ai_tools import ResumeParser
        filename = secure_filename(f"temp_{session['user_id']}_{file.filename}")
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        parsed_data = ResumeParser.auto_extract_profile(temp_path)
        
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        if parsed_data:
            return parsed_data
        return {'error': 'Could not parse resume'}, 500
    except Exception as e:
        return {'error': str(e)}, 500

@seeker_bp.route('/uploads/<filename>')
def download_cv(filename):
    if 'user_id' not in session:
        flash("Please log in to view documentation.", "error")
        return redirect(url_for('auth.login'))
    
    try:
        upload_folder = current_app.config['UPLOAD_FOLDER']
        file_path = os.path.join(upload_folder, filename)
        
        if not os.path.exists(file_path):
            current_app.logger.error(f"File not found: {file_path}")
            flash("The requested documentation could not be found on the server.", "error")
            return redirect(request.referrer or url_for('index'))

        # Serve the file
        response = send_from_directory(upload_folder, filename, as_attachment=False)
        
        # Enforce inline viewing for PDFs
        if filename.lower().endswith('.pdf'):
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = 'inline'
        elif filename.lower().endswith(('.doc', '.docx')):
            # Note: Browser support for inline DOCX varies; usually downloads.
            response.headers['Content-Type'] = 'application/msword'
            response.headers['Content-Disposition'] = 'inline'
            
        return response
    except Exception as e:
        current_app.logger.error(f"CV View Error: {str(e)}")
        flash("An error occurred while trying to view the CV.", "error")
        return redirect(request.referrer or url_for('index'))
