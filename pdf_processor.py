import os
import re
from PyPDF2 import PdfReader

INCOMING_DIR = "incoming_pdfs"

def extract_text_from_pdf(file_path):
    print(f"Attempting to extract text from PDF: {file_path}")
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        print(f"Successfully extracted text from {file_path}. Length: {len(text)}")
        return text
    except Exception as e:
        print(f"Error reading PDF {file_path}: {e}")
        return ""

def extract_student_data(text):
    name_match = re.search(r"(?:Name|Student):\s*(.+)", text, re.IGNORECASE)
    course_match = re.search(r"(?:Course):\s*(.+)", text, re.IGNORECASE)
    assignment_match = re.search(r"(?:Assignment):\s*(.+)", text, re.IGNORECASE)

    student_name = name_match.group(1).strip() if name_match else "Unknown Student"
    course_name = course_match.group(1).strip() if course_match else "Unknown Course"
    assignment_name = assignment_match.group(1).strip() if assignment_match else "Unknown Assignment"

    return student_name, course_name, assignment_name

def process_single_pdf(file_path):
    print(f"Processing single PDF: {file_path}")
    # Ensure the directory exists (create if not)
    if not os.path.exists(INCOMING_DIR):
        os.makedirs(INCOMING_DIR)

    # For now, we'll just process the single uploaded file directly
    text = extract_text_from_pdf(file_path)
    return text


if __name__ == '__main__':
    # Example Usage:
    # Create a dummy PDF file for testing
    # with open("dummy.pdf", "w") as f:
    #     f.write("This is a dummy PDF content.")

    # extracted_text = process_single_pdf("dummy.pdf")
    # print(f"Extracted Text: {extracted_text}")

    # student_name, course_name, assignment_name = extract_student_data(extracted_text)
    # print(f"Student Name: {student_name}")
    # print(f"Course Name: {course_name}")
    # print(f"Assignment Name: {assignment_name}")
    pass

