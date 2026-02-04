import os
import requests
from google import genai
from playwright.sync_api import sync_playwright

def run_agent():
    # 1. APIクライアントの準備
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    with sync_playwright() as p:
        print("ブラウザ起動中...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            # 2. ログイン処理（前回成功したロジック）
            print("ログインページへ移動...")
            page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")
            page.wait_for_timeout(3000)

            print("ID/PW入力中...")
            visible_inputs = page.locator('input:not([type="hidden"]):visible')
            
            if visible_inputs.count() >= 2:
                visible_inputs.nth(0).fill(os.environ["GOOGLE_ID"])
                visible_inputs.nth(1).fill(os.environ["GOOGLE_PW"])
                page.keyboard.press("Enter")
            
            print("ログイン成功。データ読み込み待ち（30秒）...")
            page.wait_for_timeout(30000) 

            # 3. データの抽出
            page_content = page.inner_text('body')
            print(f"取得したテキスト量: {len(page_content)}文字")
            
            # AIに送るためにデータを整理
            clean_text = " ".join(page_content.split())[:10000] 

            # --- 4. ここからが「分析部分」の修正版 ---
            print("Gemini API で分析を試行中...")
            try:
                # 404が出やすいモデル指定を、最もシンプルな形に
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=f"以下のMEOデータを要約して:\n\n{clean_text}"
                )
                final_message = response.text
                print("AI分析に成功しました。")
            except Exception as ai_error:
                # もしAIが404エラーを出しても、取得した生データを送る（全滅回避！）
                print(f"AI分析でエラー({ai_error})が出ましたが、生データを送信します。")
                final_message = f"【AI分析失敗・生データ送信】\n\n{clean_text}"

            # 5. GAS（スプレッドシート）へ送信
            print("スプレッドシートへ送信中...")
            requests.post(os.environ["GAS_URL"], json={"message": final_message})
            print("【祝】すべての工程が完了しました！")

        except Exception as e:
            print(f"ログイン工程でエラーが発生しました: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
