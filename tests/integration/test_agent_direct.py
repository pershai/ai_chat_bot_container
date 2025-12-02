import asyncio

from langchain_core.messages import HumanMessage

from src.agent import app_graph
from src.core.database import SessionLocal
from src.models.user import User


async def test_agent_directly():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "test_script_user").first()
        if not user:
            print("❌ User not found")
            return

        print(f"Testing agent directly for user: {user.username} (ID: {user.id})")

        # Call agent directly
        inputs = {
            "messages": [HumanMessage(content="What does the document say?")],
            "user_id": user.id,
        }

        print(f"\nCalling app_graph with inputs: {inputs}")
        result = app_graph.invoke(inputs)

        print(f"\nResult keys: {result.keys()}")
        print(f"Messages count: {len(result['messages'])}")

        for i, msg in enumerate(result["messages"]):
            print(f"\nMessage {i + 1}:")
            print(f"  Type: {type(msg).__name__}")
            print(
                f"  Content: {msg.content[:200] if len(str(msg.content)) > 200 else msg.content}"
            )
            if hasattr(msg, "tool_calls"):
                print(f"  Tool calls: {msg.tool_calls}")

    except Exception as e:
        print(f"❌ Failed: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_agent_directly())
