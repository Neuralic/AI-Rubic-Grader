from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from email_worker import check_inbox_periodically
from grader_utils import read_all_results
from pdf_processor import process_single_pdf
from grader import grade_assignment
import threading
import os
import shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the root directory
app.mount("/", StaticFiles(directory="."), name="static")

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = f"./{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process the PDF and extract text
    text = process_single_pdf(file_path)    
    # Grade the assignment
    rubric_feedback = grade_assignment(text)
    
    return {"filename": file.filename, "rubric_feedback": rubric_feedback}

@app.get("/results/")
async def get_results():
    results = read_all_results()
    return results

# Start the email worker in a separate thread
@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=check_inbox_periodically)
    thread.daemon = True
    thread.start()



