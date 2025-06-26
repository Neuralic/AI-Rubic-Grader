import os
import re
from PyPDF2 import PdfReader

INCOMING_DIR = "incoming_pdfs"

def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"❌ Error reading PDF {file_path}: {e}")
        return ""

def extract_student_data(text):
    name_match = re.search(r"(?:Name|Student):\\s*(.+)", text, re.IGNORECASE)
    course_match = re.search(r"(?:Course):\\s*(.+)", text, re.IGNORECASE)

    name = name_match.group(1).strip() if name_match else "Unknown"
    course = course_match.group(1).strip() if course_match else "General Studies"

    return {
        "name": name,
        "course": course,
        "text": text
    }

def process_single_pdf(filepath):
    text = extract_text_from_pdf(filepath)
    if text:
        return extract_student_data(text)
    return None

def process_all_pdfs():
    students = []
    os.makedirs(INCOMING_DIR, exist_ok=True)
    for filename in os.listdir(INCOMING_DIR):
        if filename.endswith(".pdf"):
            file_path = os.path.join(INCOMING_DIR, filename)
            data = process_single_pdf(file_path)
            if data:
                students.append(data)
            os.remove(file_path)  # Remove after processing
    return students