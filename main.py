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
        print("ブラウザ起動（精密射撃モード）...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            print("ダッシュボードへ移動...")
            page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")
            
            # 1. 「隠し要素」を無視し、名前で直接指定（これが最も確実です）
            print("IDとパスワードを精密に入力中...")
            
            # メールアドレス（Railsの標準的なname属性 [user][email] を狙う）
            page.locator('input[name*="email"]').first.fill(os.environ["GOOGLE_ID"])
            
            # パスワード
            page.locator('input[name*="password"]').first.fill(os.environ["GOOGLE_PW"])
            
            # ログインボタンをクリック
            page.keyboard.press("Enter")
            
            print("ログイン成功。データ読み込み中（30秒）...")
            page.wait_for_timeout(30000) 

            # 2. データの抽出（APIパンク防止のため15,000文字に制限）
            raw_text = page.inner_text('body')
            clean_text = " ".join(raw_text.split())[:15000] 

            # 3. Gemini 1.5 Flash で分析
            print("Gemini API (v1) で分析実行...")
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=f"以下のMEOデータを日本語で要約して:\n\n{clean_text}"
            )

            # 4. GASへ送信
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("【祝】すべての工程が完了しました！")

        except Exception as e:
            print(f"エラー発生: {e}")
            # 念のため、どこで止まったか画像を残す
            page.screenshot(path="final_debug.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
