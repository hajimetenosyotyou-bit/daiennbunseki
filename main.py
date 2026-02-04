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
        print("ブラウザ起動（完全自動モード）...")
        browser = p.chromium.launch(headless=True)
        # 画面サイズを固定
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            print("ログインページへ移動...")
            page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")
            page.wait_for_timeout(8000) # 完全に読み込むまで8秒待機

            print("キーボード入力開始（Tab連打作戦）...")
            # 1. 一度画面をクリックしてフォーカスを合わせる
            page.mouse.click(640, 400)
            
            # 2. Tabキーを数回押して、確実に最初の入力欄（ID）へ移動
            # サイトによって1回か2回か異なるため、念のためTab後に全選択して上書き
            for _ in range(3): page.keyboard.press("Tab")
            
            # 3. ID入力
            page.keyboard.type(os.environ["GOOGLE_ID"], delay=100)
            page.wait_for_timeout(1000)
            
            # 4. 次の入力欄（PW）へ移動
            page.keyboard.press("Tab")
            page.keyboard.type(os.environ["GOOGLE_PW"], delay=100)
            page.wait_for_timeout(1000)
            
            # 5. ログイン実行
            print("Enterキーでログイン実行...")
            page.keyboard.press("Enter")
            
            # 6. 遷移をじっくり待つ
            print("データ読み込み待ち（30秒）...")
            page.wait_for_timeout(30000) 

            # 7. データの抽出と判定
            page_content = page.inner_text('body')
            if "ログイン" in page_content[:100]:
                print("警告: まだログイン画面のようです。")

            # Gemini 2.0 Flash で要約
            print("Gemini 2.0 Flash で要約中...")
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"以下のMEOデータを日本語で要約して報告してください。:\n\n{page_content}"
            )

            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("【祝】全工程を強引に完了させました！")

        except Exception as e:
            print(f"エラー発生: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
