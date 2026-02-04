import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # Gemini 1.5 Flash の設定
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # 1. MEOダッシュボードのログイン画面へ
        print("MEOダッシュボードへ移動中...")
        page.goto("https://app.meo-dash.com/users/sign_in")

        # 2. IDとパスワードを入力
        print("ログイン情報を入力中...")
        page.fill('input[type="email"]', os.environ["GOOGLE_ID"]) # ここにIDが入ります
        page.fill('input[type="password"]', os.environ["GOOGLE_PW"]) # ここにパスが入ります
        
        # 3. ログインボタンをクリック
        # ボタンの名称が「ログイン」や「サインイン」であることを想定
        page.click('input[type="submit"]') 

        # 4. ログイン後の画面表示を待つ
        print("ダッシュボード読み込み中...")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(5000) # 画面が安定するまで少し待機

        # 5. スクリーンショット撮影
        print("解析用データを撮影中...")
        screenshot_path = "evidence.png"
        page.screenshot(path=screenshot_path, full_page=True)

        # 6. AIで分析
        print("Geminiが分析を開始...")
        sample_file = genai.upload_file(path=screenshot_path)
        prompt = "このMEOダッシュボードの数値を読み取り、日本語で短く要約してください。"
        response = model.generate_content([sample_file, prompt])
        
        # 7. スプレッドシート（GAS）へ送信
        print("スプレッドシートへ送信中...")
        requests.post(os.environ["GAS_URL"], json={"message": response.text})
        
        browser.close()
        print("すべての工程が完了しました！")

if __name__ == "__main__":
    run_agent()
