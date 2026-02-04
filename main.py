import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

    with sync_playwright() as p:
        print("Googleにログイン中...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # タイムアウトを60秒に延長
        page.set_default_timeout(60000)

        page.goto("https://accounts.google.com/")
        page.fill('input[type="email"]', os.environ["GOOGLE_ID"])
        page.click('#identifierNext')
        
        # 画面が変わるのをしっかり待つ
        page.wait_for_selector('input[type="password"]', state="visible")
        page.fill('input[type="password"]', os.environ["GOOGLE_PW"])
        page.click('#passwordNext')
        
        # ログイン完了を最大60秒待つ
        page.wait_for_load_state('networkidle')

        print("ダッシュボードへ移動中...")
        page.goto("https://business.google.com/locations")
        page.wait_for_timeout(10000) # 10秒じっくり待つ
        
        print("撮影完了")
        screenshot_path = "evidence.png"
        page.screenshot(path=screenshot_path)

        print("AIが解析中...")
        sample_file = genai.upload_file(path=screenshot_path)
        response = model.generate_content([sample_file, "このGoogleビジネスプロフィールの数値を読み取り、日本語で短く分析してください。"])
        analysis_result = response.text

        print("スプレッドシートへ送信中...")
        requests.post(os.environ["GAS_URL"], json={"message": analysis_result})
        
        browser.close()
        print("すべての工程が完了しました！")

if __name__ == "__main__":
    run_agent()
