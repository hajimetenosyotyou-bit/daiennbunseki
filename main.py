import os
import requests
from google import genai
from playwright.sync_api import sync_playwright

def run_agent():
    # 404を避けるため、APIのバージョン指定をあえて外してSDKの自動判別に任せます
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    with sync_playwright() as p:
        print("ブラウザ起動...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            print("ログインページへ移動...")
            page.goto("https://app.meo-dash.com/users/sign_in", wait_until="networkidle")
            page.wait_for_timeout(3000)

            print("ID/PW入力中...")
            visible_inputs = page.locator('input:not([type="hidden"]):visible')
            if visible_inputs.count() >= 2:
                visible_inputs.nth(0).fill(os.environ["GOOGLE_ID"])
                visible_inputs.nth(1).fill(os.environ["GOOGLE_PW"])
                page.keyboard.press("Enter")
            
            print("ログイン完了。30秒待機...")
            page.wait_for_timeout(30000) 

            # データ抽出
            page_content = page.inner_text('body')
            print(f"取得成功: {len(page_content)}文字")
            clean_text = " ".join(page_content.split())[:10000] 

            # --- AI分析：モデル名を 'gemini-1.5-flash' に固定 ---
            print("Gemini API 分析開始...")
            try:
                # v1beta等の不整合を避けるため、最も標準的な呼び出し方にします
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=f"以下のMEOデータを数値中心に要約してください:\n\n{clean_text}"
                )
                final_message = response.text
            except Exception as ai_err:
                print(f"AI分析でエラー({ai_err})が出ましたが、生データを送信します。")
                final_message = f"【AI分析失敗・生データ送信】\n\n{clean_text}"

            # --- GASへ送信（新しいURLを使用） ---
            print("スプレッドシートへ送信中...")
            gas_url = os.environ["GAS_URL"]
            res = requests.post(gas_url, json={"message": final_message})
            
            print(f"GAS応答ステータス: {res.status_code}")
            # もし成功すれば、ここに {"status":"success"} と表示されます
            print(f"GAS応答内容: {res.text}")

        except Exception as e:
            print(f"実行エラー: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run_agent()
