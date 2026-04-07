# biz-card

名刺管理と営業支援のためのツールキットです。

## 機能一覧

### 名刺解析（Business Card Analyzer）
名刺画像をOCRで読み取り、情報を抽出してフォローアップメールのドラフトを自動生成します。

### 営業支援ワークフロー（Sales Workflow）
営業活動の事前準備から事後振り返りまでを一貫してサポートするスキルです。以下の3つのフェーズで構成されています。

| フェーズ | 内容 | テンプレート |
|---------|------|-------------|
| 1. リサーチ | 営業先の人物・企業情報を収集し仮説を構築 | `research_template.md` |
| 2. 台本作成 | リサーチ結果をもとに商談の流れを設計 | `script_template.md` |
| 3. フィードバック | 議事録を分析し改善点と次回アクションを提案 | `feedback_template.md` |

### スライドABC生成（Slide ABC Generator）
画像からデザインシステム（A）、スライドタイプ（B）、コンテンツ原稿（C）を自動抽出・生成します。

## ディレクトリ構成

```
biz-card/
├── backend/                  # 名刺解析バックエンド
│   ├── main.py              # FastAPI サーバー
│   ├── ocr_service.py       # OCR サービス
│   ├── templates.py         # テンプレート管理
│   └── templates.json       # テンプレートデータ
├── skills/                   # Manus スキル
│   ├── sales-workflow/      # 営業支援ワークフロー
│   │   ├── SKILL.md
│   │   └── templates/
│   │       ├── research_template.md
│   │       ├── script_template.md
│   │       └── feedback_template.md
│   └── slide-abc-generator/ # スライドABC生成
├── research_template.md      # リサーチテンプレート（単体利用可）
├── script_template.md        # 営業台本テンプレート（単体利用可）
├── feedback_template.md      # フィードバックテンプレート（単体利用可）
├── sales_workflow_design.md  # ワークフロー設計書
└── biz-card-demo.html       # デモページ
```

## セットアップ

### 名刺解析バックエンド

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# .env に OpenAI API キーを設定
uvicorn main:app --reload
```

### 営業支援スキル

`skills/sales-workflow/SKILL.md` を Manus のスキルとして登録することで、営業支援ワークフローを利用できます。
