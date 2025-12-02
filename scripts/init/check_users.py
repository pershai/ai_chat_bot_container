from src.core.database import SessionLocal
from src.models.user import User

def check_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  ID: {user.id}, Username: {user.username}")
    finally:
        db.close()

if __name__ == "__main__":
    check_users()
