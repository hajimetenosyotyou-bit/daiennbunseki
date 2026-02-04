import os
import requests
from google import genai
from playwright.sync_api import sync_playwright

def run_agent():
    # 最新SDKのセットアップ
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options={'api_version': 'v1'}
    )
    
    with sync_playwright() as p:
        print("ブラウザ起動（ログイン成功維持モード）...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            print("ログインページへ移動...")
            page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")
            page.wait_for_timeout(3000)

            print("入力フィールドへID/PWを入力中...")
            visible_inputs = page.locator('input:not([type="hidden"]):visible')
            
            # 前回成功したロジックを維持
            if visible_inputs.count() >= 2:
                visible_inputs.nth(0).fill(os.environ["GOOGLE_ID"])
                visible_inputs.nth(1).fill(os.environ["GOOGLE_PW"])
                page.keyboard.press("Enter")
            
            print("ログイン成功。データ読み込み中（30秒）...")
            page.wait_for_timeout(30000) 

            # データ抽出
            page_content = page.inner_text('body')
            # 念のため、データが空っぽじゃないか確認
            print(f"取得したテキスト量: {len(page_content)}文字")
            
            # 429対策：長すぎる場合はカット
            clean_text = " ".join(page_content.split())[:10000] 

            # --- ここが修正ポイント ---
            print("Gemini API で要約実行中...")
            # モデル名の指定を 'gemini-1.5-flash' に統一（models/ は不要）
            response = client.models.generate_content(
                model="gemini-1.5-flash", 
                contents=f"以下のMEOデータを日本語で数値を中心に要約してください:\n\n{clean_text}"
            )

            # GASへ送信
            if response.text:
                requests.post(os.environ["GAS_URL"], json={"message": response.text})
                print("【祝】スプレッドシートへ送信完了しました！")
            else:
                print("Geminiからの返答が空でした。")

        except Exception as e:
            print(f"エラー発生: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
