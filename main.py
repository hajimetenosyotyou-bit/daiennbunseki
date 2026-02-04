import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # APIキーを設定
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    
    # 修正：モデル名をフルネーム(models/...)で指定し、本番用(v1)を指定
    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0")
        page = context.new_page()

        print("MEOダッシュボードへ移動中...")
        page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")

        try:
            # ログイン処理（前回成功した方法）
            page.wait_for_timeout(5000)
            inputs = page.query_selector_all('input[type="email"], input[type="text"], input[type="password"]')
            
            if len(inputs) >= 2:
                print(f"ログイン中...")
                inputs[0].fill(os.environ["GOOGLE_ID"])
                inputs[1].fill(os.environ["GOOGLE_PW"])
                page.click('button:has-text("ログイン"), input[type="submit"]')
            
            # データの読み込み待ち
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(15000) 

            # 直接テキスト抽出
            print("テキストを抽出して分析開始...")
            page_content = page.inner_text('body')

            # 分析実行（ここが修正ポイント！）
            response = model.generate_content(
                f"以下のMEOデータを日本語で要約して:\n\n{page_content}"
            )

            # GASへ送信
            print("スプレッドシートへ送信中...")
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("完了しました！")

        except Exception as e:
            print(f"エラー発生: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
