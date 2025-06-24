# grader.py
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-pro")

def load_rubric(course_name):
    # Hardcoded sample for now — later load from file or DB
    return {
        "course": course_name,
        "criteria": [
            {"item": "Clarity of writing", "points": 10},
            {"item": "Accuracy of content", "points": 10},
            {"item": "Structure and formatting", "points": 5},
            {"item": "Creativity/Originality", "points": 5}
        ]
    }

def build_prompt(rubric, student_text):
    prompt = f"You are a strict but fair assignment grader.\n\n"
    prompt += f"Here is the grading rubric for the course \"{rubric['course']}\":\n"
    for criterion in rubric["criteria"]:
        prompt += f"- {criterion['item']}: {criterion['points']} points\n"
    prompt += "\nRead the following student assignment and give:\n"
    prompt += "1. Total score out of 30\n"
    prompt += "2. Detailed feedback on where points were lost (if any)\n\n"
    prompt += f"---\nStudent Submission:\n{student_text}\n---"
    return prompt

def grade_assignment(student_data):
    rubric = load_rubric(student_data.get("course", "Unknown Course"))
    prompt = build_prompt(rubric, student_data["content"])

    try:
        response = model.generate_content(prompt)
        return {
            "name": student_data["name"],
            "email": student_data["email"],
            "course": student_data["course"],
            "filename": student_data["filename"],
            "grade_output": response.text
        }
    except Exception as e:
        print("❌ Gemini error:", e)
        return None

if __name__ == "__main__":
    from pdf_processor import process_all_pdfs
    students = process_all_pdfs()

    for student in students:
        result = grade_assignment(student)
        print("\n📊 Result for:", result["name"])
        print(result["grade_output"])
        print("-" * 40)