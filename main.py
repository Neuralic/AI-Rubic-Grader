from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from email_worker import check_inbox_periodically
from grader_utils import read_all_results
from pdf_processor import process_all_pdfs
from grader import grade_assignment
import threading
import os

app = FastAPI()

# Allow frontend to access backend from same origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Run email checker as a background task on startup
@app.on_event("startup")
def start_background_tasks():
    threading.Thread(target=check_inbox_periodically, daemon=True).start()

@app.get("/")
def get_index():
    return FileResponse("index.html")

@app.get("/results")
def get_results():
    return read_all_results()

@app.get("/grade-all")
def grade_all():
    students = process_all_pdfs()
    results = []
    for student_data in students:
        result = grade_assignment(student_data)
        results.append({
            "name": student_data["name"],
            "course": student_data["course"],
            "grade_output": result["grade_output"]
        })
    return results