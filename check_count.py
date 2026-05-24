from models.schema import Job
from app import app
with app.app_context():
    count = Job.query.count()
    print(f"Total jobs in DB: {count}")
