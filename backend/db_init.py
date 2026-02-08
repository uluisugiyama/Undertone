import os
from backend.app import app, db

def init_db():
    print("Initializing Database...")
    try:
        with app.app_context():
            # Create tables
            db.create_all()
            print("Tables created successfully.")
            
            # Check if any data exists
            from backend.models import User
            user_count = User.query.count()
            print(f"Current User Count: {user_count}")
            
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    init_db()
