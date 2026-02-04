import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # APIキーを設定
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
        page = context.new_page()

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

            # --- Gemini分析セクション (二段構え) ---
            print("Geminiが分析を実行しています...")
            
            # 試行するモデル名のリスト
            model_names = ["gemini-1.5-flash", "models/gemini-1.5-flash"]
            response_text = ""

            for name in model_names:
                try:
                    print(f"モデル名 '{name}' で試行中...")
                    model = genai.GenerativeModel(name)
                    response = model.generate_content(f"以下のMEOデータを日本語で要約して:\n\n{page_content}")
                    response_text = response.text
                    break # 成功したらループを抜ける
                except Exception as e:
                    print(f"モデル '{name}' は失敗しました。次の候補を試します。")
                    continue

            if not response_text:
                raise Exception("すべてのモデル名で404エラーが発生しました。APIキーの権限を確認してください。")

            # GASへ送信
            print("結果を送信します...")
            requests.post(os.environ["GAS_URL"], json={"message": response_text})
            print("すべて完了しました！ついに成功です！")

        except Exception as e:
            print(f"エラー発生: {e}")
            page.screenshot(path="debug_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
