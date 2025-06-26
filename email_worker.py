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

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")
INCOMING_DIR = "incoming_pdfs"

os.makedirs(INCOMING_DIR, exist_ok=True)

def send_email_feedback(to_email, subject, message):
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
            print(f"📧 Feedback email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")

def get_safe_filename(part):
    raw = part.get_filename()
    if not raw:
        return "assignment.pdf"

    try:
        decoded, encoding = decode_header(raw)[0]
        if isinstance(decoded, bytes):
            decoded = decoded.decode(encoding or "utf-8", errors="ignore")
        if not isinstance(decoded, str) or decoded is None:
            return "assignment.pdf"

        safe_name = str(decoded).replace(" ", "_")
        print(f"📄 Processed filename: {safe_name}")  # Optional debug
        return safe_name

    except Exception as e:
        print(f"❌ Failed to decode filename: {e}")
        return "assignment.pdf"

def check_email_for_pdfs():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, PASSWORD)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            return

        for num in messages[0].split():
            _, msg_data = mail.fetch(num, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            sender_email = email.utils.parseaddr(msg["From"])[1]
            subject = msg["Subject"] or "No Subject"

            for part in msg.walk():
                if part.get_content_type() == "application/pdf":
                    filename = get_safe_filename(part)
                    filepath = os.path.join(INCOMING_DIR, filename)

                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))

                    print(f"✅ Saved {filename} from {sender_email}")
                    student_data = process_single_pdf(filepath)

                    if student_data:
                        name = student_data["name"]
                        course = student_data["course"]
                        result = grade_assignment(student_data)

                        feedback = f"""Hello {name},

Here is your AI-reviewed assignment feedback for {course}:

{result['grade_output']}

Regards,
Assignment Reviewer System
"""

                        send_email_feedback(sender_email, f"{course} - Assignment Feedback", feedback)

                        write_result_to_file({
                            "name": name,
                            "course": course,
                            "grade_output": result["grade_output"]
                        })

        mail.logout()

    except Exception as e:
        print("❌ Email check failed:", e)

def check_inbox_periodically():
    while True:
        print("📬 Checking inbox...")
        check_email_for_pdfs()
        time.sleep(300)