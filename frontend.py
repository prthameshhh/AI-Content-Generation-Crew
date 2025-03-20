import streamlit as st
import requests
import os
from backend import start_transcription


# FastAPI backend URLs
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
SPEECH_API_URL = f"{BACKEND_URL}/speech-input/"

# Streamlit page configuration
st.set_page_config(page_title="AI Content generation ", layout="wide", page_icon="🤖")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "editing_message_index" not in st.session_state:
    st.session_state.editing_message_index = None

# Sidebar - Expert Selection and Controls
with st.sidebar:
    st.title("AI Content experts")
    session_type = st.selectbox(
        "Choose AI Expert:",
        ["content_strategist", "research_assistant", "technical_writer",
         "editor", "fact_checker", "format_specialist",
         "voice_processing_expert", "quality_assurance_agent"],
        index=2
    )
    
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.editing_message_index = None
        st.rerun()

    st.divider()
    
    if st.button("🎤 Voice Input", use_container_width=True, key="voice_input"):
        with st.spinner("Listening..."):
            try:
                response = requests.get(SPEECH_API_URL)
                if response.status_code == 200:
                    speech_text = response.json().get("text", "")
                    if speech_text:
                        # Add user message and trigger AI response
                        st.session_state.chat_history.append({"role": "user", "content": speech_text})
                        st.rerun()
                else:
                    st.error("Speech recognition failed")
            except Exception as e:
                st.error(f"Speech API error: {str(e)}")

# Main Chat Interface
st.title(f"💬 {session_type.replace('_', ' ').title()}")
st.caption("Powered by AI Expert Network - Edit responses using the pencil icon")

# Chat History Display
for idx, message in enumerate(st.session_state.chat_history):
    role = message["role"]
    content = message["content"]
    
    with st.chat_message(role if role == "user" else "assistant"):
        if role == "assistant":
            col1, col2 = st.columns([0.9, 0.1])
            with col1:
                st.markdown(content)
            with col2:
                if st.button("✏️", key=f"edit_{idx}"):
                    st.session_state.editing_message_index = idx
        else:
            st.markdown(content)

    # Edit Interface for AI Messages
    if role == "assistant" and st.session_state.editing_message_index == idx:
        with st.form(key=f"edit_form_{idx}"):
            new_content = st.text_area(
                "Edit Response:",
                value=content,
                height=200,
                key=f"edit_content_{idx}"
            )
            
            cols = st.columns([0.8, 0.2])
            with cols[0]:
                if st.form_submit_button("💾 Save Changes"):
                    try:
                        response = requests.put(
                            f"{BACKEND_URL}/edit-ai-message/",
                            json={"section_id": session_type, "updated_message": new_content}
                        )
                        if response.status_code == 200:
                            st.session_state.chat_history[idx]["content"] = new_content
                            st.session_state.editing_message_index = None
                            st.rerun()
                    except Exception as e:
                        st.error(f"Update failed: {str(e)}")
            with cols[1]:
                if st.form_submit_button("❌ Cancel"):
                    st.session_state.editing_message_index = None
                    st.rerun()

# Chat Input at Bottom
if user_input := st.chat_input("Type your message here..."):
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    try:
        with st.spinner(f"Consulting {session_type.replace('_', ' ').title()}..."):
            response = requests.post(
                f"{BACKEND_URL}/chat/{session_type}",
                json={"user_message": user_input}
            )
            
            if response.status_code == 200:
                ai_response = response.json().get("message", "")
                st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            else:
                st.error("Failed to get AI response")
    except Exception as e:
        st.error(f"Backend connection error: {str(e)}")
    finally:
        st.rerun()