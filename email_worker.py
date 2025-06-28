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

load_dotenv()

EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")
INCOMING_DIR = "incoming_pdfs"

os.makedirs(INCOMING_DIR, exist_ok=True)

def check_inbox_periodically():
    while True:
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(EMAIL, PASSWORD)
            mail.select("inbox")

            status, email_ids = mail.search(None, "UNSEEN")
            print(f"Found {len(email_ids[0].split())} unseen emails.")
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
                
                if not has_pdf_attachment:
                    print(f"No PDF attachment found in email from {sender} with subject: {subject}")

                mail.store(email_id, "+FLAGS", "\\Seen")

            mail.logout()

        except Exception as e:
            print(f"Error in email worker: {e}")
        time.sleep(60)  # Check every 60 seconds

def process_and_respond(pdf_path, recipient_email, original_subject):
    try:
        print(f"Attempting to process PDF: {pdf_path}")
        extracted_text = process_single_pdf(pdf_path)
        print(f"Extracted text length: {len(extracted_text)}")
        rubric_feedback = grade_assignment(extracted_text)
        print(f"Generated rubric feedback length: {len(rubric_feedback)}")

        # Save the result
        result_filename = os.path.basename(pdf_path).replace(".pdf", "_graded.txt")
        write_result_to_file(result_filename, rubric_feedback)
        print(f"Grading result saved to {result_filename}")

        send_email_feedback(recipient_email, original_subject, rubric_feedback)
        print(f"Feedback email sent to {recipient_email}")

    except Exception as e:
        print(f"Error processing and responding to PDF {pdf_path}: {e}")
        send_email_error(recipient_email, original_subject, e)

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
        error_body = f"An error occurred while processing your assignment (Subject: {original_subject}):\n\n{error_message}\n\nPlease try again or contact support."
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


