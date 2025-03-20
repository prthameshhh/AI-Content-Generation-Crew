import subprocess
import time
import webbrowser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_backend():
    """Starts the FastAPI backend server."""
    try:
        return subprocess.Popen(
            ["uvicorn", "backend:app", "--host", "127.0.0.1", "--port", "8000"], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except Exception as e:
        logger.error(f"Failed to start backend: {str(e)}")
        raise

def run_frontend():
    """Starts the Streamlit frontend without opening a browser automatically."""
    try:
        return subprocess.Popen(
            ["streamlit", "run", "frontend.py", "--server.headless", "true"], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
    except Exception as e:
        logger.error(f"Failed to start frontend: {str(e)}")
        raise

if __name__ == "__main__":
    print("Starting FastAPI backend...")
    try:
        backend_process = run_backend()
        time.sleep(5)  # Wait for backend to start
        
        print("Starting Streamlit frontend...")
        frontend_process = run_frontend()
        time.sleep(3)  # Wait for frontend to start
        
        # Open the Streamlit app manually
        webbrowser.open("http://localhost:8501")  

        backend_process.wait()
        frontend_process.wait()  # Wait for frontend to finish
        
    except KeyboardInterrupt:
        print("Shutting down...")
        backend_process.terminate()
        frontend_process.terminate()
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
