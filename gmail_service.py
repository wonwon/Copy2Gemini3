
import os.path
import base64
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import mimetypes

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/cloud-platform"
]

def get_credentials():
    """Gets valid user credentials from storage or runs auth flow."""
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                print("❌ Error: credentials.json not found.")
                print("Please download it from Google Cloud Console and place it in this directory.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

def get_service():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = get_credentials()
    if not creds:
        return None

    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except HttpError as error:
        print(f"❌ An error occurred: {error}")
        if error.resp.status == 403:
             print("💡 Tip: This might be due to a deleted Google Cloud project or insufficient permissions. Please check your credentials.json and ensure Gmail API is enabled.")
        return None

def create_message_with_attachment(sender, to, subject, message_text, file=None):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.
      file: The path to the file to be attached.

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEMultipart()
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject

    msg = MIMEText(message_text)
    message.attach(msg)

    if file and os.path.exists(file):
        try:
            content_type, encoding = mimetypes.guess_type(file)

            if content_type is None or encoding is not None:
                # No guess could be made, or the file is encoded (compressed), so
                # use a generic bag-of-bits type.
                content_type = "application/octet-stream"
            
            main_type, sub_type = content_type.split("/", 1)
            
            if main_type == "text":
                with open(file, "r") as f:
                    msg = MIMEText(f.read(), _subtype=sub_type)
            elif main_type == "image":
                with open(file, "rb") as f:
                    msg = MIMEImage(f.read(), _subtype=sub_type)
            elif main_type == "audio":
                with open(file, "rb") as f:
                    msg = MIMEAudio(f.read(), _subtype=sub_type)
            else:
                with open(file, "rb") as f:
                    msg = MIMEBase(main_type, sub_type)
                    msg.set_payload(f.read())
                    encoders.encode_base64(msg)
            
            msg.add_header("Content-Disposition", "attachment", filename=os.path.basename(file))
            message.attach(msg)
            print(f"✅ Attached file: {os.path.basename(file)} ({os.path.getsize(file)} bytes)")
        except Exception as e:
            print(f"❌ Failed to attach file {file}: {e}")
            # 添付失敗時も処理を継続
    elif file:
        print(f"⚠️  Warning: File not found: {file}")

    return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

def send_message(service, user_id, message):
    """Send an email message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      message: Message to be sent.

    Returns:
      Sent Message.
    """
    try:
        message = (
            service.users().messages().send(userId=user_id, body=message).execute()
        )
        print(f"Message Id: {message['id']}")
        return message
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
