import uvicorn
from fastapi import FastAPI, HTTPException, Path, UploadFile, File, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage, BaseChatMessageHistory
from typing import List, Dict, Optional
from prompts import *  # Ensure you have this import
import speech_recognition as sr
import base64
from io import BytesIO
import os
import logging
import deepgram
# speech_backend.py
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
import asyncio

# Replace this with your Deepgram API Key
API_KEY = "DEEPGRAM_API_KEY"

async def start_transcription(update_transcript_callback):
    """Handles real-time transcription using Deepgram and updates transcript in Streamlit."""
    try:
        config = DeepgramClientOptions(options={"keepalive": "true"})
        deepgram = DeepgramClient(API_KEY, config)
        dg_connection = deepgram.listen.asyncwebsocket.v("1")

        async def on_message(self, result, **kwargs):
            transcript = result.channel.alternatives[0].transcript
            if transcript:
                update_transcript_callback(transcript)

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)

        options = LiveOptions(
            model="nova-3",
            language="en-US",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
        )

        if await dg_connection.start(options) is False:
            raise Exception("Failed to connect to Deepgram")

        microphone = Microphone(dg_connection.send)
        microphone.start()

        while True:
            await asyncio.sleep(1)

    except Exception as e:
        raise Exception(f"Deepgram error: {e}")



# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model_name="llama3-8b-8192",
    api_key="GROQ_API_KEY"
)

# Initialize FastAPI app
app = FastAPI(
    title="Multi Agent content generation App",
    version="1.0",
    description="Collaborative content generation with multiple AI agents",
)

# Add CORS middleware (restrict to specific origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),  # Allow multiple origins from env
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage
chat_store: Dict[str, ChatMessageHistory] = {}
long_term_memory: Dict[str, List[str]] = {}

# Memory inheritance map for script writing experts
memory_inheritance = {
    "content_strategist": ["content_strategist"],  # Starts from scratch, no dependencies
    "research_assistant": ["content_strategist"],  # Takes input from content_strategist  
    "technical_writer": ["content_strategist", "research_assistant"],  # Uses both Story Outline & Research Details  
    "editor": ["technical_writer_prompt"],  # Works only on the script draft  
    "fact_checker": ["editor"],  # Checks the edited script  
    "format_specialist": ["fact_checker"],  # Formats the fact-checked script  
    "voice_processing_expert": ["format_specialist"],  # Optimizes the formatted script for voice delivery  
    "quality_assurance_agent": ["voice_processing_expert"]  # Performs a final review  
}

chat_inheritance = memory_inheritance.copy()

def get_chat_history(session_id: str) -> BaseChatMessageHistory:
    """Get chat history for a session, including inherited messages."""
    if session_id not in chat_store:
        chat_store[session_id] = ChatMessageHistory()
    
    session_history = chat_store[session_id]
    
    if session_id in chat_inheritance:
        for inherited_session in chat_inheritance[session_id]:
            if inherited_session in chat_store:
                last_message = get_last_conversation(inherited_session)
                if last_message:
                    session_history.add_message(
                        AIMessage(content=f"Inherited from {inherited_session}: {last_message.content}")
                    )
    
    return session_history

def get_last_conversation(session_id: str) -> BaseMessage:
    """Get the last message from a session's conversation history."""
    history = chat_store.get(session_id)
    if history and history.messages:
        return history.messages[-1]
    return None

def create_chat_prompt_template(template_name: str) -> ChatPromptTemplate:
    """Create a chat prompt template with the given system message."""
    return ChatPromptTemplate.from_messages([
        ("system", template_name),
        ("system", "Long-term memory: {long_term_memory}"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

# Create prompt templates
prompt_templates = {
    "content_strategist": create_chat_prompt_template(content_strategist),
    "research_assistant": create_chat_prompt_template(research_assistant),
    "technical_writer": create_chat_prompt_template(technical_writer),
    "editor": create_chat_prompt_template(editor),
    "fact_checker": create_chat_prompt_template(fact_checker), 
    "format_specialist": create_chat_prompt_template(format_specialist),
    "voice_processing_expert": create_chat_prompt_template(voice_processing_expert),
    "quality_assurance_agent": create_chat_prompt_template(quality_assurance_agent)
}

# Create chains
chains = {
    session_type: RunnableWithMessageHistory(
        prompt_templates[session_type] | llm,
        get_chat_history,
        input_messages_key="input",
        history_messages_key="history"
    ) for session_type in prompt_templates.keys()
}

def get_long_term_memory(session_id: str) -> str:
    """Get long-term memory for a session, including inherited memories."""
    memories = []
    
    if session_id in long_term_memory:
        memories.append(f"Session {session_id} memory: {'. '.join(long_term_memory[session_id])}")
    
    if session_id in memory_inheritance:
        for inherited_session in memory_inheritance[session_id]:
            if inherited_session in long_term_memory:
                memories.append(f"Inherited from {inherited_session}: {'. '.join(long_term_memory[inherited_session])}")
    
    return "\n".join(memories)

def update_long_term_memory(session_id: str, input: str, output: str):
    """Update long-term memory for a session."""
    if session_id not in long_term_memory:
        long_term_memory[session_id] = []
    if len(input) > 20:
        long_term_memory[session_id].append(f"User said: {input}")
    if len(long_term_memory[session_id]) > 5:
        long_term_memory[session_id] = long_term_memory[session_id][-5:]

# Request models
class UserMessage(BaseModel):
    user_message: str = Field(..., description="The message from the user")

class EditMessageRequest(BaseModel):
    section_id: str = Field(..., description="The section ID to edit")
    updated_message: str = Field(..., description="The updated message")

class SpeechInput(BaseModel):
    audio_data: str = Field(..., description="Base64 encoded audio data")

# Supported session types
SUPPORTED_SESSION_TYPES = {
    "content_strategist", "research_assistant", "technical_writer", "editor",
    "fact_checker", "format_specialist", "voice_processing_expert", "quality_assurance_agent"
}

# Speech-to-text function
def speech_to_text(audio_data: str) -> str:
    """Convert speech (base64 encoded audio) to text using speech_recognition."""
    try:
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data)
        audio_file = BytesIO(audio_bytes)

        # Use speech_recognition to convert speech to text
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            return text
    except Exception as e:
        logger.error(f"Error converting speech to text: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error converting speech to text: {str(e)}")

# Speech input endpoint
@app.post("/speech-input/", response_model=Dict[str, str])
async def handle_speech_input(speech_input: SpeechInput):
    """Handle speech input and convert it to text."""
    try:
        text = speech_to_text(speech_input.audio_data)
        return {"text": text}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error handling speech input: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

async def chat(input_text: str, session_id: str) -> str:
    """Process a chat message using the appropriate chain."""
    if session_id not in chains:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid session ID: {session_id}")
    
    chain = chains[session_id]
    long_term_mem = get_long_term_memory(session_id)
    
    try:
        response = await chain.ainvoke(
            {"input": input_text, "long_term_memory": long_term_mem},
            config={"configurable": {"session_id": session_id}}
        )
        
        update_long_term_memory(session_id, input_text, response.content)
        return response.content
    except Exception as e:
        logger.error(f"Chat processing error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Chat processing error: {str(e)}")

# Function to edit the most recent AI message
def edit_most_recent_ai_message(chat_store, section_id: str, updated_message: str):
    """Fetches the most recent AI message from a specified section, allows editing, and updates it in the chat store."""
    if section_id not in chat_store:
        return {"error": f"Section ID '{section_id}' not found in chat store."}

    section_messages = chat_store[section_id].messages

    for message in reversed(section_messages):
        if message.type == 'ai':
            message.content = updated_message
            return {"message": f"Message updated to: {message.content}"}

    return {"error": "No AI message found to edit in the specified section."}

# Chat endpoint
@app.post("/chat/{session_type}", response_model=Dict[str, str])
async def handle_chat(
    session_type: str = Path(..., description="The type of chat session"),
    request: UserMessage = None,
):
    """Unified chat endpoint with session type passed as a URL parameter."""
    try:
        # Validate session type
        if session_type not in SUPPORTED_SESSION_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid session type: {session_type}. Supported types are {', '.join(SUPPORTED_SESSION_TYPES)}.",
            )
        
        # Process the chat request
        message = await chat(request.user_message, session_type)
        return {"message": message}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error handling chat request: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Endpoint to edit the most recent AI message
@app.put("/edit-ai-message/", response_model=Dict[str, str])
async def edit_ai_message(request: EditMessageRequest):
    result = edit_most_recent_ai_message(chat_store, request.section_id, request.updated_message)

    if 'error' in result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result['error'])
    return result



# Function to run the server
def run_backend():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    run_backend()