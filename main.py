
import os
import sys
import json
import time
from gmail_service import get_service, create_message_with_attachment, send_message, get_credentials
from dotenv import load_dotenv
import google.generativeai as genai
import pyperclip
from google.cloud import texttospeech

# Load environment variables
load_dotenv()

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY_FALLBACK = os.getenv("GEMINI_API_KEY_FALLBACK")
PROMPTS_FILE = "prompts.json"
TARGET_EMAIL = os.getenv("TARGET_EMAIL")

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in .env file.")
    sys.exit(1)

# 初期設定はプライマリキー
genai.configure(api_key=GEMINI_API_KEY)

def get_api_key(use_fallback=False):
    """プライマリまたはフォールバックのAPIキーを返す"""
    if use_fallback:
        if not GEMINI_API_KEY_FALLBACK:
            print("⚠️  Warning: GEMINI_API_KEY_FALLBACK not set in .env")
            return None
        return GEMINI_API_KEY_FALLBACK
    return GEMINI_API_KEY

def call_gemini_with_fallback(model_name, prompt, operation_name="API call"):
    """Gemini APIをフォールバック機構付きで呼び出し"""
    for attempt, use_fallback in enumerate([False, True]):
        api_key = get_api_key(use_fallback)
        if not api_key:
            continue
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            key_type = "Fallback" if use_fallback else "Primary"
            print(f"✅ {operation_name} succeeded with {key_type} API")
            return response
        except Exception as e:
            key_type = "Fallback" if use_fallback else "Primary"
            print(f"❌ {operation_name} failed with {key_type} API: {e}")
            if not use_fallback:
                print("   Retrying with Fallback API...")
    
    raise Exception(f"{operation_name} failed with both Primary and Fallback APIs")

def load_prompts():
    """Load prompts from JSON file."""
    try:
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {PROMPTS_FILE} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {PROMPTS_FILE}.")
        sys.exit(1)

def get_clipboard_content():
    """Get text from clipboard."""
    print("Reading from clipboard...")
    content = pyperclip.paste()
    if not content or not content.strip():
        print("Clipboard is empty.")
        sys.exit(1)
    return content

def identify_genre(text, prompts):
    """ジャンル識別（フォールバック対応）"""
    print("Identifying genre...")
    
    genres = list(prompts.keys())
    classification_prompt = f"""
    You are a text classifier. Analyze the following text and categorize it into one of these categories: {', '.join(genres)}.
    Return ONLY the category name. If unsure, return 'default'.
    
    Text:
    {text[:500]}... (truncated)
    """
    
    try:
        response = call_gemini_with_fallback('gemini-3-flash-preview', classification_prompt, "Genre identification")
        genre = response.text.strip().lower()
        if genre in genres:
            return genre
        return "default"
    except Exception as e:
        print(f"Genre identification failed: {e}. Using default.")
        return "default"

def summarize_text(text, genre, prompts, model_name='gemini-3-flash-preview'):
    """テキスト要約（フォールバック対応）"""
    print(f"Summarizing as '{genre}' using {model_name}...")
    start_time = time.time()
    
    base_prompt = prompts.get(genre, prompts["default"])
    full_prompt = f"{base_prompt}\n\n{text}"
    
    try:
        response = call_gemini_with_fallback(model_name, full_prompt, "Summarization")
        elapsed_time = time.time() - start_time
        return response.text, elapsed_time
    except Exception as e:
        print(f"Summarization failed ({model_name}): {e}")
        return f"Error: {e}", 0

def text_to_speech(text, output_file="summary.mp3"):
    """Convert text to speech using Google Cloud TTS with 1.8x speed."""
    print("Converting text to speech (Cloud TTS)...")

    # 1. Truncate text if "## 3" exists (to include ## 2)
    if "## 3" in text:
        print("Truncating text before '## 3'...")
        text = text.split("## 3")[0]
        
    # Clean text (remove # and *)
    text = text.replace("#", "").replace("*", "")

    try:
        # 2. Get credentials and initialize client
        creds = get_credentials()
        if not creds:
             print("Failed to get credentials for TTS.")
             return None
             
        client = texttospeech.TextToSpeechClient(credentials=creds)

        # 4. Configure Voice (Japanese, Neural)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ja-JP",
            name="ja-JP-Neural2-B" # Standard Japanese Neural Voice
        )

        # 5. Configure Audio (MP3, 1.8x speed)
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.8
        )

        # Split text into chunks (approx 1000 characters to be safe for 5000 byte limit)
        # Using simple splitting by lines to avoid breaking sentences
        max_chars = 1000
        chunks = []
        current_chunk = ""
        
        for line in text.split('\n'):
            if len(current_chunk) + len(line) < max_chars:
                current_chunk += line + "\n"
            else:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
        if current_chunk:
            chunks.append(current_chunk)

        print(f"Split text into {len(chunks)} chunks.")
        
        combined_audio = b""
        
        for i, chunk in enumerate(chunks):
             print(f"Processing chunk {i+1}/{len(chunks)}...")
             input_text = texttospeech.SynthesisInput(text=chunk)
             response = client.synthesize_speech(
                input=input_text, voice=voice, audio_config=audio_config
             )
             combined_audio += response.audio_content

        # 7. Write to file
        with open(output_file, "wb") as out:
            out.write(combined_audio)
            
        return output_file

    except Exception as e:
        print(f"❌ Cloud TTS failed: {e}")
        if "Project" in str(e) and "deleted" in str(e):
            print("💡 Tip: The Google Cloud project might have been deleted. Please check your credentials.json.")
        return None

def main():
    # Parse Command Line Arguments
    target_model = "gemini-3-flash-preview" # Default
    if len(sys.argv) > 1:
        target_model = sys.argv[1]

    prompts = load_prompts()
    
    # 1. Get Content
    text = get_clipboard_content()
    print(f"Clipboard content length: {len(text)} chars")
    
    # 2. Identify Genre
    genre = identify_genre(text, prompts)
    print(f"Detected Genre: {genre}")
    
    # 3. Summarize (Single Model)
    summary, elapsed_time = summarize_text(text, genre, prompts, target_model)
    print(f"\n--- Summary ({target_model}) [{elapsed_time:.2f}s] ---\n")
    print(summary)
    print("\n----------------\n")
    
    # 4. Parse Gemini Response (1st line = Title, Rest = Summary)
    response_lines = summary.strip().splitlines()
    if response_lines:
        # Use first line as extracted title
        extracted_title = response_lines[0].strip(" #*")
        # Join the rest as the actual summary for TTS and Body
        if len(response_lines) > 2:
            real_summary = "\n".join(response_lines[2:]).strip() # Skip title and optional blank line
        elif len(response_lines) > 1:
            real_summary = "\n".join(response_lines[1:]).strip()
        else:
            real_summary = summary
    else:
        extracted_title = "No Title"
        real_summary = summary

    # 5. TTS (Always run for the selected summary content)
    audio_file = text_to_speech(real_summary)
    
    # 6. Gmail API Sending
    print("Preparing to send email via Gmail API...")
    service = get_service()
    if not service:
        print("❌ Failed to get Gmail service. Check credentials.")
        return

    # Use extracted title for subject
    title = extracted_title if extracted_title else "No Title"
    if len(title) > 60:
        title = title[:60] + "..."
    
    # Customize Subject based on Model (3 chars)
    model_map = {
        "gemini-2.0-flash-lite": "LIT",
        "gemini-3-pro-preview": "PRO",
        "gemini-3-flash-preview": "FLS"
    }
    model_short_name = model_map.get(target_model, "GEM")
    subject = f"【{model_short_name}】{title}"
    
    body = (
        f"Original Text Length: {len(text)}\n"
        f"Genre: {genre}\n"
        f"Model: {target_model} (Time: {elapsed_time:.2f}s)\n\n"
        f"Summary:\n"
        f"{real_summary}"
    )
    
    if not audio_file:
        body += "\n\n(Note: Audio attachment failed during generation.)"
    
    # Assuming the authenticated user is the sender ("me")
    sender = "me" 
    recipient = TARGET_EMAIL if TARGET_EMAIL else "me" # Default to self if target not set
    
    msg = create_message_with_attachment(sender, recipient, subject, body, audio_file)
    result = send_message(service, "me", msg)
    if result:
        print("✅ Email sent successfully via Gmail API!")
    else:
        print("❌ Failed to send email via Gmail API.")
    
    # Cleanup
    if audio_file and os.path.exists(audio_file):
        # os.remove(audio_file)
        pass

if __name__ == "__main__":
    main()
