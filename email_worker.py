import imaplib
import email
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.header import decode_header
from dotenv import load_dotenv
from pdf_processor import process_single_pdf
from grader import grade_assignment
from grader_utils import write_result_to_file
from datetime import datetime, date, timedelta
import json

load_dotenv()

EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")
INCOMING_DIR = "incoming_pdfs"

os.makedirs(INCOMING_DIR, exist_ok=True)

# Generic rubric for any course
GENERIC_RUBRIC = """Rubric for Assignment:

Criteria 1: Content Accuracy (40 points)
- 40 points: All facts, concepts, and information presented are accurate and well-supported.
- 30 points: Mostly accurate, with minor factual errors or less robust support.
- 20 points: Several inaccuracies or insufficient evidence to support claims.
- 10 points: Significant inaccuracies or lack of factual basis.

Criteria 2: Clarity and Organization (30 points)
- 30 points: The assignment is logically organized, clear, and easy to follow. Ideas are presented coherently.
- 20 points: Generally organized, but may have minor issues with flow or coherence.
- 10 points: Somewhat disorganized, with unclear transitions or a weak overall structure.
- 5 points: Disorganized and difficult to follow.

Criteria 3: Critical Thinking and Analysis (20 points)
- 20 points: Demonstrates strong critical thinking and insightful analysis of the subject matter.
- 15 points: Shows some critical thinking, but analysis may be less developed or occasionally lack depth.
- 10 points: Limited critical thinking or superficial analysis.
- 5 points: Lacks critical thinking or provides incorrect reasoning.

Criteria 4: Presentation and Communication (10 points)
- 10 points: Solution is well-organized, legible, and easy to follow. All steps are clearly communicated.
- 0 points: Solution is disorganized and illegible, making it difficult to understand.

Overall Feedback: Provide constructive feedback on strengths and areas for improvement. Suggest specific actions for the student to take to improve their understanding or performance.
"""

def check_inbox_periodically():
    while True:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(EMAIL, PASSWORD)
            mail.select("inbox")

            # Calculate date for 24 hours ago
            date_24_hours_ago = (date.today() - timedelta(days=1)).strftime("%d-%b-%Y")
            
            # Search for unseen emails from the last 24 hours
            status, email_ids = mail.search(None, 
                                            f'(UNSEEN SENTSINCE "{date_24_hours_ago}")')
            
            print(f"Found {len(email_ids[0].split())} unseen emails from the last 24 hours.")
            for email_id in email_ids[0].split():
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])

                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")

                sender, encoding = decode_header(msg["From"])[0]
                if isinstance(sender, bytes):
                    sender = sender.decode(encoding or "utf-8")

                print(f"Processing email from: {sender} with subject: {subject}")

                has_pdf_attachment = False
                for part in msg.walk():
                    try:
                        print(f"Checking part: {part.get_content_type()}")
                        if part.get_content_maintype() == "application" and part.get_content_subtype() == "pdf":
                            has_pdf_attachment = True
                            filename = part.get_filename()
                            if filename:
                                filepath = os.path.join(INCOMING_DIR, filename)
                                print(f"Identified PDF attachment: {filename}. Saving to {filepath}")
                                with open(filepath, "wb") as f:
                                    f.write(part.get_payload(decode=True))
                                print(f"Downloaded PDF: {filename}")

                                # Process PDF, grade, and send email
                                process_and_respond(filepath, sender, subject)
                            else:
                                print("PDF attachment found but no filename.")
                        elif part.get_content_maintype() == "multipart":
                            print("Multipart email part, continuing to walk.")
                        else:
                            print(f"Skipping non-PDF part: {part.get_content_type()}")
                    except AttributeError as ae:
                        print(f"AttributeError when processing email part: {ae}. Part type: {type(part)}. Part content: {part}")
                        print("This part might not be a valid email.message.Message object.")
                    except Exception as part_e:
                        print(f"Unexpected error when processing email part: {part_e}. Part type: {type(part)}")
                
                if not has_pdf_attachment:
                    print(f"No PDF attachment found in email from {sender} with subject: {subject}")

                mail.store(email_id, "+FLAGS", "\\Seen")

            mail.logout()

        except Exception as e:
            print(f"Error in email worker: {e}")
        time.sleep(300)  # Check every 300 seconds (5 minutes)

def process_and_respond(pdf_path, recipient_email, original_subject):
    try:
        print(f"Attempting to process PDF: {pdf_path}")
        extracted_text = process_single_pdf(pdf_path)
        print(f"Extracted text length: {len(extracted_text)}")
        
        # grade_assignment now returns a dictionary (JSON object)
        grading_result = grade_assignment(extracted_text, "generic")
        
        # Check if grading_result is an error dictionary
        if isinstance(grading_result, dict) and "error" in grading_result:
            print(f"Error during grading: {grading_result["error"]}")
            # Ensure the error message is a plain string before passing
            error_msg_to_send = str(grading_result["error"])
            send_email_error(recipient_email, original_subject, error_msg_to_send)
            return

        print(f"Generated rubric feedback: {json.dumps(grading_result, indent=2)}")

        # Transform the result to match frontend expectations

        frontend_result = {

            "name": grading_result.get("student_name", "Unknown"),

            "email": recipient_email,

            "course": "Email Submission",

            "grade_output": f"Grade: {grading_result.get('overall_grade', 'N/A')}\n\nFeedback: {grading_result.get('feedback', 'No feedback available')}",\

            "timestamp": "",

            "criteria_scores": grading_result.get("criteria_scores", [])

        }

        # Save the structured result
        write_result_to_file(frontend_result)
        print(f"Grading result saved.")

        # Format feedback for email
        feedback_for_email = f"Overall Grade: {grading_result.get("overall_grade", "N/A")}\n\n"
        feedback_for_email += "Criteria Scores:\n"
        for criterion in grading_result.get("criteria_scores", []):
            # Escape curly braces in justification and detalle
            justification = criterion.get("justification", "N/A").replace("{", "{{").replace("}", "}}")
            detalle = criterion.get("detalle", "").replace("{", "{{").replace("}", "}}")

            feedback_for_email += f"- {criterion.get("criterion", "N/A")}: {criterion.get("score", "N/A")} - {justification}\n"
            if detalle:
                feedback_for_email += f"  (Points lost: {detalle})\n"
        feedback_for_email += f"\nOverall Feedback: {grading_result.get("feedback", "N/A")}"

        send_email_feedback(recipient_email, original_subject, feedback_for_email)
        print(f"Feedback email sent to {recipient_email}")

    except Exception as e:
        print(f"Error processing and responding to PDF {pdf_path}: {e}")
        # Ensure the error message is a plain string before passing
        error_msg_to_send = str(e)
        send_email_error(recipient_email, original_subject, error_msg_to_send)

def send_email_feedback(recipient_email, original_subject, feedback):
    try:
        msg = MIMEText(feedback)
        msg["Subject"] = f"Re: {original_subject} - Your Assignment Feedback"
        msg["From"] = EMAIL
        msg["To"] = recipient_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
        print(f"Feedback email sent to {recipient_email}")
    except Exception as e:
        print(f"Error sending feedback email to {recipient_email}: {e}")

def send_email_error(recipient_email, original_subject, error_message):
    try:
        # Escape curly braces in the error_message itself
        escaped_error_message = error_message.replace("{", "{{").replace("}", "}}")
        error_body = f"An error occurred while processing your assignment (Subject: {original_subject}):\n\n{escaped_error_message}\n\nPlease try again or contact support."
        msg = MIMEText(error_body)
        msg["Subject"] = f"Re: {original_subject} - Error Processing Assignment"
        msg["From"] = EMAIL
        msg["To"] = recipient_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
        print(f"Error email sent to {recipient_email}")
    except Exception as e:
        print(f"Error sending error email to {recipient_email}: {e}")

if __name__ == "__main__":
    print("Email worker started. Checking inbox periodically...")
    # check_inbox_periodically() # Uncomment to run directly for testing
