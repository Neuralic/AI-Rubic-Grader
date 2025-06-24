# main.py
from fastapi import FastAPI
from grader import grade_assignment
from pdf_processor import process_all_pdfs
from fastapi.responses import JSONResponse

app = FastAPI(title="Assignment Reviewer")

# Store graded results in memory for now (or extend to DB later)
graded_results = []

@app.get("/")
def home():
    return {"message": "🎓 Assignment Reviewer API is running"}

@app.post("/grade-all")
def grade_all():
    global graded_results
    students = process_all_pdfs()
    graded_results = []

    for student in students:
        result = grade_assignment(student)
        if result:
            graded_results.append(result)

    return {"graded": len(graded_results), "status": "completed"}

@app.get("/results")
def get_results():
    return JSONResponse(content=graded_results)