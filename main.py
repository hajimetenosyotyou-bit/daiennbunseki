import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # Geminiの設定
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

    with sync_playwright() as p:
        print("Googleにログイン中...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # Googleログイン処理
        page.goto("https://accounts.google.com/")
        page.fill('input[type="email"]', os.environ["GOOGLE_ID"])
        page.click('#identifierNext')
        page.wait_for_selector('input[type="password"]')
        page.fill('input[type="password"]', os.environ["GOOGLE_PW"])
        page.click('#passwordNext')
        page.wait_for_load_state('networkidle')

        print("ダッシュボードへ移動中...")
        # ビジネスプロフィールのURLへ（ここはご自身の環境に合わせて調整が必要な場合があります）
        page.goto("https://business.google.com/locations")
        page.wait_for_timeout(5000)
        
        print("撮影完了")
        screenshot_path = "evidence.png"
        page.screenshot(path=screenshot_path)

        print("AIが解析中...")
        # 画像を読み込んでGeminiで解析
        sample_file = genai.upload_file(path=screenshot_path, display_name="MEO Screen")
        response = model.generate_content([sample_file, "このGoogleビジネスプロフィールの数値を読み取り、前日との差分や改善点を日本語で短く分析してください。"])
        analysis_result = response.text

        # GASへ送信
        print("スプレッドシートへ送信中...")
        requests.post(os.environ["GAS_URL"], json={"message": analysis_result})
        
        browser.close()
        print("すべての工程が完了しました！")

if __name__ == "__main__":
    run_agent()
