import os
import requests
# ライブラリを変更: google.generativeai ではなく google.genai を使用
from google import genai
from playwright.sync_api import sync_playwright

def run_agent():
    # 最新のクライアント設定
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    model_id = "gemini-1.5-flash"

    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0")
        page = context.new_page()

        print("MEOダッシュボードへ移動中...")
        page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")

        try:
            # ログイン（これまで成功している手順）
            page.wait_for_timeout(5000)
            inputs = page.query_selector_all('input[type="email"], input[type="text"], input[type="password"]')
            if len(inputs) >= 2:
                print("ログイン中...")
                inputs[0].fill(os.environ["GOOGLE_ID"])
                inputs[1].fill(os.environ["GOOGLE_PW"])
                page.click('button:has-text("ログイン"), input[type="submit"]')
            
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(15000) 

            # 直接テキスト抽出
            print("テキストを抽出して分析開始...")
            page_content = page.inner_text('body')

            # 最新の分析実行コマンド
            print("Geminiが分析を実行しています...")
            response = client.models.generate_content(
                model=model_id,
                contents=f"以下のMEOデータを日本語で要約して報告してください:\n\n{page_content}"
            )

            # GASへ送信
            print("スプレッドシートへ送信中...")
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("すべて完了しました！成功です。")

        except Exception as e:
            print(f"エラー発生: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
