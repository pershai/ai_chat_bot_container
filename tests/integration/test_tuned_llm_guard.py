import asyncio
from src.core.database import SessionLocal
from src.services.chat_service import process_chat
from src.models.user import User

async def test_tuned_llm_guard():
    db = SessionLocal()
    try:
        # Get the test user
        user = db.query(User).filter(User.username == "test_script_user").first()
        if not user:
            print("❌ User not found")
            return

        print(f"Testing LLM Guard with tuned settings for user: {user.username} (ID: {user.id})")
        
        # Test messages that previously failed
        test_messages = [
            "Tell me about Gemini from the document",
            "What does the PDF contain?",
            "Hello, can you help me?",
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n{'='*60}")
            print(f"Test {i}: {message}")
            print(f"{'='*60}")
            
            try:
                response = await process_chat(message, user.id)
                print(f"✅ Response: {response[:200]}...")
            except Exception as e:
                print(f"❌ Failed: {e}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_tuned_llm_guard())
