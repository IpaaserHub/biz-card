import os
import time
import base64
from dotenv import load_dotenv

load_dotenv()

# Check for OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class OCRService:
    def __init__(self):
        if OPENAI_API_KEY:
            import openai
            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
            print("OCR Service: OpenAI API Mode Enabled.")
        else:
            self.client = None
            print("OCR Service: Running in Mock/Demo Mode (No OpenAI API Key found).")

    def analyze(self, image_paths, template_content=None):
        print(f"Analyzing images: {image_paths}, Template: {'Yes' if template_content else 'No'}")
        
        # Ensure input is a list
        if isinstance(image_paths, str):
            image_paths = [image_paths]

        if self.client:
            return self._analyze_with_openai(image_paths, template_content)
        else:
            return self._analyze_mock(image_paths, template_content)

    def _analyze_with_openai(self, image_paths, template_content=None):
        try:
            content_images = []
            for path in image_paths:
                with open(path, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    content_images.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    })

            instruction = "1. Extract all text from them accurately, combining information from both sides. 2. Draft a polite follow-up email in Japanese based on the extracted info."
            if template_content:
                instruction += f"\n\nIMPORTANT: Use the following template for the draft:\n---\n{template_content}\n---\nReplace placeholders like [Name] with extracted info."

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts information from business cards and drafts a follow-up email."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Here are images of a business card. {instruction} Return JSON with keys 'text' and 'draft'."},
                        *content_images
                    ]
                }
            ]

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={ "type": "json_object" }
            )
            
            import json
            content = json.loads(response.choices[0].message.content)
            return content

        except Exception as e:
            print(f"OpenAI API Error: {e}")
            return {"text": f"Error: {str(e)}", "draft": "API Error occurred."}

    def _analyze_mock(self, image_paths, template_content=None):
        # Simulate processing time
        time.sleep(1.5)
        
        text = """(デモ抽出結果)
株式会社サンプル
代表取締役 田中 太郎

〒100-0001
東京都千代田区千代田1-1-1
TEL: 03-1283-XXXX
Email: taro.sample@example.com"""
        
        if template_content:
            draft = f"(テンプレート適用済み)\n{template_content}\n\n(※実際のAPIモードでは、ここにAIが抽出した名前などが埋め込まれます)" 
        else:
            draft = """件名: 名刺交換のお礼

株式会社サンプル
田中 太郎 様

平素より大変お世話になっております。
[あなたの名前]です。

本日はお忙しい中、名刺交換のお時間をいただき誠にありがとうございました。
田中様のお話を伺い、大変勉強になりました。

今後とも良きお付き合いをさせていただければ幸いです。
引き続き何卒よろしくお願い申し上げます。

--------------------------------------------------
[あなたの署名]
--------------------------------------------------"""
        
        # Add a note about API Key
        text += "\n\n[INFO] OpenAI APIキーが設定されていないため、デモデータを表示しています。.envファイルにキーを設定すると、実際の画像解析が可能になります。"
        
        return {
            "text": text,
            "draft": draft
        }

    def _generate_draft(self, text):
        # Deprecated in favor of LLM generation
        pass
