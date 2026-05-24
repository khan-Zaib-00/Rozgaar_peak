from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from models.schema import db, User, Job, Company, Application
from utils.decorators import admin_required
from flask import session
import csv
from io import StringIO

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def dashboard():
    stats = {
        'total_users': User.query.count(),
        'total_jobs': Job.query.count(),
        'total_companies': Company.query.count(),
        'total_applications': Application.query.count()
    }
    
    recent_users = User.query.order_by(User.id.desc()).limit(5).all()
    recent_jobs = Job.query.order_by(Job.id.desc()).limit(5).all()
    recent_apps = Application.query.order_by(Application.id.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                           stats=stats, 
                           recent_users=recent_users, 
                           recent_jobs=recent_jobs, 
                           recent_apps=recent_apps)

@admin_bp.route('/users')
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == session.get('user_id'):
        flash("You cannot delete your own admin account!", "error")
        return redirect(url_for('admin.manage_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.name} has been deleted.", "success")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/jobs')
@admin_required
def manage_jobs():
    jobs = Job.query.all()
    return render_template('admin/jobs.html', jobs=jobs)

@admin_bp.route('/jobs/delete/<int:job_id>', methods=['POST'])
@admin_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash(f"Job '{job.title}' deleted successfully.", "success")
    return redirect(url_for('admin.manage_jobs'))

@admin_bp.route('/applications')
@admin_required
def manage_applications():
    applications = Application.query.order_by(Application.applied_at.desc()).all()
    return render_template('admin/applications.html', applications=applications)

@admin_bp.route('/jobs/edit/<int:job_id>', methods=['GET', 'POST'])
@admin_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    if request.method == 'POST':
        job.title = request.form.get('title')
        job.description = request.form.get('description')
        job.salary = request.form.get('salary')
        job.location = request.form.get('location')
        job.category = request.form.get('category')
        job.job_type = request.form.get('job_type')
        
        db.session.commit()
        flash("Job updated successfully.", "success")
        return redirect(url_for('admin.manage_jobs'))
    
    return render_template('admin/edit_job.html', job=job)

@admin_bp.route('/export/users')
@admin_required
def export_users():
    users = User.query.all()
    def generate():
        data = StringIO()
        writer = csv.writer(data)
        writer.writerow(['ID', 'Name', 'Email', 'Role'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        for user in users:
            writer.writerow([user.id, user.name, user.email, user.role])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
            
    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="users_export.csv")
    return response

@admin_bp.route('/export/jobs')
@admin_required
def export_jobs():
    jobs = Job.query.all()
    def generate():
        data = StringIO()
        writer = csv.writer(data)
        writer.writerow(['ID', 'Title', 'Company', 'Location', 'Type', 'Salary', 'Date Posted'])
        yield data.getvalue()
        data.seek(0)
        data.truncate(0)
        for job in jobs:
            writer.writerow([job.id, job.title, job.company.company_name, job.location, job.job_type, job.salary, job.created_at])
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
            
    response = Response(generate(), mimetype='text/csv')
    response.headers.set("Content-Disposition", "attachment", filename="jobs_export.csv")
    return response
