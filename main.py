import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask

def authenticate_google():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def test_sheet_access():
    client = authenticate_google()
    
    # Actual22 데이터 가져오기 테스트
    sheet_actual = client.open("Go").worksheet("Actual22")
    records = sheet_actual.get_all_records()
    print(f"✅ Actual22 records fetched: {records[:3]}... (총 {len(records)}개)")  # 많으면 앞 3개만 출력

    # F10 시트 데이터 추가 테스트
    sheet_f10 = client.open("Go").worksheet("F10")
    sheet_f10.append_row(["2025-05-05", "9999999", "Debug", "01,02,03,04,05"], value_input_option="USER_ENTERED")
    print("✅ F10 test append success")

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    try:
        test_sheet_access()
        return "Debugging success", 200
    except Exception as e:
        return f"❌ Debugging failed: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
