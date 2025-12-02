import asyncio

from src.core.database import SessionLocal
from src.models.user import User
from src.services.chat_service import process_chat


async def test_chat_debug():
    db = SessionLocal()
    try:
        # Get the test user
        user = db.query(User).filter(User.username == "test_script_user").first()
        if not user:
            print("❌ User not found")
            return

        print(f"Testing chat for user: {user.username} (ID: {user.id})")

        # Test message
        message = "What does the document say?"
        print(f"Sending message: {message}")

        # Add debug to agent
        import src.agent as agent_module

        original_call_tools = agent_module.call_tools

        def debug_call_tools(state):
            print(f"\n[DEBUG] call_tools called with state: {state.keys()}")
            print(f"[DEBUG] user_id in state: {state.get('user_id')}")
            result = original_call_tools(state)
            print(f"[DEBUG] tool results: {result}")
            return result

        agent_module.call_tools = debug_call_tools

        response = await process_chat(message, user.id)
        print(f"\n✅ Response: {response}")

    except Exception as e:
        print(f"❌ Chat failed: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_chat_debug())
