# Copy2Gemini3 進化の系譜 (Evolution History)

## 2026-01-16: Gemini 3 プレビューモデルへの移行とメール件名の自動最適化

### [P]: Planning

- **背景**: より高性能な `gemini-3-pro-preview` および `gemini-3-flash-preview` を利用することで、要約の質と速度を向上させる。
- **課題**: Gemini が生成する要約の先頭に記事タイトルを含めるようにし、それを Gmail の件名として自動的に使用することで、受信箱での視認性を高める。

### [D]: Design/Decision

- **モデル採用**: `gemini-3-pro-preview` および `gemini-3-flash-preview` を主要モデルとして採用。
- **パースロジック**: Gemini のレスポンスの 1 行目をタイトルとして抽出し、2 行目以降（または 3 行目以降）を要約本文および TTS 生成対象とするロジックを `main.py` に実装。
- **件名フォーマット**: `【モデル略称】タイトル` の形式を採用（例：`【PRO】記事のタイトル`）。

### [A]: Action/Achievement

- `main.py`: モデル名の更新、レスポンスのパースロジック追加、Gmail メッセージ生成ロジックの修正。
- `prompts.json`: 出力の最初にタイトルを配置するよう、すべてのプロンプトに指示を追加。
- `job_analyze.py`: `gemini-3-pro-preview` へのモデル名更新。
- `.gitignore`: macOS のメタデータファイル (`._*`) を無視対象に追加。
- GitHub へのプッシュ完了。
