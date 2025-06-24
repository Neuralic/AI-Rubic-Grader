# main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from grader import grade_assignment
from pdf_processor import process_all_pdfs

app = FastAPI(title="Assignment Reviewer")

# In-memory store for graded results
graded_results = []

@app.get("/")
def home():
    return {
        "message": "🎓 Assignment Reviewer API is running",
        "endpoints": {
            "POST /grade-all": "Trigger grading for all new PDF assignments",
            "GET /results": "View all graded assignments"
        }
    }

@app.post("/grade-all")
def grade_all():
    """
    Processes all incoming PDFs, grades them via Gemini API,
    and stores the results in memory.
    """
    global graded_results
    students = process_all_pdfs()
    graded_results = []

    for student in students:
        result = grade_assignment(student)
        if result:
            graded_results.append(result)

    return {
        "status": "success",
        "graded_count": len(graded_results),
        "message": f"{len(graded_results)} assignment(s) graded successfully."
    }

@app.get("/results")
def get_results():
    """
    Returns all graded assignments and feedback.
    """
    return JSONResponse(content=graded_results)