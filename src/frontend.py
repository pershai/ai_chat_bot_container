import streamlit as st
import requests
import os

# Configuration
API_URL = os.getenv("API_URL")

st.set_page_config(page_title="AI Chat Bot", page_icon="🤖")

# Auth Configuration
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "access_token" not in st.session_state:
    st.session_state.access_token = None

def login():
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"username": st.session_state.username, "password": st.session_state.password}
        )
        if response.status_code == 200:
            token_data = response.json()
            st.session_state.access_token = token_data["access_token"]
            st.session_state.authenticated = True
            st.success("Logged in!")
            st.rerun()
        else:
            st.error("😕 Incorrect username or password")
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")

def register():
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={"username": st.session_state.reg_username, "password": st.session_state.reg_password}
        )
        if response.status_code == 200:
            st.success("Registered successfully! Please login.")
        else:
            st.error(f"Registration failed: {response.json().get('detail')}")
    except Exception as e:
        st.error(f"Connection Error: {str(e)}")

if not st.session_state.authenticated:
    st.title("🔐 Login / Register")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=login)
        
    with tab2:
        st.text_input("New Username", key="reg_username")
        st.text_input("New Password", type="password", key="reg_password")
        st.button("Register", on_click=register)
        
    st.stop()

st.title("🤖 AI Chat Bot")

# Sidebar for file upload and conversations
with st.sidebar:
    st.header("📚 Knowledge Base")
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Upload"):
            with st.spinner("Uploading and ingesting..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
                    response = requests.post(f"{API_URL}/upload", files=files, headers=headers)
                    if response.status_code == 200:
                        st.success(response.json().get("message", "Uploaded successfully!"))
                    else:
                        st.error(f"Upload failed: {response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    st.divider()
    
    # Conversation History
    st.header("💬 History")
    
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.current_conversation_id = None
        st.session_state.messages = []
        st.rerun()
    
    # Load conversations
    if st.session_state.authenticated:
        try:
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            response = requests.get(f"{API_URL}/conversations/", headers=headers)
            if response.status_code == 200:
                conversations = response.json()
                for conv in conversations:
                    if st.button(f"📝 {conv['title']}", key=f"conv_{conv['id']}", use_container_width=True):
                        st.session_state.current_conversation_id = conv['id']
                        # Load messages for this conversation
                        msg_response = requests.get(f"{API_URL}/conversations/{conv['id']}", headers=headers)
                        if msg_response.status_code == 200:
                            data = msg_response.json()
                            st.session_state.messages = data.get("messages", [])
                        st.rerun()
        except Exception as e:
            st.error(f"Failed to load history: {e}")

# Chat Interface
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is your question?"):
    # Create conversation if it doesn't exist
    if not st.session_state.current_conversation_id:
        try:
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            # Use first 30 chars of prompt as title
            title = prompt[:30] + "..." if len(prompt) > 30 else prompt
            conv_response = requests.post(
                f"{API_URL}/conversations/",
                json={"title": title},
                headers=headers
            )
            if conv_response.status_code == 200:
                st.session_state.current_conversation_id = conv_response.json()["id"]
            else:
                st.error("Failed to create conversation")
        except Exception as e:
            st.error(f"Error creating conversation: {e}")

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
                payload = {"message": prompt}
                if st.session_state.current_conversation_id:
                    payload["conversation_id"] = st.session_state.current_conversation_id
                
                response = requests.post(
                    f"{API_URL}/chat",
                    json=payload,
                    headers=headers
                )
                if response.status_code == 200:
                    answer = response.json().get("response", "No response received.")
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    error_msg = f"Error: {response.status_code} - {response.text}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"Connection Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
