import os
import requests
import google.generativeai as genai # 一旦、安定している古いライブラリに戻します
from playwright.sync_api import sync_playwright

def run_agent():
    # ライブラリの設定をリセットしてシンプルに
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    
    # モデルの存在確認と呼び出し
    model = genai.GenerativeModel('gemini-1.5-flash')

    with sync_playwright() as p:
        print("ブラウザを起動...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # ログイン（ここは成功しているのでそのまま）
            page.goto("https://app.meo-dash.com/users/sign_in")
            page.wait_for_timeout(5000)
            inputs = page.query_selector_all('input')
            if len(inputs) >= 2:
                inputs[0].fill(os.environ["GOOGLE_ID"])
                inputs[1].fill(os.environ["GOOGLE_PW"])
                page.click('input[type="submit"], button[type="submit"]')
            
            page.wait_for_timeout(10000)
            page_content = page.inner_text('body')
            print("テキスト抽出完了。分析を依頼します...")

            # API呼び出し（一番シンプルな書き方）
            response = model.generate_content(f"以下の内容を要約して:\n\n{page_content}")

            print(f"AIの回答: {response.text[:50]}...")
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("完了！")

        except Exception as e:
            print(f"詳細エラー: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
