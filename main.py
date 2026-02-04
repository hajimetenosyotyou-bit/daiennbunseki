import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # 修正ポイント: APIキーの設定とモデル名の指定
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    
    # 最も安定しているモデル名を指定
    model = genai.GenerativeModel("gemini-1.5-flash")

    with sync_playwright() as p:
        print("ブラウザを起動します...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0")
        page = context.new_page()

        print("MEOダッシュボードへ直接アクセス中...")
        page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")

        try:
            print("入力フォームを強制特定中...")
            page.wait_for_timeout(5000)
            inputs = page.query_selector_all('input[type="email"], input[type="text"], input[type="password"]')
            
            if len(inputs) >= 2:
                print(f"{len(inputs)}個の入力機を検出。ログインを試みます。")
                inputs[0].fill(os.environ["GOOGLE_ID"])
                inputs[1].fill(os.environ["GOOGLE_PW"])
                page.click('button:has-text("ログイン"), input[type="submit"], .btn-primary')
            else:
                print("予備の入力方法を実行...")
                page.fill('input[name*="email"]', os.environ["GOOGLE_ID"])
                page.fill('input[type="password"]', os.environ["GOOGLE_PW"])
                page.click('input[type="submit"]')

            print("ログイン後のデータ取得中...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(15000) 

            # 【撮影せず直接分析】テキスト情報を抽出
            print("画面のテキスト情報を直接抽出中...")
            page_content = page.inner_text('body')

            # Geminiで分析（ここがエラーの場所でした）
            print("Geminiがテキストデータを直接分析しています...")
            prompt = f"以下のMEOダッシュボードのテキストから、主要な数値（検索数、閲覧数など）を抜き出し、日本語で簡潔に報告してください。\n\nデータ:\n{page_content}"
            
            # 安全に生成を実行
            response = model.generate_content(prompt)

            # GAS経由でスプレッドシートへ送信
            print(f"分析結果を送信します: {response.text[:50]}...")
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("スプレッドシートへの送信が完了しました！")

        except Exception as e:
            print(f"エラー発生: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
