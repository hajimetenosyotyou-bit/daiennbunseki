import os
import requests
from google import genai # インストールされていればエラーになりません
from playwright.sync_api import sync_playwright

def run_agent():
    # 1. APIクライアントの設定 (最新の google-genai 方式)
    try:
        client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"],
            http_options={'api_version': 'v1'}
        )
    except Exception as e:
        print(f"クライアント作成失敗: {e}")
        return

    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # ログイン処理 (ここは今まで成功していたので維持)
            page.goto("https://app.meo-dash.com/users/sign_in")
            page.wait_for_timeout(5000)
            inputs = page.query_selector_all('input')
            if len(inputs) >= 2:
                inputs[0].fill(os.environ["GOOGLE_ID"])
                inputs[1].fill(os.environ["GOOGLE_PW"])
                page.keyboard.press("Enter")
            
            page.wait_for_timeout(15000)
            page_content = page.inner_text('body')

            # 2. API呼び出しテスト
            print("Gemini API (v1) に接続を試みます...")
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=f"以下の情報を短くまとめて:\n\n{page_content}"
            )

            # 3. 成功ならGASへ送信
            print("API応答あり。結果を送信します。")
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("【祝】すべて完了しました！")

        except Exception as e:
            # ここで 404 が出たら、APIキーのプロジェクト設定に問題があります
            print(f"実行中にエラーが発生しました: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
