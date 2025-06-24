# main.py
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from grader import grade_assignment
from pdf_processor import process_all_pdfs

app = FastAPI()

graded_results = []

@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

@app.get("/style.css")
def serve_css():
    return FileResponse("style.css", media_type="text/css")

@app.post("/grade-all")
def grade_all():
    global graded_results
    students = process_all_pdfs()
    graded_results = []

    for student in students:
        result = grade_assignment(student)
        if result:
            graded_results.append(result)

    return {"status": "success", "graded": len(graded_results)}


import threading
from email_worker import check_inbox_periodically

@app.on_event("startup")
def start_background_tasks():
    threading.Thread(target=check_inbox_periodically, daemon=True).start()

@app.get("/results")
def get_results():
    return JSONResponse(content=graded_results)