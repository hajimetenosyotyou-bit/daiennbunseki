import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # Gemini設定
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    with sync_playwright() as p:
        print("ブラウザを起動します...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0")
        page = context.new_page()

        print("MEOダッシュボードへ直接アクセス中...")
        page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")

        try:
            # 【新機能】画面上のすべての入力欄を取得して、1番目にID、2番目にPWを入れる
            print("入力フォームを強制特定中...")
            page.wait_for_timeout(5000) # 読み込みを待つ
            inputs = page.query_selector_all('input[type="email"], input[type="text"], input[type="password"]')
            
            if len(inputs) >= 2:
                print(f"{len(inputs)}個の入力欄を検出。ログインを試みます。")
                inputs[0].fill(os.environ["GOOGLE_ID"])
                inputs[1].fill(os.environ["GOOGLE_PW"])
                # 送信ボタンを「ログイン」という文字から探してクリック
                page.click('button:has-text("ログイン"), input[type="submit"], .btn-primary')
            else:
                # 予備の探し方
                page.fill('input[name*="user"]', os.environ["GOOGLE_ID"])
                page.fill('input[type="password"]', os.environ["GOOGLE_PW"])
                page.click('input[type="submit"]')

            print("ログイン後のデータ取得中...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(15000) # グラフ描画をしっかり待つ

            # 【重要】撮影せず、テキストデータを直接抜き出す
            print("画面のテキスト情報を直接抽出中...")
            page_content = page.inner_text('body')

            # Geminiにテキストを丸投げして分析
            print("Geminiがデータを直接分析しています...")
            prompt = f"以下のMEOダッシュボードのテキストデータから、主要な数値（検索数、閲覧数など）を抜き出し、日本語で簡潔に報告してください。\n\nデータ内容:\n{page_content}"
            response = model.generate_content(prompt)

            # 送信
            print(f"分析結果を送信します: {response.text[:50]}...")
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("スプレッドシートへの送信が完了しました！")

        except Exception as e:
            print(f"失敗しました: {e}")
            # エラー時のみ、何が起きていたか撮影
            page.screenshot(path="debug_final.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
