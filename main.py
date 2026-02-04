import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    # Gemini設定（最新の安定版モデルを使用）
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    with sync_playwright() as p:
        print("ブラウザを起動します（Googleにはアクセスしません）")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # 【重要】Googleではなく、直接MEOダッシュボードのログインページへ行く
        print("目標URL: https://app.meo-dash.com/users/sign_in へ移動中...")
        page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")

        try:
            # メアド入力枠が出るまで最大30秒待つ
            page.wait_for_selector('input[name="user[email]"]', timeout=30000)
            
            print("MEOダッシュボードのID/パスワードを入力中...")
            # MEOチェキ専用の入力項目名に合わせて指定
            page.fill('input[name="user[email]"]', os.environ["GOOGLE_ID"]) # Secretsの中身(hikaruoota11)
            page.fill('input[name="user[password]"]', os.environ["GOOGLE_PW"]) # Secretsの中身(nyanntarunn)
            
            print("ログインボタンをクリック...")
            page.click('input[name="commit"]') 

            # ログイン後のダッシュボード画面が表示されるのを待つ
            print("ログイン後の画面を読み込み中...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(10000) # グラフなどが表示されるまで10秒待つ
            
            # 撮影
            screenshot_path = "meo_report.png"
            page.screenshot(path=screenshot_path, full_page=True)
            print("撮影完了。AIによる分析を開始します。")

            # AI分析
            sample_file = genai.upload_file(path=screenshot_path)
            response = model.generate_content([sample_file, "このMEOレポートの数値を読み取り、日本語で短く要約してください。"])
            
            # スプレッドシートへ送信
            print("スプレッドシート（f1836014のアカウントが持つシート）へ結果を送信中...")
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            
            print("すべて完了しました！成功です。")

        except Exception as e:
            print(f"途中でエラーが発生しました: {e}")
            # どこで止まったか確認するために証拠写真を撮る
            page.screenshot(path="error_at_meo.png")

        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
