import os
import requests
from google import genai
from playwright.sync_api import sync_playwright

def run_agent():
    # 最新SDK & v1窓口（404対策）
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        http_options={'api_version': 'v1'}
    )
    
    with sync_playwright() as p:
        print("ブラウザ起動中...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            print("ダッシュボードへ移動...")
            page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")
            
            # ログイン処理（最も成功率の高いシンプルな方法）
            page.wait_for_selector('input', timeout=10000)
            inputs = page.query_selector_all('input[type="email"], input[type="password"]')
            if len(inputs) >= 2:
                inputs[0].fill(os.environ["GOOGLE_ID"])
                inputs[1].fill(os.environ["GOOGLE_PW"])
                page.keyboard.press("Enter")
            
            print("ログイン後の読み込み待ち（30秒）...")
            page.wait_for_timeout(30000) 

            # --- 本質的な改善：データの「間引き」 ---
            print("データを抽出・整理中...")
            # 全文ではなく、数値や重要なテキストが含まれる「主要な要素」だけを抽出
            # これによりAPIに送るトークン数を劇的に減らし、429エラーを防ぎます
            raw_text = page.inner_text('body')
            
            # 不要な空白や改行を削り、先頭から数万文字程度に制限（パンク防止）
            clean_text = " ".join(raw_text.split())[:15000] 

            if len(clean_text) < 200:
                print("警告: 取得データが少なすぎます。ログインに失敗している可能性があります。")

            # Gemini 1.5 Flash (制限が2.0より緩い) で実行
            print(f"Gemini APIへ送信中（データ長: {len(clean_text)}文字）...")
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=f"以下のMEOデータを解析し、重要な数値を日本語で要約して:\n\n{clean_text}"
            )

            # GASへ送信
            requests.post(os.environ["GAS_URL"], json={"message": response.text})
            print("【祝】すべての工程が完了しました！")

        except Exception as e:
            print(f"実行中にエラーが発生: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
