import os
import base64
import requests
import json
from playwright.sync_api import sync_playwright
from openai import OpenAI

# 1. 設定情報の読み込み（GitHubのSecretsから取得）
GAS_URL = "https://script.google.com/a/macros/ssu.ac.jp/s/AKfycbwl6Mu0DnTO6JIrgLb2D8MLFqp6o3rPqrfT_mYUWW_4irDp692mhZEg5wfGEOSrDlAVAg/exec"
GOOGLE_ID = os.environ.get("GOOGLE_ID")
GOOGLE_PW = os.environ.get("GOOGLE_PW")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

def run_agent():
    with sync_playwright() as p:
        # ブラウザ起動
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 1200})
        page = context.new_page()

        print("Googleにログイン中...")
        page.goto("https://accounts.google.com/ServiceLogin?hl=ja")
        page.fill('input[type="email"]', GOOGLE_ID)
        page.click('#identifierNext')
        page.wait_for_timeout(3000)
        page.fill('input[type="password"]', GOOGLE_PW)
        page.click('#passwordNext')
        page.wait_for_timeout(10000) 

        print("ダッシュボードへ移動中...")
        # 管理画面のURL
        page.goto("https://business.google.com/locations") 
        page.wait_for_timeout(7000)

        # 撮影
        screenshot_path = "capture.png"
        page.screenshot(path=screenshot_path, full_page=True)
        print("撮影完了")

        # AI解析
        client = OpenAI(api_key=OPENAI_API_KEY)
        with open(screenshot_path, "rb") as f:
            base64_img = base64.b64encode(f.read()).decode('utf-8')
            
        print("AIが解析中...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "画像から『表示回数』『検索数』『合計アクション数』を数値(int)で、考察をinsight(text)としてJSON形式(keys: views, searches, actions, insight)で抽出して。数値のみ返して。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                ]
            }],
            response_format={ "type": "json_object" }
        )
        
        result = json.loads(response.choices[0].message.content)
        print(f"解析結果: {result}")

        # GASに送信
        response_gas = requests.post(GAS_URL, json=result)
        print(f"GAS送信結果: {response_gas.status_code}")

if __name__ == "__main__":
    run_agent()
