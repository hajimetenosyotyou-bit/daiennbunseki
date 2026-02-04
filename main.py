import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # Gemini設定
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')

    with sync_playwright() as p:
        print("ブラウザ起動中...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800}, locale="ja-JP")
        page = context.new_page()
        page.set_default_timeout(90000)

        print("Googleログイン画面へ...")
        page.goto("https://accounts.google.com/v3/signin/identifier?continue=https://business.google.com/locations")
        
        # ID入力
        page.fill('input[type="email"]', os.environ["GOOGLE_ID"])
        page.click('#identifierNext')
        
        # パスワード入力
        print("パスワード入力中...")
        page.wait_for_selector('input[type="password"]', state="visible")
        page.fill('input[type="password"]', os.environ["GOOGLE_PW"])
        page.click('#passwordNext')

        # --- ここから数字を探す処理 ---
        print("本人確認待ち... 画面をスキャンしています。")
        page.wait_for_timeout(10000) # 10秒待機

        # 画面上の「大きな数字」を探してログに出す
        try:
            # Googleの認証画面に現れる数字の候補をすべて取得
            potential_numbers = page.query_selector_all('div[data-number]')
            if potential_numbers:
                for num in potential_numbers:
                    print(f"★スマホで選ぶ数字はこれかも知れません: {num.get_attribute('data-number')}")
            
            # 別の形式（テキスト）で数字が出ている場合
            main_text = page.inner_text('body')
            print("--- 画面内のテキスト抜粋 ---")
            # 2桁の数字っぽいものを探して表示（簡易版）
            import re
            numbers = re.findall(r'\b\d{2}\b', main_text)
            if numbers:
                print(f"★見つかった2桁の数字候補: {', '.join(numbers)}")
            print("----------------------------")

        except Exception as e:
            print(f"数字の取得中にエラー（無視して続行）: {e}")

        # 認証が終わるのを待つ
        print("スマホを操作してください。認証完了を待っています...")
        page.wait_for_url("https://business.google.com/locations", timeout=120000)
        
        # --- 以降、通常処理 ---
        print("撮影完了")
        screenshot_path = "evidence.png"
        page.screenshot(path=screenshot_path)

        sample_file = genai.upload_file(path=screenshot_path)
        response = model.generate_content([sample_file, "数値を日本語で短く要約してください。"])
        requests.post(os.environ["GAS_URL"], json={"message": response.text})
        
        browser.close()
        print("成功しました！")

if __name__ == "__main__":
    run_agent()
