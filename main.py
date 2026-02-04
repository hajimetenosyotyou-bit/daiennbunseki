import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # APIの設定
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    
    # 【重要】ここが404対策のキモです
    # 古いライブラリでも、強制的に本番用窓口(v1)を使うように指定します
    from google.generativeai.types import RequestOptions
    options = RequestOptions(api_version='v1')
    
    # モデル名を指定
    model = genai.GenerativeModel('gemini-1.5-flash')

    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("MEOダッシュボードへ移動中...")
        page.goto("https://app.meo-dash.com/users/sign_in")

        try:
            # ログイン成功時の方法を維持
            page.wait_for_timeout(5000)
            print("ログイン情報を入力中...")
            
            inputs = page.query_selector_all('input')
            if len(inputs) >= 2:
                inputs[0].fill(os.environ["GOOGLE_ID"])
                inputs[1].fill(os.environ["GOOGLE_PW"])
                page.keyboard.press("Enter")
            
            print("ログイン成功！データ読み込み中...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(20000) 

            # テキスト抽出
            print("データを抽出中...")
            page_content = page.inner_text('body')

            # 【修正】分析実行時に RequestOptions を渡す
            print("Gemini (v1) で分析中...")
            response = model.generate_content(
                f"以下のMEOデータを日本語で要約して報告してください。:\n\n{page_content}",
                request_options=options  # これで v1beta ではなく v1 に繋がります
            )

            # GASへ送信
            print("結果を送信します...")
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("【祝】すべて完了しました！")

        except Exception as e:
            print(f"エラー発生: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
