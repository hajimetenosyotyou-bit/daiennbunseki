import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # APIの設定
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    
    # 404対策：モデル名をフルパスで指定
    model = genai.GenerativeModel('models/gemini-1.5-flash')

    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("MEOダッシュボードへ移動中...")
        page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")

        try:
            # ログイン処理
            page.wait_for_timeout(5000)
            inputs = page.query_selector_all('input')
            if len(inputs) >= 2:
                print("ログイン実行...")
                inputs[0].fill(os.environ["GOOGLE_ID"])
                inputs[1].fill(os.environ["GOOGLE_PW"])
                page.click('input[type="submit"], button[type="submit"]')
            
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(10000) 

            # テキスト抽出
            print("データを抽出してAIに送信中...")
            page_content = page.inner_text('body')

            # 分析実行
            response = model.generate_content(f"以下のMEOデータを要約して報告してください:\n\n{page_content}")

            # GASへ送信
            print(f"結果を送信します: {response.text[:30]}...")
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("すべて完了しました！")

        except Exception as e:
            print(f"エラー発生: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
