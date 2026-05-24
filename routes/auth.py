from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from models.schema import db, User, Profile, Company

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['role'] = user.role
                session['name'] = user.name
                flash('Logged in successfully!', 'success')
                if user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif user.role == 'employer':
                    return redirect(url_for('employer.employer_dashboard'))
                else:
                    return redirect(url_for('seeker.seeker_dashboard'))
            else:
                flash('Invalid email or password', 'error')
        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')
            
    return render_template('login.html')

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        
        if role not in ['seeker', 'employer']:
            flash('Invalid role selected', 'error')
            return redirect(url_for('auth.signup'))
            
        try:
            if User.query.filter_by(email=email).first():
                flash('Email already registered. Please login.', 'error')
                return redirect(url_for('auth.signup'))
                
            hashed_password = generate_password_hash(password)
            new_user = User(name=name, email=email, password=hashed_password, role=role)
            db.session.add(new_user)
            db.session.flush() # To get the new user.id
            
            if role == 'employer':
                new_company = Company(user_id=new_user.id, company_name='', description='')
                db.session.add(new_company)
            else:
                new_profile = Profile(user_id=new_user.id, skills='', experience='')
                db.session.add(new_profile)
                
            db.session.commit()
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Signup error: {str(e)}', 'error')
            
    return render_template('signup.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))
