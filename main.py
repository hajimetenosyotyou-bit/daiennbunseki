import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # APIの設定
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('models/gemini-1.5-flash')

    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        # 画面サイズを少し大きくして要素を見つけやすくします
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        print("MEOダッシュボードへ移動中...")
        page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")

        try:
            # 入力欄が「見える状態」になるまで最大30秒待ちます
            print("入力欄が表示されるのを待っています...")
            email_selector = 'input[name*="email"], input[type="email"], input[id*="email"]'
            page.wait_for_selector(email_selector, state="visible", timeout=30000)
            
            # 入力欄を特定して入力
            inputs = page.query_selector_all(email_selector)
            pw_inputs = page.query_selector_all('input[type="password"]')
            
            if inputs and pw_inputs:
                print("ログイン情報を入力中...")
                inputs[0].fill(os.environ["GOOGLE_ID"])
                pw_inputs[0].fill(os.environ["GOOGLE_PW"])
                
                # ログインボタンをクリック（確実に「ボタン」として認識させる）
                page.click('input[type="submit"], button[type="submit"], .btn-primary')
            else:
                raise Exception("入力欄が見つかりませんでした。")

            print("ログイン成功。データの読み込みを待機（20秒）...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(20000) # ダッシュボードの描画時間を十分に確保

            # テキスト抽出
            print("データを抽出してAIに送信中...")
            page_content = page.inner_text('body')

            # 分析実行
            response = model.generate_content(f"以下のMEOデータを日本語で要約して報告してください:\n\n{page_content}")

            # GASへ送信
            print(f"分析結果を送信します: {response.text[:30]}...")
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("すべて完了しました！ついに成功です！")

        except Exception as e:
            print(f"エラー発生: {e}")
            # エラー時の画面を保存（デバッグ用）
            page.screenshot(path="debug_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
