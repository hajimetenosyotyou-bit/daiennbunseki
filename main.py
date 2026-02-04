import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # Gemini 1.5 Flash の最新モデル名を指定（404エラー対策）
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    with sync_playwright() as p:
        print("ブラウザを起動中...")
        # Googleに「普通の人間」だと思わせるための設定
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            locale="ja-JP"
        )
        page = context.new_page()
        page.set_default_timeout(90000)

        print("Googleログイン画面へ移動...")
        page.goto("https://accounts.google.com/v3/signin/identifier?continue=https://business.google.com/locations")
        
        # ID入力
        page.fill('input[type="email"]', os.environ["GOOGLE_ID"])
        page.click('#identifierNext')
        
        # パスワード入力
        print("パスワードを入力中...")
        page.wait_for_selector('input[type="password"]', state="visible")
        page.fill('input[type="password"]', os.environ["GOOGLE_PW"])
        page.click('#passwordNext')

        print("認証待ち... スマホを確認してください。")
        # 画面上のテキストをスキャンして数字を探す
        page.wait_for_timeout(10000) 
        try:
            body_text = page.inner_text('body')
            import re
            numbers = re.findall(r'\b\d{2}\b', body_text)
            if numbers:
                print(f"★★★ スマホで選ぶ数字はこれです： {numbers[0]} ★★★")
            else:
                print("画面内に2桁の数字が見つかりませんでした。")
        except:
            pass

        # ログイン成功を最大2分待機
        try:
            page.wait_for_url("**/locations**", timeout=120000)
            print("ログイン成功！")
        except:
            print("タイムアウトしました。スマホに通知が来ていないか、別の確認画面が出ている可能性があります。")
            page.screenshot(path="error_screen.png")

        # 撮影と分析
        print("最終画面を撮影中...")
        screenshot_path = "evidence.png"
        page.screenshot(path=screenshot_path)

        print("Geminiが分析を開始...")
        sample_file = genai.upload_file(path=screenshot_path)
        response = model.generate_content([sample_file, "この店舗の数値を日本語で短く要約してください。"])
        
        requests.post(os.environ["GAS_URL"], json={"message": response.text})
        browser.close()
        print("全工程が完了しました！")

if __name__ == "__main__":
    run_agent()
