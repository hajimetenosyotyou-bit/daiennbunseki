import os
import requests
from google import genai
from playwright.sync_api import sync_playwright

def run_agent():
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options={'api_version': 'v1'}
    )
    
    with sync_playwright() as p:
        print("ブラウザ起動...")
        browser = p.chromium.launch(headless=True)
        # 人間らしく振る舞うためのコンテキスト設定
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            print("ログインページへ移動...")
            page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")

            # 1. 隠し要素(hidden)ではない、本物の入力欄を特定する
            # 'email' という単語が含まれる、かつ「表示されている」入力欄を探す
            print("入力欄をスキャン中...")
            
            # メールアドレス入力欄を探して入力
            email_field = page.locator('input[type="email"], input[name*="email"], input[id*="email"]').filter(filtered_by=lambda e: e.is_visible()).first
            email_field.wait_for(timeout=10000)
            email_field.fill(os.environ["GOOGLE_ID"])
            
            # パスワード入力欄を探して入力
            password_field = page.locator('input[type="password"], input[name*="password"]').filter(filtered_by=lambda e: e.is_visible()).first
            password_field.fill(os.environ["GOOGLE_PW"])
            
            print("ログイン実行...")
            page.keyboard.press("Enter")
            
            # 2. ログイン後のデータ読み込みを待つ
            print("データ読み込み待ち（25秒）...")
            page.wait_for_timeout(25000) 

            # 3. ページ全体のテキストを抽出
            page_content = page.inner_text('body')

            # 4. Gemini 2.0 Flash で要約
            print("Gemini 2.0 Flash で要約中...")
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"以下のMEOデータを日本語で要約して報告してください。:\n\n{page_content}"
            )

            # 5. GAS経由でスプレッドシートへ
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("【祝】すべての処理が完了しました！")

        except Exception as e:
            print(f"エラー発生: {e}")
            # どこで止まったか視覚的に確認するための保存
            page.screenshot(path="debug_login.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
