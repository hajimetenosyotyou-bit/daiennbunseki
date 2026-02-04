import os
import requests
import google.generativeai as genai
from playwright.sync_api import sync_playwright

def run_agent():
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('models/gemini-1.5-flash')

    with sync_playwright() as p:
        print("ブラウザを起動中...")
        browser = p.chromium.launch(headless=True)
        # 確実にPC版として認識させる
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        page = context.new_page()

        print("MEOダッシュボードへ移動中...")
        page.goto("https://app.meo-dash.com/users/sign_in", wait_until="load")

        try:
            # 5秒待ってから、画面上の全入力を取得
            page.wait_for_timeout(5000)
            print("入力フォームを探しています...")
            
            # input要素をすべて取得
            inputs = page.query_selector_all('input')
            
            # 1番目の入力欄にID、2番目にPWを入れる（最も原始的だが確実な方法）
            # もしログインIDと書いてある場所を狙い撃ちしたい場合、その付近のinputを探す
            target_inputs = [i for i in inputs if i.is_visible()]
            
            if len(target_inputs) >= 2:
                print(f"可視状態の入力欄を{len(target_inputs)}個発見。入力を開始します。")
                target_inputs[0].fill(os.environ["GOOGLE_ID"])
                target_inputs[1].fill(os.environ["GOOGLE_PW"])
                
                # ログインボタン（type="submit" または "ログイン" という文字を含むボタン）
                login_button = page.query_selector('button:has-text("ログイン"), input[type="submit"]')
                if login_button:
                    login_button.click()
                else:
                    page.keyboard.press("Enter") # ボタンが見つからなければEnterキー
            else:
                # 最終手段：ID/PWというキーワードで探す
                page.get_by_placeholder("メールアドレス").fill(os.environ["GOOGLE_ID"])
                page.get_by_placeholder("パスワード").fill(os.environ["GOOGLE_PW"])
                page.get_by_role("button", name="ログイン").click()

            print("ログイン後の画面読み込み待ち（20秒）...")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(20000) 

            # テキスト抽出
            print("データを抽出してAIに送信中...")
            page_content = page.inner_text('body')

            # 分析実行
            response = model.generate_content(f"以下のMEOデータを日本語で要約して報告してください:\n\n{page_content}")

            # GASへ送信
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("すべて完了しました！成功です！")

        except Exception as e:
            print(f"エラー発生: {e}")
            page.screenshot(path="debug_error.png") # 失敗時の証拠写真
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
