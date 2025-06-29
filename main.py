from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from email_worker import check_inbox_periodically
from grader_utils import read_all_results, write_result_to_file
from pdf_processor import process_single_pdf
from grader import grade_assignment
import threading
import os
import shutil
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def serve_home():
    """Serve the main index.html file"""
    return FileResponse("index.html")

@app.get("/style.css")
async def serve_css():
    """Serve the CSS file"""
    return FileResponse("style.css")

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = f"./{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process the PDF and extract text
    text = process_single_pdf(file_path)    
    # Grade the assignment, passing the generic rubric
    rubric_feedback = grade_assignment(text, "generic")
    
    # Transform the response to match frontend expectations
    result = {
        "filename": file.filename,
        "student_name": rubric_feedback.get("student_name", "Unknown"),
        "overall_grade": rubric_feedback.get("overall_grade", "N/A"),
        "feedback": rubric_feedback.get("feedback", "No feedback available"),
        "criteria_scores": rubric_feedback.get("criteria_scores", [])
    }
    
    # Save to results file with frontend-compatible format
    frontend_result = {
        "name": result["student_name"],
        "email": "",  # Not available from PDF upload
        "course": "Unknown Course",  # Could be extracted or set
        "grade_output": f"Grade: {result['overall_grade']}\n\nFeedback: {result['feedback']}",
        "timestamp": "",
        "criteria_scores": result["criteria_scores"]
    }
    
    write_result_to_file(frontend_result)
    
    return result

@app.get("/results/")
async def get_results():
    results = read_all_results()
    return results

@app.post("/grade-all/")
async def grade_all():
    """Endpoint to process all pending submissions"""
    # This would typically process files in a queue
    # For now, return a success message
    return {"message": "All submissions processed", "processed_count": 0}

# Start the email worker in a separate thread
@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=check_inbox_periodically)
    thread.daemon = True
    thread.start()