from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from email_worker import check_inbox_periodically
from grader_utils import read_all_results
from pdf_processor import process_all_pdfs
from grader import grade_assignment
import threading
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/", StaticFiles(directory=".", html=True), name="static")

@app.on_event("startup")
def start_background_tasks():
    print("🚀 Background inbox checker started.")
    threading.Thread(target=check_inbox_periodically, daemon=True).start()

@app.get("/", response_class=HTMLResponse)
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