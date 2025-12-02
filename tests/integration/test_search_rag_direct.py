import asyncio
from src.core.database import SessionLocal
from src.models.user import User
from src.tools import search_rag


async def test_search_rag_directly():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "test_script_user").first()
        if not user:
            print("❌ User not found")
            return

        print(f"Testing search_rag for user: {user.username} (ID: {user.id})")

        # Test with state
        state = {"user_id": user.id}
        result = search_rag.invoke({"query": "Hello Gemini", "state": state})
        print(f"✅ Result: {result}")

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_search_rag_directly())
