from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('seeker', 'employer', 'admin', name='role_enum'), nullable=False)
    
    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")
    companies = db.relationship('Company', backref='owner', cascade="all, delete-orphan")
    applications = db.relationship('Application', backref='applicant', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', cascade="all, delete-orphan")
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', cascade="all, delete-orphan")
    messages_received = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', cascade="all, delete-orphan")

class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    skills = db.Column(db.Text)
    experience = db.Column(db.Text)
    education = db.Column(db.Text)
    bio = db.Column(db.Text)
    phone = db.Column(db.String(20))
    linkedin_url = db.Column(db.String(255))
    portfolio_url = db.Column(db.String(255))
    current_location = db.Column(db.String(150))
    expected_salary = db.Column(db.String(100))
    notice_period = db.Column(db.String(100))
    total_exp = db.Column(db.String(50))
    contact_email = db.Column(db.String(100))
    headline = db.Column(db.String(255), default='Professional Job Seeker')
    profile_pic = db.Column(db.String(255), default='default_avatar.png')

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    
    jobs = db.relationship('Job', backref='company', cascade="all, delete-orphan")

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    salary = db.Column(db.Numeric(10, 2))
    location = db.Column(db.String(100))
    category = db.Column(db.String(100), default='Other')
    job_type = db.Column(db.Enum('full-time', 'part-time', 'remote', name='jobtype_enum'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    applications = db.relationship('Application', backref='job', cascade="all, delete-orphan")

class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    cv_path = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    education = db.Column(db.Text)
    skills = db.Column(db.Text)
    experience = db.Column(db.Text)
    linkedin_url = db.Column(db.String(255))
    portfolio_url = db.Column(db.String(255))
    current_location = db.Column(db.String(150))
    expected_salary = db.Column(db.String(100))
    notice_period = db.Column(db.String(100))
    total_exp = db.Column(db.String(50))
    contact_email = db.Column(db.String(100))
    status = db.Column(db.Enum('Applied', 'Under Review', 'Interview', 'Shortlisted', 'Rejected', name='status_enum'), default='Applied')
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    status_updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    action_url = db.Column(db.String(255), nullable=True) # URL for the notification action
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=True) # Linked job context
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
