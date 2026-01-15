
import smtplib
import os
from dotenv import load_dotenv

def test_gmail_connection():
    load_dotenv()
    
    user = os.getenv("GMAIL_USER")
    password = os.getenv("GMAIL_APP_PASSWORD")
    
    print(f"Testing login for: {user}")
    
    if not user or not password:
        print("Error: GMAIL_USER or GMAIL_APP_PASSWORD is missing in .env")
        return

    # Password format checks
    clean_pass = password.strip()
    print(f"Password length: {len(password)}")
    if ' ' in password:
        print("⚠️ WARNING: Password contains spaces. App Passwords should be 16 characters with NO spaces.")
    if len(clean_pass) != 16:
        print(f"⚠️ WARNING: Password length is {len(clean_pass)}. It should typically be exactly 16 characters.")


    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.ehlo()
        print("Connection established. Attempting login...")
        server.login(user, password)
        print("✅ Login successful!")
        server.quit()
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Please check your Email and App Password.")
        print("Note: You must use an App Password, not your regular Gmail password.")
        print("Check for spaces in the password string in .env")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    test_gmail_connection()
