# email_worker.py
import imaplib
import email
from email.header import decode_header
import os
import time
from dotenv import load_dotenv

load_dotenv()

IMAP_HOST = os.getenv("IMAP_HOST")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
EMAIL_USER = os.getenv("EMAIL_ADDRESS")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")
SAVE_DIR = "incoming_pdfs"

os.makedirs(SAVE_DIR, exist_ok=True)

def connect_mailbox():
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select("inbox")
    return mail

def save_pdf_attachments(mail):
    status, messages = mail.search(None, '(UNSEEN)')
    email_ids = messages[0].split()

    for email_id in email_ids:
        res, msg_data = mail.fetch(email_id, "(RFC822)")
        if res != "OK":
            continue

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")

                from_ = msg.get("From")
                date = msg.get("Date")
                print(f"📬 New email from {from_} - {subject}")

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        filename = part.get_filename()

                        if filename and filename.endswith(".pdf"):
                            filepath = os.path.join(SAVE_DIR, filename)
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            print(f"✅ Saved PDF: {filename}")
                else:
                    # Not multipart - rare case
                    pass

    print("✅ Inbox scan complete.")

if __name__ == "__main__":
    print("🔁 Starting email poller...")
    while True:
        try:
            mail = connect_mailbox()
            save_pdf_attachments(mail)
            mail.logout()
        except Exception as e:
            print("❌ Error:", e)

        time.sleep(60)  # Poll every 60 seconds