import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # Gemini 1.5 Flash の設定
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0")
        page = context.new_page()

        print("MEOダッシュボードへ移動...")
        page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")

        try:
            # ログイン処理（網を広げて探す設定を継続）
            print("ログイン情報を入力中...")
            page.wait_for_selector('input[name*="email"], input[type="email"]', timeout=30000)
            page.fill('input[name*="email"], input[type="email"]', os.environ["GOOGLE_ID"])
            page.fill('input[type="password"]', os.environ["GOOGLE_PW"])
            page.click('input[type="submit"], button[type="submit"]')

            # ログイン後のデータ読み込み待ち
            print("ダッシュボードのデータを読み込み中...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(10000) # グラフや表が確定するまで待機

            # 【ここが重要】撮影ではなく、画面上の「全テキスト」を取得
            print("画面上のテキストデータを抽出しています...")
            all_text = page.inner_text('body') 

            # AIにテキストデータを渡して分析
            print("Geminiがテキストデータを直接分析中...")
            prompt = f"""
            以下のMEOダッシュボードから抽出されたテキストデータから、
            「検索数」「閲覧数」「アクション数（通話やルート）」などの主要な数値を抜き出し、
            日本語で分かりやすく要約してスプレッドシート形式の報告文を作成してください。
            
            データ内容:
            {all_text}
            """
            
            response = model.generate_content(prompt)
            print(f"分析完了: {response.text[:100]}...") # 冒頭だけ表示

            # スプレッドシートへ送信
            print("結果をスプレッドシートへ送信中...")
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("完了しました！")

        except Exception as e:
            print(f"エラー発生: {e}")
            # トラブル時のみ、状況確認用に撮影して保存
            page.screenshot(path="debug_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
