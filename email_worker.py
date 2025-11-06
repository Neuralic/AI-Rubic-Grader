import imaplib
import email
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.header import decode_header
from dotenv import load_dotenv
from pdf_processor import process_single_pdf
from grader import analyze_document
from grader_utils import write_result_to_file
from datetime import datetime, date, timedelta
import json
import re
from concurrent.futures import ThreadPoolExecutor
import threading

load_dotenv()

EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_PASSWORD")
INCOMING_DIR = "incoming_pdfs"

os.makedirs(INCOMING_DIR, exist_ok=True)

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=3)

def extract_email_address(sender_string):
    """Extract just the email address from a sender string like 'Name <email@example.com>'"""
    # Try to find email in angle brackets first
    match = re.search(r'<(.+?)>', sender_string)
    if match:
        return match.group(1)
    # If no angle brackets, assume the whole string is the email
    return sender_string.strip()

# Document type detection helper
def detect_document_type(text):
    """Auto-detect financial document type from content"""
    text_lower = text.lower()
    if "bank statement" in text_lower or "account balance" in text_lower or "checking account" in text_lower:
        return "bank_statement"
    elif "credit report" in text_lower or "credit score" in text_lower or "fico" in text_lower or "experian" in text_lower:
        return "credit_report"
    else:
        return "generic"

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
            
            email_list = email_ids[0].split()
            print(f"Found {len(email_list)} unseen emails from the last 24 hours.")
            
            for email_id in email_list:
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])

                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")

                sender, encoding = decode_header(msg["From"])[0]
                if isinstance(sender, bytes):
                    sender = sender.decode(encoding or "utf-8")
                
                # Extract just the email address from the sender field
                sender_email = extract_email_address(sender)

                print(f"[Financial Analyzer] Processing email from: {sender} (extracted: {sender_email}) with subject: {subject}")

                has_pdf_attachment = False
                for part in msg.walk():
                    try:
                        if part.get_content_maintype() == "application" and part.get_content_subtype() == "pdf":
                            has_pdf_attachment = True
                            filename = part.get_filename()
                            if filename:
                                filepath = os.path.join(INCOMING_DIR, filename)
                                print(f"Identified PDF attachment: {filename}. Saving to {filepath}")
                                with open(filepath, "wb") as f:
                                    f.write(part.get_payload(decode=True))
                                print(f"Downloaded PDF: {filename}")

                                # Process in background thread for swift response
                                executor.submit(process_and_respond, filepath, sender_email, subject)
                                print(f"[Financial Analyzer] Queued processing for {filename}")
                            else:
                                print("PDF attachment found but no filename.")
                    except AttributeError as ae:
                        print(f"AttributeError when processing email part: {ae}. Part type: {type(part)}")
                    except Exception as part_e:
                        print(f"Unexpected error when processing email part: {part_e}. Part type: {type(part)}")
                
                if not has_pdf_attachment:
                    print(f"No PDF attachment found in email from {sender_email} with subject: {subject}")

                # Mark as seen immediately after downloading attachments
                mail.store(email_id, "+FLAGS", "\\Seen")

            mail.logout()

        except Exception as e:
            print(f"Error in email worker: {e}")
        
        # Reduced check interval for faster response
        time.sleep(30)  # Check every 30 seconds instead of 5 minutes

def process_and_respond(pdf_path, recipient_email, original_subject):
    try:
        print(f"[Financial Analyzer] Processing PDF: {pdf_path}")
        extracted_text = process_single_pdf(pdf_path)
        print(f"[Financial Analyzer] Extracted text length: {len(extracted_text)}")
        
        # Auto-detect document type
        doc_type = detect_document_type(extracted_text)
        print(f"[Financial Analyzer] Detected document type: {doc_type}")
        
        # analyze_document returns a dictionary (JSON object)
        analysis_result = analyze_document(extracted_text, doc_type)
        
        # Check if analysis_result is an error dictionary
        if isinstance(analysis_result, dict) and "error" in analysis_result:
            print(f"[Financial Analyzer] Error during analysis: {analysis_result['error']}")
            error_msg_to_send = str(analysis_result["error"])
            send_email_error(recipient_email, original_subject, error_msg_to_send)
            return

        print(f"[Financial Analyzer] Analysis complete")

        # Transform the result to match frontend expectations
        frontend_result = {
            "name": analysis_result.get("client_name", "Unknown"),
            "email": recipient_email,
            "course": doc_type.replace("_", " ").title(),
            "grade_output": f"Assessment: {analysis_result.get('overall_assessment', 'Pending Review')}\n\nSummary: {analysis_result.get('analysis_summary', 'No summary available')}\n\nKey Findings: {analysis_result.get('key_findings', 'No findings')}\n\nRed Flags: {analysis_result.get('red_flags', 'None identified')}\n\nRecommendations: {analysis_result.get('recommendations', 'No recommendations')}",
            "timestamp": "",
            "criteria_scores": analysis_result.get("criteria_analysis", []),
            "document_type": doc_type,
            "red_flags": analysis_result.get("red_flags", "None identified")
        }

        # Save the structured result
        write_result_to_file(frontend_result)
        print(f"[Financial Analyzer] Analysis result saved.")

        # Format feedback for email - safely convert all values to strings
        feedback_for_email = f"FINANCIAL DOCUMENT ANALYSIS REPORT\n\n"
        feedback_for_email += f"Document Type: {doc_type.replace('_', ' ').upper()}\n"
        
        overall_assessment = analysis_result.get('overall_assessment', 'N/A')
        feedback_for_email += f"Overall Assessment: {str(overall_assessment)}\n\n"
        
        analysis_summary = analysis_result.get('analysis_summary', 'N/A')
        feedback_for_email += f"SUMMARY:\n{str(analysis_summary)}\n\n"
        
        key_findings = analysis_result.get('key_findings', 'N/A')
        feedback_for_email += f"KEY FINDINGS:\n{str(key_findings)}\n\n"
        
        # Add criteria analysis
        feedback_for_email += "DETAILED ANALYSIS:\n"
        for criterion in analysis_result.get("criteria_analysis", []):
            # Safely get findings and convert to string before replacing
            findings_raw = criterion.get("findings", "N/A")
            findings = str(findings_raw).replace("{", "{{").replace("}", "}}") if findings_raw else "N/A"
            
            assessment_raw = criterion.get("assessment", "N/A")
            assessment = str(assessment_raw) if assessment_raw else "N/A"
            
            notes_raw = criterion.get("notes", "")
            notes = str(notes_raw).replace("{", "{{").replace("}", "}}") if notes_raw else ""

            feedback_for_email += f"\n{criterion.get('criterion', 'N/A')}:\n"
            feedback_for_email += f"  Findings: {findings}\n"
            feedback_for_email += f"  Assessment: {assessment}\n"
            if notes:
                feedback_for_email += f"  Notes: {notes}\n"
        
        # Add red flags section - safely convert to string
        red_flags = analysis_result.get("red_flags", "None identified")
        red_flags_str = str(red_flags) if red_flags else "None identified"
        if red_flags_str and red_flags_str != "None identified":
            feedback_for_email += f"\n⚠️ RED FLAGS:\n{red_flags_str}\n"
        
        recommendations = analysis_result.get('recommendations', 'N/A')
        feedback_for_email += f"\nRECOMMENDATIONS:\n{str(recommendations)}\n"
        feedback_for_email += "\n---\nThis is an automated analysis. Please review the original document for complete details."

        send_email_feedback(recipient_email, original_subject, feedback_for_email)
        print(f"[Financial Analyzer] Analysis report sent to {recipient_email}")

    except Exception as e:
        print(f"Error processing and responding to PDF {pdf_path}: {e}")
        import traceback
        traceback.print_exc()  # Print full error trace for debugging
        error_msg_to_send = str(e)
        send_email_error(recipient_email, original_subject, error_msg_to_send)

def send_email_feedback(recipient_email, original_subject, feedback):
    try:
        # Ensure we have a clean email address
        clean_email = extract_email_address(recipient_email)
        
        msg = MIMEText(feedback)
        msg["Subject"] = f"Re: {original_subject} - Financial Document Analysis Report"
        msg["From"] = EMAIL
        msg["To"] = clean_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
        print(f"[Financial Analyzer] Analysis report email sent to {clean_email}")
    except Exception as e:
        print(f"[Financial Analyzer] Error sending analysis report to {recipient_email}: {e}")

def send_email_error(recipient_email, original_subject, error_message):
    try:
        # Ensure we have a clean email address
        clean_email = extract_email_address(recipient_email)
        
        escaped_error_message = error_message.replace("{", "{{").replace("}", "}}")
        error_body = f"An error occurred while processing your financial document (Subject: {original_subject}):\n\n{escaped_error_message}\n\nPlease ensure the document is a valid PDF and try again, or contact our support team."
        msg = MIMEText(error_body)
        msg["Subject"] = f"Re: {original_subject} - Error Processing Document"
        msg["From"] = EMAIL
        msg["To"] = clean_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)
        print(f"[Financial Analyzer] Error email sent to {clean_email}")
    except Exception as e:
        print(f"[Financial Analyzer] Error sending error email to {recipient_email}: {e}")

if __name__ == "__main__":
    print("[Financial Analyzer] Email worker started. Monitoring inbox for financial documents...")
    print("[Financial Analyzer] Swift response mode enabled (30-second check interval)")
    check_inbox_periodically()
