import asyncio

from src.core.database import SessionLocal
from src.models.user import User
from src.services.chat_service import process_chat


async def test_chat():
    db = SessionLocal()
    try:
        # Get the test user
        user = db.query(User).filter(User.username == "test_script_user").first()
        if not user:
            print("❌ User not found")
            return

        print(f"Testing chat for user: {user.username} (ID: {user.id})")

        # Test message
        message = "What does the PDF contain?"
        print(f"Sending message: {message}")

        response = await process_chat(message, user.id)
        print(f"✅ Response: {response}")

    except Exception as e:
        print(f"❌ Chat failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_chat())
