from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from models.schema import db, User, Company, Job, Application, Notification, Profile
import pandas as pd
from flask_mail import Message

employer_bp = Blueprint('employer', __name__, url_prefix='/employer')

def is_employer():
    return session.get('role') == 'employer'

@employer_bp.route('/dashboard')
def employer_dashboard():
    if not is_employer():
        return redirect(url_for('auth.login'))
        
    try:
        company = Company.query.filter_by(user_id=session['user_id']).first()
        
        if not company or not company.company_name:
            flash('Please complete your company profile first.', 'warning')
            return redirect(url_for('employer.employer_profile'))
            
        jobs = Job.query.filter_by(company_id=company.id).order_by(Job.created_at.desc()).all()
        
        # In SQLAlchemy, we can just access job.applications or count them
        formatted_jobs = []
        for job in jobs:
            formatted_jobs.append({
                'id': job.id,
                'title': job.title,
                'location': job.location,
                'salary': job.salary,
                'job_type': job.job_type,
                'category': job.category,
                'created_at': job.created_at,
                'applicant_count': Application.query.filter_by(job_id=job.id).count()
            })
            
        return render_template('employer/dashboard.html', jobs=formatted_jobs, company=company)
    except Exception as e:
        flash(f"Dashboard error: {str(e)}", "error")
        return redirect(url_for('index'))

@employer_bp.route('/profile', methods=['GET', 'POST'])
def employer_profile():
    if not is_employer():
        return redirect(url_for('auth.login'))
        
    try:
        company = Company.query.filter_by(user_id=session['user_id']).first()
        if request.method == 'POST':
            company.company_name = request.form.get('company_name')
            company.description = request.form.get('description')
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('employer.employer_dashboard'))
            
        return render_template('employer/profile.html', company=company)
    except Exception as e:
        db.session.rollback()
        flash(f"Profile error: {str(e)}", "error")
        return redirect(url_for('employer.employer_dashboard'))

@employer_bp.route('/job/new', methods=['GET', 'POST'])
def post_job():
    if not is_employer():
        return redirect(url_for('auth.login'))
        
    try:
        company = Company.query.filter_by(user_id=session['user_id']).first()
        
        if not company or not company.company_name:
            flash('Please complete your company profile before posting a job.', 'warning')
            return redirect(url_for('employer.employer_profile'))
            
        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')
            salary = request.form.get('salary')
            location = request.form.get('location')
            job_type = request.form.get('job_type')
            category = request.form.get('category', 'Technology') # Default category
            
            new_job = Job(
                company_id=company.id,
                title=title,
                description=description,
                salary=salary,
                location=location,
                job_type=job_type,
                category=category
            )
            db.session.add(new_job)
            db.session.commit()
            flash('Job posted successfully!', 'success')
            return redirect(url_for('employer.employer_dashboard'))
    except Exception as e:
        db.session.rollback()
        flash(f"Posting error: {str(e)}", "error")
        
    return render_template('employer/job_form.html')

@employer_bp.route('/job/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    if not is_employer():
        return redirect(url_for('auth.login'))
        
    try:
        company = Company.query.filter_by(user_id=session['user_id']).first()
        job = Job.query.filter_by(id=job_id, company_id=company.id).first()
        
        if not job:
            flash('Job not found or unauthorized.', 'error')
            return redirect(url_for('employer.employer_dashboard'))
            
        if request.method == 'POST':
            job.title = request.form.get('title')
            job.description = request.form.get('description')
            job.salary = request.form.get('salary')
            job.location = request.form.get('location')
            job.job_type = request.form.get('job_type')
            job.category = request.form.get('category', job.category)
            
            db.session.commit()
            flash('Job updated successfully!', 'success')
            return redirect(url_for('employer.employer_dashboard'))
            
        return render_template('employer/job_form.html', job=job)
    except Exception as e:
        db.session.rollback()
        flash(f"Edit error: {str(e)}", "error")
        return redirect(url_for('employer.employer_dashboard'))

@employer_bp.route('/job/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    if not is_employer():
        return redirect(url_for('auth.login'))
        
    try:
        company = Company.query.filter_by(user_id=session['user_id']).first()
        job = Job.query.filter_by(id=job_id, company_id=company.id).first()
        if job:
            db.session.delete(job)
            db.session.commit()
            flash('Job deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Deletion error: {str(e)}", "error")
        
    return redirect(url_for('employer.employer_dashboard'))

@employer_bp.route('/job/<int:job_id>/applicants')
def view_applicants(job_id):
    if not is_employer():
        return redirect(url_for('auth.login'))
        
    try:
        company = Company.query.filter_by(user_id=session['user_id']).first()
        job = Job.query.filter_by(id=job_id, company_id=company.id).first()
        
        if not job:
            flash('Job not found or unauthorized.', 'error')
            return redirect(url_for('employer.employer_dashboard'))
            
        # Join Application with User and Profile
        applicants_data = db.session.query(Application, User, Profile)\
            .join(User, Application.user_id == User.id)\
            .join(Profile, User.id == Profile.user_id)\
            .filter(Application.job_id == job_id).all()
            
        formatted_applicants = []
        for app, user, prof in applicants_data:
            formatted_applicants.append({
                'application_id': app.id,
                'cv_path': app.cv_path,
                'status': app.status,
                'applied_at': app.applied_at,
                'user_id': user.id,
                'name': app.full_name or user.name,
                'email': user.email,
                'phone': app.phone,
                'bio': app.bio,
                'education': app.education,
                'skills': app.skills,
                'experience': app.experience,
                'linkedin_url': app.linkedin_url,
                'portfolio_url': app.portfolio_url,
                'current_location': app.current_location,
                'expected_salary': app.expected_salary,
                'notice_period': app.notice_period,
                'total_exp': app.total_exp
            })
            
        return render_template('employer/applicants.html', applicants=formatted_applicants, job=job)
    except Exception as e:
        flash(f"Applicants fetch error: {str(e)}", "error")
        return redirect(url_for('employer.employer_dashboard'))

@employer_bp.route('/application/<int:app_id>/status', methods=['POST'])
def update_status(app_id):
    if not is_employer():
        return redirect(url_for('auth.login'))
        
    status = request.form.get('status')
    if status not in ['Applied', 'Shortlisted', 'Interview', 'Rejected']:
        flash('Invalid status.', 'error')
        return redirect(request.referrer)
        
    try:
        company = Company.query.filter_by(user_id=session['user_id']).first()
        application = Application.query.get(app_id)
        
        if not application or application.job.company_id != company.id:
            flash('Unauthorized or application not found.', 'error')
            return redirect(url_for('employer.employer_dashboard'))
            
        # Update status
        application.status = status
        application.status_updated_at = db.func.now()
        
        # In-App Notification
        notif_msg = f"Your application for '{application.job.title}' has been updated to: {status}"
        new_notif = Notification(user_id=application.user_id, message=notif_msg[:490])
        db.session.add(new_notif)
        
        db.session.commit()
        
        # Email Notification
        try:
            from app import mail
            msg = Message(f"Update on your application for {application.job.title}",
                          recipients=[application.applicant.email])
            msg.body = f"Hi {application.applicant.name},\n\nYour application status for '{application.job.title}' has been updated to: {status}.\n\nLog in to your dashboard to see more details.\n\nBest regards,\nRozgaarSphere Team"
            mail.send(msg)
        except Exception as mail_err:
            print(f"Mail sending failed: {mail_err}")
            
        # Real-time SocketIO Notification
        try:
            from app import socketio
            socketio.emit('notification', {'message': notif_msg}, room=f"user_{application.user_id}")
        except Exception as socket_err:
            print(f"Socket notification failed: {socket_err}")
            
        flash(f'Application {status} successfully and candidate notified.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Status update error: {str(e)}", "error")
        
    return redirect(request.referrer)

@employer_bp.route('/jobs/toggle/<int:job_id>', methods=['POST'])
def toggle_job_status(job_id):
    if not is_employer():
        return redirect(url_for('auth.login'))
        
    try:
        company = Company.query.filter_by(user_id=session['user_id']).first()
        job = Job.query.get(job_id)
        
        if not job or job.company_id != company.id:
            flash('Unauthorized or job not found.', 'error')
            return redirect(url_for('employer.employer_dashboard'))
            
        job.is_active = not job.is_active
        db.session.commit()
        
        status_text = "Reopened" if job.is_active else "Closed"
        flash(f'Job "{job.title}" has been {status_text}.', "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error toggling job status: {str(e)}", "error")
        
    return redirect(url_for('employer.employer_dashboard'))

@employer_bp.route('/analytics')
def analytics():
    if not is_employer():
        return redirect(url_for('auth.login'))
        
    try:
        company = Company.query.filter_by(user_id=session['user_id']).first()
        jobs = Job.query.filter_by(company_id=company.id).all()
        
        if not jobs:
            return render_template('employer/analytics.html', no_data=True)
            
        # Gather data for Pandas
        jobs_list = []
        for j in jobs:
            jobs_list.append({
                'id': j.id,
                'title': j.title,
                'location': j.location,
                'category': j.category
            })
        
        # Gather applications for jobs owned by this company
        job_ids = [j.id for j in jobs]
        apps = Application.query.filter(Application.job_id.in_(job_ids)).all()
        
        if not apps:
            return render_template('employer/analytics.html', no_data=True)
            
        apps_list = []
        for a in apps:
            profile = Profile.query.filter_by(user_id=a.user_id).first()
            apps_list.append({
                'id_app': a.id,
                'job_id': a.job_id,
                'status': a.status,
                'skills': profile.skills if profile else ''
            })
            
        df_jobs = pd.DataFrame(jobs_list)
        df_apps = pd.DataFrame(apps_list)
        
        # Analysis
        # 1. Job Distribution (Locations where jobs are posted)
        job_location_dist = df_jobs['location'].value_counts().to_dict()
        
        # 2. Candidate Reach (Where candidates actually live)
        # Re-fetch apps with locations (already done in apps_list if we update it)
        apps_list = []
        for a in apps:
            apps_list.append({
                'id_app': a.id,
                'job_id': a.job_id,
                'status': a.status,
                'candidate_location': a.current_location or 'Unknown'
            })
        df_apps = pd.DataFrame(apps_list)
        df_merged = pd.merge(df_apps, df_jobs, left_on='job_id', right_on='id')
        
        apps_per_job = df_merged.groupby('title')['id_app'].count().to_dict()
        status_distribution = df_apps['status'].value_counts().to_dict()
        
        popular_job_title = "None"
        if not df_merged.empty:
            popular_job_title = df_merged['title'].value_counts().idxmax()
            
        # Skills Analysis
        skills_list = []
        for a in apps:
            if a.skills:
                skills = [s.strip().title() for s in str(a.skills).split(',') if s.strip()]
                skills_list.extend(skills)
            
        top_skills = {}
        if skills_list:
            top_skills = pd.Series(skills_list).value_counts().head(5).to_dict()
            
        candidate_location_dist = df_apps['candidate_location'].value_counts().to_dict()
        total_applicants = len(apps)
        
        return render_template('employer/analytics.html', 
                               apps_per_job=apps_per_job, 
                               popular_job_title=popular_job_title,
                               top_skills=top_skills,
                               status_distribution=status_distribution,
                               job_location_dist=job_location_dist,
                               candidate_location_dist=candidate_location_dist,
                               total_applicants=total_applicants)
    except Exception as e:
        flash(f"Analytics error: {str(e)}", "error")
        return render_template('employer/analytics.html', no_data=True)
