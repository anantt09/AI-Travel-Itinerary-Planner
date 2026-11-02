import os
import sys
import uvicorn

# Ensure the backend directory is in the Python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("====================================================")
    print(" Travel Itinerary Planner Backend (FastAPI)")
    print(" Server: http://127.0.0.1:8000")
    print(" API Docs: http://127.0.0.1:8000/docs")
    print("====================================================")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
