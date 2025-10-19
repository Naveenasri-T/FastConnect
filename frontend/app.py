# FastConnect - Modern Chat UI
import os
import json
import streamlit as st
from dotenv import load_dotenv
from websocket import create_connection, WebSocketException
from datetime import datetime
import time

# Load environment variables
load_dotenv()
BACKEND_WS = os.getenv("BACKEND_WS_URL", "ws://localhost:8000/ws")

# Page configuration
st.set_page_config(
    page_title="FastConnect - AI Chat", 
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .chat-message:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }
    .user-message {
        background-color: #e3f2fd;
        border-left-color: #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left-color: #9c27b0;
    }
    .error-message {
        background-color: #ffebee;
        border-left-color: #f44336;
    }
    /* Highlight the newest message */
    .chat-message:first-of-type {
        border: 2px solid #4caf50;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
    }
    .status-box {
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .success { background-color: #e8f5e8; color: #2e7d32; }
    .error { background-color: #ffebee; color: #c62828; }
    .info { background-color: #e3f2fd; color: #1565c0; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False

# Header
st.markdown("""
<div class="main-header">
    <h1>🚀 FastConnect AI Chat</h1>
    <p>Powered by Groq LLM via WebSocket</p>
</div>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Connection status
    st.subheader("🔗 Connection Status")
    
    # Test backend connection
    @st.cache_data(ttl=5)  # Cache result for 5 seconds
    def test_backend_connection():
        try:
            # Try HTTP health check first (more reliable)
            import urllib.request
            health_url = BACKEND_WS.replace("ws://", "http://").replace("/ws", "/health")
            with urllib.request.urlopen(health_url, timeout=3) as response:
                if response.getcode() == 200:
                    return True, "HTTP OK"
        except:
            pass
        
        # Fallback to WebSocket test
        try:
            test_ws = create_connection(BACKEND_WS, timeout=5)
            test_ws.close()
            return True, "WebSocket OK"
        except Exception as e:
            return False, str(e)
    
    connection_ok, connection_msg = test_backend_connection()
    
    if connection_ok:
        st.markdown('<div class="status-box success">✅ Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-box error">❌ Disconnected</div>', unsafe_allow_html=True)
        with st.expander("🔍 Connection Details"):
            st.error(f"Error: {connection_msg}")
            st.info(f"Backend URL: {BACKEND_WS}")
    
    st.markdown("---")

    st.subheader("💬 Chat Options")
    max_messages = st.slider("Max messages to show", 5, 50, 20)
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    # Info section
    st.subheader("ℹ️ About")
    st.info("""
    **FastConnect** uses:
    - 🔗 WebSocket for real-time communication
    - 🤖 Groq API for AI responses
    - ⚡ FastAPI backend
    - 🎨 Streamlit frontend
    """)

def send_message_to_backend(prompt_text):
    """Send message via WebSocket and return complete response"""
    try:
        ws = create_connection(BACKEND_WS, timeout=10)
        ws.send(json.dumps({"type": "prompt", "prompt": prompt_text}))
        
        complete_response = ""
        response_placeholder = st.empty()
        
        while True:
            raw = ws.recv()
            if raw is None:
                break
                
            try:
                data = json.loads(raw)
                if data.get("type") == "delta":
                    complete_response += data.get("text", "")
                    # Show streaming response
                    response_placeholder.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>🤖 Assistant:</strong><br>
                        {complete_response}
                    </div>
                    """, unsafe_allow_html=True)
                elif data.get("type") == "done":
                    break
                elif data.get("type") == "error":
                    complete_response = f"❌ Error: {data.get('message', 'Unknown error')}"
                    break
            except Exception:
                continue
                
        ws.close()
        response_placeholder.empty()  # Clear the streaming placeholder
        return complete_response
        
    except WebSocketException as e:
        return f"❌ WebSocket Error: {str(e)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Main chat interface
col1, col2 = st.columns([3, 1])

with col1:
    # Message input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "💬 Type your message here:", 
            height=100,
            placeholder="Ask me anything! e.g., 'Explain Python basics' or 'Help me with JavaScript'"
        )
        
        col_send, col_example = st.columns([1, 2])
        with col_send:
            send_button = st.form_submit_button("🚀 Send", use_container_width=True)
        with col_example:
            if st.form_submit_button("💡 Try Example: 'Explain machine learning'", use_container_width=True):
                user_input = "Explain machine learning concepts in simple terms"
                send_button = True

with col2:
    st.metric("💬 Total Messages", len(st.session_state.messages))
    if connection_ok:
        st.success("🟢 Ready to chat!")
    else:
        st.error("🔴 Connection issue")

# Handle message sending
if send_button and user_input.strip():
    if not connection_ok:
        st.error("❌ Cannot send message: No connection to backend")
    else:
        # Add user message
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input.strip(),
            "timestamp": timestamp
        })
        
        # Get AI response
        with st.spinner("🤖 AI is thinking..."):
            response = send_message_to_backend(user_input.strip())
            
        # Add assistant message
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        # Auto-scroll to top (where newest message will appear)
        st.markdown("""
        <script>
            window.scrollTo({top: 0, behavior: 'smooth'});
        </script>
        """, unsafe_allow_html=True)
        
        st.rerun()

# Display chat messages
col_title, col_scroll = st.columns([3, 1])
with col_title:
    st.subheader("💬 Chat History")
with col_scroll:
    if len(st.session_state.messages) > 0:
        if st.button("� Refresh", help="Refresh chat display", key="refresh_chat"):
            st.rerun()

# Show latest conversation snippet at the top for easy access
if st.session_state.messages and len(st.session_state.messages) >= 2:
    latest_user = st.session_state.messages[-2] if st.session_state.messages[-2]["role"] == "user" else None
    latest_assistant = st.session_state.messages[-1] if st.session_state.messages[-1]["role"] == "assistant" else None
    
    if latest_user and latest_assistant:
        with st.container():
            st.markdown("### 🆕 Latest Conversation")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown(f"""
                <div style="background: #e8f5e8; padding: 1rem; border-radius: 8px; border-left: 4px solid #4caf50;">
                    <strong>👤 Your Last Question:</strong><br>
                    <em>"{latest_user['content'][:100]}{'...' if len(latest_user['content']) > 100 else ''}"</em>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background: #fff3e0; padding: 1rem; border-radius: 8px; border-left: 4px solid #ff9800;">
                    <strong>🤖 Latest Response:</strong><br>
                    <em>"{latest_assistant['content'][:100]}{'...' if len(latest_assistant['content']) > 100 else ''}"</em>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")

if st.session_state.messages:
    # Show only the last N messages IN REVERSE ORDER (newest first)
    recent_messages = st.session_state.messages[-max_messages:]
    
    # Display messages in reverse order (newest at top)
    for i, message in enumerate(reversed(recent_messages)):
        message_key = f"msg_{len(recent_messages) - i - 1}"
        
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message" id="{message_key}">
                <strong>👤 You</strong> <small>({message.get('timestamp', '')})</small><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message" id="{message_key}">
                <strong>🤖 Assistant</strong> <small>({message.get('timestamp', '')})</small><br>
                {message['content']}
            </div>
            """, unsafe_allow_html=True)
    
    # Show message count info at bottom
    info_col1, info_col2 = st.columns([2, 1])
    with info_col1:
        if len(st.session_state.messages) > max_messages:
            st.info(f"📊 Showing {max_messages} most recent messages (out of {len(st.session_state.messages)} total)")
        else:
            st.success(f"📊 Showing all {len(st.session_state.messages)} messages")
    
    with info_col2:
        st.markdown("**💡 Tip:** Newest messages appear at the top!")
else:
    st.markdown("""
    <div style="text-align: center; padding: 3rem; color: #666;">
        <h3>👋 Welcome to FastConnect!</h3>
        <p>Start a conversation by typing a message above and clicking Send.</p>
        <p><strong>Try asking:</strong></p>
        <ul style="text-align: left; max-width: 400px; margin: 0 auto;">
            <li>💻 "Explain Python programming"</li>
            <li>🔬 "What is machine learning?"</li>
            <li>🌐 "How do web applications work?"</li>
            <li>🤖 "Tell me about AI"</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
