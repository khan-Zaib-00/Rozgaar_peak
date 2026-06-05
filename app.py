import os
from flask import Flask, render_template, session, g, request, redirect, url_for
from flask_mail import Mail
from flask_socketio import SocketIO, emit, join_room
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

from models.db import init_db, get_db_connection
from routes.auth import auth_bp
from routes.seeker import seeker_bp
from routes.employer import employer_bp
from routes.jobs import jobs_bp
from routes.admin import admin_bp
from routes.messages import messages_bp
from models.schema import db

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_v2')

# Flask-WTF CSRF Protection
csrf = CSRFProtect(app)

# Flask-Mail Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.mailtrap.io')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 2525))
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@rozgaarsphere.com')

mail = Mail(app)
if 'PYTHONANYWHERE_DOMAIN' in os.environ:
    # PythonAnywhere does NOT support WebSockets - must disable upgrades and use polling only
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', allow_upgrades=False, transports=['polling'])
else:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'job_portal.db'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

app.register_blueprint(auth_bp)
app.register_blueprint(seeker_bp)
app.register_blueprint(employer_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(messages_bp)

@app.errorhandler(Exception)
def handle_generic_error(e):
    app.logger.error(f"Unhandled exception: {e}")
    if 'sqlite' in str(type(e)).lower() or 'database' in str(e).lower():
        return render_template('error.html', message="Database connection failed."), 500
    # Don't re-raise — return a safe error page instead of crashing the WSGI worker
    return render_template('error.html', message="An unexpected error occurred. Please try again."), 500

from models.schema import db, Job, Profile, Company
from flask import g

@app.before_request
def load_user_profile():
    # Load profile info for sidebar
    if 'user_id' in session:
        try:
            if session.get('role') == 'seeker':
                profile = Profile.query.filter_by(user_id=session['user_id']).first()
                if profile:
                    session['headline'] = profile.headline or 'Professional Job Seeker'
                    session['profile_pic'] = profile.profile_pic or 'default_avatar.png'
            elif session.get('role') == 'employer':
                company = Company.query.filter_by(user_id=session['user_id']).first()
                if company:
                    session['headline'] = f"Founder at {company.company_name or 'Tech Hub'}"
                    session['profile_pic'] = 'default_avatar.png'
        except Exception as e:
            app.logger.error(f"Error loading user profile: {e}")
    
    # Load hiring trends for right sidebar using SQLAlchemy
    try:
        from sqlalchemy import func
        # Locations
        loc_res = db.session.query(Job.location, func.count(Job.id).label('count')).group_by(Job.location).order_by(func.count(Job.id).desc()).limit(5).all()
        g.top_locations = [{'location': r[0], 'count': r[1]} for r in loc_res]
        
        # Categories
        cat_res = db.session.query(Job.category, func.count(Job.id).label('count')).group_by(Job.category).order_by(func.count(Job.id).desc()).limit(5).all()
        g.top_categories = [{'category': r[0], 'count': r[1]} for r in cat_res]
    except Exception as e:
        app.logger.error(f"Error loading hiring trends: {e}")
        g.top_locations = []
        g.top_categories = []

@app.context_processor
def inject_notifications():
    if 'user_id' in session:
        try:
            from models.schema import Notification
            # Get recent 5 notifications
            notifications = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.created_at.desc()).limit(5).all()
            # Count unread
            unread_count = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
            return dict(notifications=notifications, unread_count=unread_count)
        except Exception as e:
            app.logger.error(f"Notification injection error: {e}")
            return dict(notifications=[], unread_count=0)
    return dict(notifications=[], unread_count=0)

@app.route('/')
def index():
    # AUTO-LOGIN and Redirection disabled to show the landing page first
    # Auto-login removed to allow switching between Seeker, Employer and Admin roles.
    
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(10).all()
    # If already logged in, redirecting disabled to allow viewing landing page
    # if 'user_id' in session:
    #     if session['role'] == 'admin':
    #         return redirect(url_for('admin.dashboard'))
    #     elif session['role'] == 'employer':
    #         return redirect(url_for('employer.employer_dashboard'))
    #     else:
    #         return redirect(url_for('seeker.seeker_dashboard'))
            
    return render_template('index.html', jobs=recent_jobs)

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        join_room(f"user_{session['user_id']}")
        print(f"User {session['user_id']} connected and joined room user_{session['user_id']}")

@socketio.on('join')
def on_join(data):
    if 'user_id' in session:
        join_room(f"user_{session['user_id']}")

@socketio.on('send_msg')
def handle_message(data):
    if 'user_id' not in session:
        return
    
    receiver_id = data.get('receiver_id')
    job_id = data.get('job_id')
    content = data.get('content')
    
    if receiver_id and content:
        try:
            from models.schema import Message, Notification
            new_msg = Message(sender_id=session['user_id'], receiver_id=receiver_id, job_id=job_id, content=content)
            db.session.add(new_msg)
            
            # Real-time alert to receiver
            notif_msg = f"New message from {session['name']}: {content[:30]}..."
            action_url = url_for('messages.inbox', user_id=session['user_id'], job_id=job_id)
            new_notif = Notification(user_id=receiver_id, message=notif_msg, action_url=action_url)
            db.session.add(new_notif)
            db.session.commit()
            
            # Emit message to both sender and receiver rooms
            msg_data = {
                'sender_id': session['user_id'],
                'sender_name': session['name'],
                'content': content,
                'job_id': job_id,
                'created_at': 'Just now'
            }
            emit('new_msg', msg_data, room=f"user_{receiver_id}")
            emit('new_msg', msg_data, room=f"user_{session['user_id']}")
            
            # Also emit a general notification for the header
            emit('notification', {
                'message': f"New message from {session['name']}",
                'action_url': action_url
            }, room=f"user_{receiver_id}")
            
        except Exception as e:
            print(f"Message socket error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Warning: Database initialization failed. Error: {e}")
        
    # Initialize everything and run with socketio
    socketio.run(app, debug=True, port=5001)
