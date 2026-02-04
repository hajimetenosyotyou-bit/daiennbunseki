import os
import requests
from google import genai
from playwright.sync_api import sync_playwright

def run_agent():
    # 制限の少ない 1.5-flash 用に設定
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options={'api_version': 'v1'}
    )
    
    with sync_playwright() as p:
        print("ブラウザ起動...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            print("ログインページへ移動...")
            page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")
            page.wait_for_timeout(5000)

            # 強制入力
            print("ログイン情報を直接指定して入力...")
            # セレクターを極限までシンプルに
            page.type('input[type="email"]', os.environ["GOOGLE_ID"], delay=50)
            page.type('input[type="password"]', os.environ["GOOGLE_PW"], delay=50)
            page.keyboard.press("Enter")
            
            print("遷移待ち...")
            page.wait_for_timeout(20000) 

            page_content = page.inner_text('body')
            
            # 【重要】もしログイン画面のままなら、その理由をログに出す
            if "ログイン" in page_content[:50]:
                print("--- ログイン失敗時の画面内容 (先頭200文字) ---")
                print(page_content[:200])
                print("------------------------------------------")

            print("Gemini 1.5 Flash で分析開始...")
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=f"以下のテキストを要約して:\n\n{page_content}"
            )

            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("完了！")

        except Exception as e:
            print(f"実行エラー: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
