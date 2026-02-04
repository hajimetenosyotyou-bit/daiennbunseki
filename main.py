import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # シンプルに設定
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    
    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("MEOダッシュボードへ移動中...")
        page.goto("https://app.meo-dash.com/users/sign_in", wait_until="load")

        try:
            page.wait_for_timeout(5000)
            print("ログイン情報を入力中...")
            inputs = page.query_selector_all('input')
            target_inputs = [i for i in inputs if i.is_visible()]
            
            if len(target_inputs) >= 2:
                target_inputs[0].fill(os.environ["GOOGLE_ID"])
                target_inputs[1].fill(os.environ["GOOGLE_PW"])
                login_button = page.query_selector('button:has-text("ログイン"), input[type="submit"]')
                if login_button: login_button.click()
                else: page.keyboard.press("Enter")
            
            print("ログイン成功！データ読み込み中...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(20000) 

            print("テキストを抽出中...")
            page_content = page.inner_text('body')

            # --- 最も標準的なGemini 1.5 Flashの呼び出し ---
            print("Geminiにデータを送信中...")
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(f"以下のMEOデータを日本語で要約して:\n\n{page_content}")

            # GASへ送信
            print("結果を送信します...")
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("【祝】すべて完了しました！成功です！")

        except Exception as e:
            print(f"エラー発生: {e}")
            page.screenshot(path="debug_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
