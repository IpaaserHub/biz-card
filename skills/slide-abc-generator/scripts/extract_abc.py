#!/usr/bin/env python3
"""
extract_abc.py — 画像を解析してA/B/C（デザインシステム・スライドタイプ・コンテンツ原稿）を生成するスクリプト

使用方法:
    python extract_abc.py --image <画像パス> [--image <画像パス2> ...] --output <出力先ディレクトリ>

出力:
    <output>/design_system_A.md  — A：デザインシステム
    <output>/slide_types_B.md    — B：スライドタイプ
    <output>/content_draft_C.md  — C：コンテンツ原稿
"""

import argparse
import base64
import os
import sys
from pathlib import Path
from openai import OpenAI

# ─────────────────────────────────────────────
# プロンプト定義
# ─────────────────────────────────────────────

PROMPT_A = """
あなたは資料デザインの専門家です。提供された画像（スライド・資料・デザインサンプル）を詳細に分析し、
「A：デザインシステム（憲法）」を抽出してください。

## 出力形式（Markdown）

# デザインシステム（A）

## カラーパレット

| 役割 | カラーコード | 用途 |
|------|-------------|------|
| メインカラー | #XXXXXX | ... |
| アクセントカラー | #XXXXXX | ... |
| 背景色 | #XXXXXX | ... |
| テキスト色 | #XXXXXX | ... |
（画像から読み取れる色をすべて記載）

## タイポグラフィ

| 要素 | フォント | サイズ（推定） | ウェイト | 用途 |
|------|---------|--------------|---------|------|
| H1（タイトル） | ... | ...pt | ... | ... |
| H2（見出し） | ... | ...pt | ... | ... |
| 本文 | ... | ...pt | ... | ... |
（読み取れる範囲で推定）

## レイアウトルール

- **余白（マージン）：** 推定値
- **グリッド：** カラム構成の推定
- **要素間スペース：** 推定値

## トーン＆マナー

- **文体：** 「だ・である調」か「です・ます調」か（テキストから判断）
- **表現スタイル：** 簡潔・箇条書き重視 / 説明的・文章重視
- **ブランドキーワード：** 画像から感じ取れるブランドの印象・キーワード

## 総評

このデザインシステムの特徴を2〜3文で説明する。

---
注意：
- カラーコードは画像から可能な限り正確に推定する
- フォントが不明な場合は「[推定: Noto Sans等のサンセリフ体]」のように記載する
- 推定値には「（推定）」と付記する
""".strip()

PROMPT_B = """
あなたは資料構成の専門家です。提供された画像（スライド・資料・デザインサンプル）を詳細に分析し、
「B：スライドタイプ（金型）」を抽出してください。

## 出力形式（Markdown）

# スライドタイプ（B）

## ページ構成（推奨フロー）

画像から読み取れるスライドの構成・流れを番号付きリストで記載する。
例：
1. **表紙** — タイトル・サブタイトル・日付
2. **アジェンダ** — 目次
3. ...

## スライドタイプ一覧

画像に含まれる各スライドタイプを分析し、以下の形式で記載する：

### TYPE-XX：[タイプ名]
- **レイアウト：** 配置の説明
- **要素：** 含まれる要素のリスト
- **使用場面：** どのような内容に適しているか
- **背景：** 背景色・画像の指定

（画像から読み取れるすべてのタイプを記載。最低3タイプ以上）

## レイアウトパターン

画像から読み取れるレイアウトパターンを説明する（2カラム、左テキスト右画像など）。

---
注意：
- 画像に複数のスライドが含まれる場合は、すべてを分析する
- 1枚の画像でも、そこから推定できる他のスライドタイプを提案してよい
- 「このタイプは〇〇ページに使う」という具体的な使用場面を必ず記載する
""".strip()

PROMPT_C = """
あなたは資料編集の専門家です。提供された画像（スライド・資料・デザインサンプル）から、
「C：コンテンツ原稿（材料）」を抽出してください。

## 出力形式（Markdown）

# コンテンツ原稿（C）

> **注意：** このファイルは「毎回変わる変数」です。A（デザインシステム）とB（スライドタイプ）は固定したまま、このCだけを書き換えることで同スタイルの資料を量産できます。

## スライド別コンテンツ

画像に含まれるすべてのスライド・ページのテキストを忠実に抽出し、以下の形式で記載する：

### [ページ番号] [スライドタイトル]
- **メッセージ（このスライドの主旨）：** ...
- **タイトル：** ...
- **本文・箇条書き：**
  - ...
  - ...
- **データ・数値：** ...
- **その他の要素：** ...

（すべてのスライドについて繰り返す）

## 次回作成時の変数リスト

このコンテンツを別テーマで作り直す際に変更すべき「変数」を一覧化する：

| 変数名 | 現在の値 | 変更例 |
|--------|---------|--------|
| タイトル | ... | ... |
| テーマ | ... | ... |
| 対象読者 | ... | ... |
| 主要メッセージ | ... | ... |

---
注意：
- テキストが読み取れない部分は `[要確認]` と記載する
- 画像・グラフの内容は「[グラフ：〇〇の推移を示す棒グラフ]」のように説明文で記載する
- テキストは原文を忠実に抽出し、要約・改変しない
""".strip()


# ─────────────────────────────────────────────
# ユーティリティ関数
# ─────────────────────────────────────────────

def encode_image(image_path: str) -> tuple[str, str]:
    """画像をbase64エンコードし、MIMEタイプと共に返す"""
    path = Path(image_path)
    ext = path.suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(ext, "image/png")
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return data, mime_type


def build_messages(prompt: str, image_paths: list[str]) -> list[dict]:
    """マルチモーダルメッセージを構築する"""
    content = [{"type": "text", "text": prompt}]
    for img_path in image_paths:
        data, mime_type = encode_image(img_path)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime_type};base64,{data}",
                "detail": "high"
            }
        })
    return [{"role": "user", "content": content}]


def call_llm(client: OpenAI, prompt: str, image_paths: list[str], label: str) -> str:
    """LLMを呼び出してテキストを生成する"""
    print(f"  → {label} を生成中...", flush=True)
    messages = build_messages(prompt, image_paths)
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        max_tokens=4096,
        temperature=0.3,
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────────
# メイン処理
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="画像を解析してA/B/C（デザインシステム・スライドタイプ・コンテンツ原稿）を生成する"
    )
    parser.add_argument(
        "--image", action="append", required=True, metavar="IMAGE_PATH",
        help="解析する画像ファイルのパス（複数指定可）"
    )
    parser.add_argument(
        "--output", required=True, metavar="OUTPUT_DIR",
        help="出力先ディレクトリ"
    )
    args = parser.parse_args()

    # 画像ファイルの存在確認
    for img in args.image:
        if not os.path.exists(img):
            print(f"エラー: 画像ファイルが見つかりません: {img}", file=sys.stderr)
            sys.exit(1)

    # 出力ディレクトリの作成
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # OpenAI クライアントの初期化
    client = OpenAI()

    print(f"\n🔍 画像解析を開始します（{len(args.image)}枚）")
    print(f"📁 出力先: {output_dir}\n")

    # A：デザインシステムの生成
    content_a = call_llm(client, PROMPT_A, args.image, "A：デザインシステム")
    path_a = output_dir / "design_system_A.md"
    path_a.write_text(content_a, encoding="utf-8")
    print(f"  ✅ 保存: {path_a}")

    # B：スライドタイプの生成
    content_b = call_llm(client, PROMPT_B, args.image, "B：スライドタイプ")
    path_b = output_dir / "slide_types_B.md"
    path_b.write_text(content_b, encoding="utf-8")
    print(f"  ✅ 保存: {path_b}")

    # C：コンテンツ原稿の生成
    content_c = call_llm(client, PROMPT_C, args.image, "C：コンテンツ原稿")
    path_c = output_dir / "content_draft_C.md"
    path_c.write_text(content_c, encoding="utf-8")
    print(f"  ✅ 保存: {path_c}")

    print(f"\n🎉 完了！3ファイルを生成しました:")
    print(f"   A: {path_a}")
    print(f"   B: {path_b}")
    print(f"   C: {path_c}")


if __name__ == "__main__":
    main()
