import os
import sys
import uvicorn

# Add backend directory to sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

if __name__ == "__main__":
    print("====================================================")
    print(" Starting FastAPI Travel Backend on http://127.0.0.1:8000")
    print(" API Documentation: http://127.0.0.1:8000/docs")
    print("====================================================")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
