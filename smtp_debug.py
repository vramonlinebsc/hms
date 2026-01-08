import os
import smtplib
import socket
import sys
import traceback

print("=== SMTP DEBUG TEST START ===")

# 1. Read environment variables
smtp_user = os.environ.get("HMS_EMAIL_USER")
smtp_pass = os.environ.get("HMS_EMAIL_PASSWORD")

print("SMTP USER:", smtp_user)
print("SMTP PASS SET:", "YES" if smtp_pass else "NO")
print("SMTP PASS LENGTH:", len(smtp_pass) if smtp_pass else 0)

if not smtp_user or not smtp_pass:
    print("❌ Environment variables not set correctly")
    sys.exit(1)

try:
    print("\n[1] Creating SMTP object...")
    server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
    print("✔ SMTP object created")

    print("\n[2] Starting TLS...")
    server.starttls()
    print("✔ TLS started")

    print("\n[3] Attempting login...")
    server.login(smtp_user, smtp_pass)
    print("✔ LOGIN OK")

    print("\n[4] Sending NO email (login-only test)")
    server.quit()
    print("✔ Connection closed cleanly")

except socket.timeout:
    print("❌ TIMEOUT: Network or Gmail not responding")
    traceback.print_exc()

except smtplib.SMTPAuthenticationError as e:
    print("❌ AUTH ERROR: Gmail rejected credentials")
    print("SMTP code:", e.smtp_code)
    print("SMTP message:", e.smtp_error)
    traceback.print_exc()

except Exception as e:
    print("❌ UNEXPECTED ERROR:", type(e).__name__)
    traceback.print_exc()

print("\n=== SMTP DEBUG TEST END ===")
