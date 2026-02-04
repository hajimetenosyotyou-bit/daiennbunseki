import os
import requests
from google import genai
from playwright.sync_api import sync_playwright

def run_agent():
    # Gemini 2.0 Flash を使用する設定
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options={'api_version': 'v1'}
    )
    
    with sync_playwright() as p:
        print("ブラウザ起動中（人間モード）...")
        # 画面サイズを一般的（PCサイズ）にして、ボット判定を回避
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            print("MEOダッシュボードへ移動...")
            page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")

            # 1. ページが完全に描画されるまで少し待つ
            page.wait_for_timeout(5000)

            # 2. セレクターをあいまいにせず、ログインID欄を特定してクリック
            print("ログイン情報を入力中...")
            # email, user, id など、何らかの入力欄が出るまで待つ
            page.wait_for_selector("input", timeout=10000)
            
            inputs = page.query_selector_all('input')
            # 画面に見えている入力欄だけを抽出
            visible_inputs = [i for i in inputs if i.is_visible()]

            if len(visible_inputs) >= 2:
                # 1つ目にID、2つ目にパスワードを丁寧に入力
                visible_inputs[0].click()
                visible_inputs[0].fill(os.environ["GOOGLE_ID"])
                page.wait_for_timeout(1000)
                
                visible_inputs[1].click()
                visible_inputs[1].fill(os.environ["GOOGLE_PW"])
                page.wait_for_timeout(1000)
                
                # Enterキーを叩く
                page.keyboard.press("Enter")
            else:
                # 予備：もしinputで見つからない場合、名前(name)で探す
                page.fill('input[name*="email"]', os.environ["GOOGLE_ID"])
                page.fill('input[name*="password"]', os.environ["GOOGLE_PW"])
                page.keyboard.press("Enter")
            
            print("ログイン成功。データの読み込みを待機（25秒）...")
            page.wait_for_timeout(25000) 

            # 3. テキスト抽出
            page_content = page.inner_text('body')

            # 4. Gemini 2.0 Flash で分析
            print("Gemini 2.0 Flash で分析実行...")
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"以下のMEOデータを日本語で要約して報告してください。:\n\n{page_content}"
            )

            # 5. GASへ送信
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("【祝】すべての工程が完了しました！")

        except Exception as e:
            print(f"エラー発生: {e}")
            # 失敗した時の画面を保存（デバッグ用）
            page.screenshot(path="login_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
