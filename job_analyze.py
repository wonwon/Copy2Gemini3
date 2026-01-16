
import os
import sys
import json
import time
import re
from gmail_service import get_service, create_message_with_attachment, get_credentials
from dotenv import load_dotenv
import google.generativeai as genai
import pyperclip
from google.cloud import texttospeech

# 環境変数の読み込み
load_dotenv()

# 設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY_FALLBACK = os.getenv("GEMINI_API_KEY_FALLBACK")
PROMPTS_FILE = "prompts.json"
TARGET_EMAIL = os.getenv("TARGET_EMAIL")

if not GEMINI_API_KEY:
    print("エラー: .env ファイルに GEMINI_API_KEY が見つかりません。")
    sys.exit(1)

# APIキーの設定
genai.configure(api_key=GEMINI_API_KEY)

def get_api_key(use_fallback=False):
    """プライマリまたはフォールバックのAPIキーを返す"""
    if use_fallback:
        return GEMINI_API_KEY_FALLBACK
    return GEMINI_API_KEY

def call_gemini_with_fallback(model_name, prompt, operation_name="API呼び出し"):
    """Gemini APIをフォールバック機能付きで呼び出し"""
    for attempt, use_fallback in enumerate([False, True]):
        api_key = get_api_key(use_fallback)
        if not api_key:
            continue
        
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            key_type = "フォールバック" if use_fallback else "プライマリ"
            print(f"✅ {operation_name} が {key_type} API で成功しました")
            return response
        except Exception as e:
            key_type = "フォールバック" if use_fallback else "プライマリ"
            print(f"❌ {operation_name} が {key_type} API で失敗しました: {e}")
            if not use_fallback and GEMINI_API_KEY_FALLBACK:
                print("   フォールバック API で再試行中...")
    
    raise Exception(f"{operation_name} が両方の API で失敗しました")

def load_prompts():
    """プロンプトをJSONファイルから読み込む"""
    try:
        with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"エラー: {PROMPTS_FILE} の読み込みに失敗しました: {e}")
        sys.exit(1)

def get_clipboard_content():
    """クリップボードからテキストを取得"""
    print("クリップボードから読み取り中...")
    content = pyperclip.paste()
    if not content or not content.strip():
        print("クリップボードが空です。")
        sys.exit(1)
    return content

def text_to_speech(text, output_file="job_proposal.mp3"):
    """Google Cloud TTSを使用してテキストを音声に変換（1.8倍速）"""
    print("音声変換中 (Cloud TTS)...")
    
    # クリーンアップ
    text = text.replace("#", "").replace("*", "")

    try:
        creds = get_credentials()
        if not creds:
             return None
             
        client = texttospeech.TextToSpeechClient(credentials=creds)
        voice = texttospeech.VoiceSelectionParams(
            language_code="ja-JP",
            name="ja-JP-Neural2-B"
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.8
        )

        input_text = texttospeech.SynthesisInput(text=text[:4000]) # 制限考慮
        response = client.synthesize_speech(
            input=input_text, voice=voice, audio_config=audio_config
        )

        with open(output_file, "wb") as out:
            out.write(response.audio_content)
            
        return output_file
    except Exception as e:
        print(f"❌ TTS 失敗: {e}")
        return None


def main():
    target_model = "gemini-2.0-flash-exp" # 最新のFlashモデルをデフォルトに
    if len(sys.argv) > 1:
        target_model = sys.argv[1]

    prompts = load_prompts()
    text = get_clipboard_content()
    
    print(f"入力テキスト長: {len(text)} 文字")
    
    # 1. 提案生成
    base_prompt = prompts.get("job_analyze")
    full_prompt = f"{base_prompt}\n\n{text}"
    
    print(f"AI提案を生成中 ({target_model})...")
    start_time = time.time()
    try:
        response = call_gemini_with_fallback(target_model, full_prompt, "提案生成")
        summary = response.text
        elapsed_time = time.time() - start_time
    except Exception as e:
        print(f"エラー: {e}")
        return

    # 1. Parse Gemini Response (1st line = Title, Rest = Proposal content)
    response_lines = summary.strip().splitlines()
    if response_lines:
        extracted_title = response_lines[0].strip(" #*")
        if len(response_lines) > 2:
            real_summary = "\n".join(response_lines[2:]).strip()
        elif len(response_lines) > 1:
            real_summary = "\n".join(response_lines[1:]).strip()
        else:
            real_summary = summary
    else:
        extracted_title = "求人分析提案"
        real_summary = summary

    print(f"\n--- AI提案 [{elapsed_time:.2f}s] ---\n")
    print(real_summary)
    
    # 2. 音声化
    audio_file = text_to_speech(real_summary)
    
    # 3. メール送信
    print("メール送信準備中...")
    service = get_service()
    if not service:
        return

    subject = f"【求人分析】{extracted_title}"
    
    body = (
        f"分析モデル: {target_model}\n"
        f"処理時間: {elapsed_time:.2f}s\n\n"
        f"--- AIからの提案 ---\n\n"
        f"{real_summary}"
    )
    
    sender = "me"
    recipient = TARGET_EMAIL if TARGET_EMAIL else "me"
    
    from gmail_service import send_message
    msg = create_message_with_attachment(sender, recipient, subject, body, audio_file)
    result = send_message(service, "me", msg)
    
    if result:
        print("✅ メールを送信しました！")
    
    # クリーンアップ
    if audio_file and os.path.exists(audio_file):
        # os.remove(audio_file)
        pass

if __name__ == "__main__":
    main()
