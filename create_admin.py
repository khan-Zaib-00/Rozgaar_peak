import os
from app import app
from models.schema import db, User
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        name = "RozgaarSphere Admin"
        email = "admin@rozgaarsphere.com"
        password = "admin123"
        
        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            print(f"User {email} already exists. Updating to admin role...")
            user.role = 'admin'
        else:
            print(f"Creating new admin user: {email}")
            hashed_password = generate_password_hash(password)
            user = User(name=name, email=email, password=hashed_password, role='admin')
            db.session.add(user)
            
        db.session.commit()
        print("---------------------------------")
        print("Admin account ready!")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print("---------------------------------")

if __name__ == "__main__":
    create_admin()
