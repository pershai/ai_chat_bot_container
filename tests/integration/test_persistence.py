import requests

BASE_URL = "http://127.0.0.1:8000"


def test_chat_persistence():
    print("🚀 Testing Chat Persistence...")

    # 0. Register (just in case)
    print("\n0. Registering...")
    requests.post(
        f"{BASE_URL}/auth/register",
        json={"username": "persist_user", "password": "password123"},
    )

    # 1. Login
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "persist_user", "password": "password123"},
    )
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Logged in successfully")

    # 2. Create Conversation
    print("\n2. Creating Conversation...")
    conv_response = requests.post(
        f"{BASE_URL}/conversations/",
        json={"title": "Test Persistence"},
        headers=headers,
    )
    if conv_response.status_code != 200:
        print(f"❌ Create conversation failed: {conv_response.text}")
        return
    conversation_id = conv_response.json()["id"]
    print(f"✅ Created conversation ID: {conversation_id}")

    # 3. Send Message 1
    print("\n3. Sending Message 1 (Context Setting)...")
    msg1 = "My favorite color is blue."
    chat_response1 = requests.post(
        f"{BASE_URL}/chat",
        json={"message": msg1, "conversation_id": conversation_id},
        headers=headers,
    )
    if chat_response1.status_code != 200:
        print(f"❌ Chat 1 failed: {chat_response1.text}")
        return
    print(f"✅ Chat 1 Response: {chat_response1.json()['response']}")

    # 4. Send Message 2 (Context Retrieval)
    print("\n4. Sending Message 2 (Context Retrieval)...")
    msg2 = "What is my favorite color?"
    chat_response2 = requests.post(
        f"{BASE_URL}/chat",
        json={"message": msg2, "conversation_id": conversation_id},
        headers=headers,
    )
    if chat_response2.status_code != 200:
        print(f"❌ Chat 2 failed: {chat_response2.text}")
        return
    response_text = chat_response2.json()["response"]
    print(f"✅ Chat 2 Response: {response_text}")

    if "blue" in response_text.lower():
        print("🎉 SUCCESS: Context was preserved!")
    else:
        print("⚠️ WARNING: Context might not have been preserved.")

    # 5. Verify DB Persistence
    print("\n5. Verifying DB Persistence...")
    history_response = requests.get(
        f"{BASE_URL}/conversations/{conversation_id}", headers=headers
    )
    if history_response.status_code == 200:
        messages = history_response.json()["messages"]
        print(f"✅ Found {len(messages)} messages in history")
        for msg in messages:
            print(f"   - [{msg['role']}]: {msg['content'][:50]}...")
    else:
        print(f"❌ Failed to fetch history: {history_response.text}")


if __name__ == "__main__":
    test_chat_persistence()
