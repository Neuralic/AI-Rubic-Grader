# pdf_processor.py
import os
import re
from PyPDF2 import PdfReader

INCOMING_DIR = "incoming_pdfs"

# Ensure the directory exists (create if not)
if not os.path.exists(INCOMING_DIR):
    os.makedirs(INCOMING_DIR)

def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return ""

def parse_student_info(text):
    """
    Try to extract student's name, email, and course from the assignment.
    This can be improved later with regex or AI parsing.
    """
    student = {
        "name": None,
        "email": None,
        "course": None,
        "content": text.strip()
    }

    # Basic regex patterns (adjust to match your actual assignment layout)
    name_match = re.search(r"Name[:\-]?\s*(.+)", text, re.IGNORECASE)
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    course_match = re.search(r"Course[:\-]?\s*(.+)", text, re.IGNORECASE)

    if name_match:
        student["name"] = name_match.group(1).strip()
    if email_match:
        student["email"] = email_match.group(0).strip()
    if course_match:
        student["course"] = course_match.group(1).strip()

    return student

def process_all_pdfs():
    results = []

    for filename in os.listdir(INCOMING_DIR):
        if filename.endswith(".pdf"):
            file_path = os.path.join(INCOMING_DIR, filename)
            print(f"📄 Processing {filename}...")
            text = extract_text_from_pdf(file_path)
            student_data = parse_student_info(text)
            student_data["filename"] = filename
            results.append(student_data)

    return results

if __name__ == "__main__":
    students = process_all_pdfs()
    for student in students:
        print("✅ Parsed assignment:")
        print(student)
        print("-" * 40)