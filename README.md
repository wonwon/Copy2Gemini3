# Copy2Gemini3

クリップボードの内容を最新の Gemini モデルで要約し、音声を生成して Gmail で送信する CLI ツールです。

## 主な機能

- **マルチモデル対応**: `gemini-3-pro-preview` および `gemini-3-flash-preview` を使用。
- **自動ジャンル識別**: 入力テキストを解析し、「ニュース」「技術記事」「求人情報」などのジャンルに自動分類。
- **高品質要約**: ジャンルごとに最適化されたプロンプトを使用して要約を生成。
- **Text-to-Speech (TTS)**: Google Cloud TTS を使用して要約の音声を生成（1.8 倍速）。
- **Gmail 連携**: 生成された要約と音声ファイルを自動的に指定のメールアドレスへ送信。
- **自動タイトル抽出**: AI の回答からタイトルを抽出し、メールの件名に反映。

## セットアップ

1. **環境変数の設定**: `.env` ファイルに以下の情報を記述します。
   - `GEMINI_API_KEY`: Google AI Studio の API キー
   - `TARGET_EMAIL`: 送信先メールアドレス
   - `GOOGLE_APPLICATION_CREDENTIALS`: Google Cloud Service Account の鍵 (JSON)
2. **依存関係のインストール**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Google API の認証**:
   初めて実行する際、Gmail へのアクセス権限をリクエストするブラウザ窓が開きます。

## 使い方

クリップボードにテキストをコピーした状態で、以下のスクリプトを実行します。

```bash
# Pro モデルで実行 (精緻な要約)
./run_gemini_pro.sh

# Flash モデルで実行 (高速な要約)
./run_gemini_flash.sh
```

## 開発ドキュメント

- [開発標準 (SOP)](development_standard.md)
- [進化の系譜 (Evolution History)](evolution_history.md)
