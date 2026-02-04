import os
import requests
from google import genai
from playwright.sync_api import sync_playwright

def run_agent():
    # 最新SDKとv1窓口を使用
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options={'api_version': 'v1'}
    )
    
    with sync_playwright() as p:
        print("ブラウザ起動（画像解析に基づく最適化モード）...")
        browser = p.chromium.launch(headless=True)
        # スクリーンショットと同じ解像度に近い設定
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            print("ログインページへ移動...")
            page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")
            
            # ページが安定するまで少し待機
            page.wait_for_timeout(3000)

            # --- 本質的解決策：可視入力欄を順番に埋める ---
            print("入力フィールドを特定中...")
            # type="hidden"（隠しトークン）を排除し、画面に見えているものだけを取得
            visible_inputs = page.locator('input:not([type="hidden"]):visible')
            
            input_count = visible_inputs.count()
            print(f"操作可能な入力欄を {input_count} 個発見しました。")

            if input_count >= 2:
                print("1番目にID、2番目にパスワードを入力...")
                # nth(0)がログインID、nth(1)がパスワード
                visible_inputs.nth(0).fill(os.environ["GOOGLE_ID"])
                visible_inputs.nth(1).fill(os.environ["GOOGLE_PW"])
                
                # 青い「ログイン」ボタンをクリック
                # ボタンが3つ目のinputの場合もあれば、buttonタグの場合もあるため
                # 最も確実な「Enterキー」で送信します
                page.keyboard.press("Enter")
            else:
                # もし上記で見つからない場合の予備：プレースホルダーやラベルに近いものを探す
                print("汎用セレクターで再試行...")
                page.get_by_placeholder("ログインID").fill(os.environ["GOOGLE_ID"])
                page.get_by_placeholder("パスワード").fill(os.environ["GOOGLE_PW"])
                page.keyboard.press("Enter")
            
            print("ログイン後のデータ読み込み待ち（30秒）...")
            page.wait_for_timeout(30000) 

            # データ抽出
            page_content = page.inner_text('body')
            # APIパンク防止（429対策）
            clean_text = " ".join(page_content.split())[:15000] 

            print("Gemini 1.5 Flash で分析実行...")
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=f"以下のMEOデータを日本語で要約してください:\n\n{clean_text}"
            )

            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("【祝】ログイン突破・データ送信完了！")

        except Exception as e:
            print(f"エラー発生: {e}")
            page.screenshot(path="final_debug.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
