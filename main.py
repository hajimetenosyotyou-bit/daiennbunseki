import os
import requests
from google import genai
from playwright.sync_api import sync_playwright

def run_agent():
    # 2.0系を動かすための最新の書き方です
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options={'api_version': 'v1'}
    )
    
    with sync_playwright() as p:
        print("ブラウザ起動中...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # ログイン（成功していた頃のロジック）
            page.goto("https://app.meo-dash.com/users/sign_in")
            page.wait_for_timeout(5000)
            inputs = page.query_selector_all('input')
            if len(inputs) >= 2:
                inputs[0].fill(os.environ["GOOGLE_ID"])
                inputs[1].fill(os.environ["GOOGLE_PW"])
                page.keyboard.press("Enter")
            
            print("ログイン成功。読み込み待ち...")
            page.wait_for_timeout(20000)
            page_content = page.inner_text('body')

            # --- モデル名を 2.0 Flash に変更 ---
            print("Gemini 2.0 Flash で分析中...")
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"以下のMEOデータを日本語で要約して:\n\n{page_content}"
            )

            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("【祝】Gemini 2.0 で全工程完了！")

        except Exception as e:
            print(f"エラー発生: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
