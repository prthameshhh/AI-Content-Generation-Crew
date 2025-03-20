# AI Content Generation Crew

A comprehensive AI-powered content generation system featuring specialized expert roles, voice input, and a collaborative workflow for creating high-quality content.

## 🌟 Features

- **AI Expert Network** - Specialized AI roles for different stages of content creation:
  - Content Strategist: Defines content vision and direction
  - Research Assistant: Gathers relevant information and sources
  - Technical Writer: Creates precise, well-structured content
  - Editor: Refines and polishes the writing
  - Fact Checker: Ensures accuracy of information
  - Format Specialist: Optimizes layout and presentation
  - Voice Processing Expert: Adapts content for spoken delivery
  - Quality Assurance Agent: Performs final review

- **Interactive Chat Interface** - Clean, intuitive Streamlit frontend with:
  - Role-specific chat histories
  - Real-time AI responses
  - Message editing capabilities
  - Chat history persistence

- **Voice Input Support** - Speak directly to the AI using:
  - Integration with Google Speech Recognition
  - Deepgram real-time transcription API

- **Memory Inheritance System** - Experts build on the work of previous roles, creating a seamless production pipeline

- **Advanced LLM Backend** - Powered by:
  - Groq's LLaMA3-8B model for fast, high-quality responses
  - LangChain for prompt engineering and chat history management
  - FastAPI for robust API endpoints

## 📋 Requirements

- Python 3.8+
- Groq API key
- Deepgram API key (for advanced voice transcription)

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-content-generation-assistant.git
   cd ai-content-generation-assistant
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your API keys:
   ```bash
   # For Linux/Mac
   export GROQ_API_KEY="your_groq_api_key_here"
   
   # For Windows
   set GROQ_API_KEY=your_groq_api_key_here
   ```

   Alternatively, replace the API keys directly in `backend.py` for testing purposes.

## 🚀 Usage

Run the application with a single command:

```bash
python main.py
```

This will:
1. Start the FastAPI backend server
2. Launch the Streamlit frontend
3. Open the application in your default web browser

### Using the Application

1. **Select an Expert**: Choose the AI expert that best fits your current task from the sidebar
2. **Send a Message**: Type in the chat input or use the voice input button
3. **Review Response**: The AI will respond based on its expert role and previous context
4. **Edit if Needed**: Click the pencil icon to edit any AI response
5. **Build Content Iteratively**: Move between experts to refine your content

## 🔄 Workflow Example

1. Begin with the **Content Strategist** to outline your content goals
2. Switch to the **Research Assistant** to gather relevant information
3. Use the **Technical Writer** to create the initial draft
4. Refine with the **Editor** and verify facts with the **Fact Checker**
5. Optimize formatting with the **Format Specialist**
6. If creating spoken content, use the **Voice Processing Expert**
7. Conduct a final review with the **Quality Assurance Agent**

## 🧠 Memory System

The system uses two types of memory:
- **Chat History**: Complete conversation records for each expert
- **Long-term Memory**: Key points extracted from conversations

Experts inherit memory from relevant previous experts according to the workflow design. For example, the Technical Writer inherits memory from both the Content Strategist and Research Assistant.

## 🔧 Customization

### Adding New Experts

1. Define a new prompt template in `prompts.py`
2. Add the expert to the `SUPPORTED_SESSION_TYPES` list in `backend.py`
3. Update the `memory_inheritance` dictionary if needed
4. Add the expert to the dropdown in `frontend.py`

### Modifying Prompts

Expert behavior is controlled by prompt templates in `prompts.py`. Edit these to change how each expert responds to user input.

## 📝 License

[MIT License](LICENSE)

## 🔮 Future Enhancements

- Document upload and analysis capabilities
- Export options for content in various formats
- Integration with project management tools
- Multi-user collaboration features
- Custom expert creation interface

---

Created with ❤️ using LangChain, FastAPI, and Streamlit
