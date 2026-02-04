import os
from google import genai

def run_agent():
    try:
        # 1. 接続設定 (v1を強制)
        client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"],
            http_options={'api_version': 'v1'}
        )
        
        # 2. 単純な挨拶を投げる
        print("APIの接続テストを開始します...")
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="こんにちは、接続テストです。成功なら『OK』と返してください。"
        )
        
        print(f"APIからの返答: {response.text}")
        print("【結論】APIキーとライブラリの設定は正常です！")

    except Exception as e:
        print(f"【結論】APIに問題があります: {e}")

if __name__ == "__main__":
    run_agent()
