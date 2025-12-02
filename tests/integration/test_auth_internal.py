from src.core.database import SessionLocal
from src.services.auth_service import create_user, authenticate_user
from src.schemas.user import UserCreate

def test_auth():
    db = SessionLocal()
    try:
        # 1. Create User
        print("Creating user...")
        user_in = UserCreate(username="test_script_user", password="password123")
        try:
            user = create_user(db, user_in)
            print(f"User created: {user.username}")
        except Exception as e:
            print(f"User creation failed (might already exist): {e}")

        # 2. Authenticate
        print("Authenticating...")
        user = authenticate_user(db, "test_script_user", "password123")
        if user:
            print("✅ Authentication successful!")
        else:
            print("❌ Authentication failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_auth()
