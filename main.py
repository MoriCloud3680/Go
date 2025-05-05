import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import random
from flask import Flask

# 구글 인증
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

# 최신 실제 번호 가져오기
def get_latest_numbers():
    client = authenticate_google()
    sheet = client.open("Go").worksheet("Actual22")
    df = pd.DataFrame(sheet.get_all_records())
    df['Round'] = pd.to_numeric(df['Round'])
    latest_row = df.loc[df['Round'].idxmax()]

    actual_numbers = latest_row['Actual22']
    if isinstance(actual_numbers, (int, float)):
        actual_numbers = str(int(actual_numbers)).zfill(44)
        actual_numbers = ",".join([actual_numbers[i:i+2] for i in range(0, len(actual_numbers), 2)])

    return latest_row['Round'], actual_numbers

# 데이터 저장 테스트 (특정 셀에 강제 저장)
def save_recommended_numbers_test(round_no, numbers, tag):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("F10")
    today_date = pd.Timestamp.now().strftime("%Y-%m-%d")

    if isinstance(numbers, list):
        numbers = ",".join([f"{int(num):02d}" for num in numbers])
    else:
        numbers = ",".join([f"{int(num):02d}" for num in numbers.split(",")])

    round_no = int(round_no)

    # A2 셀에 강제 저장 테스트
    sheet.update("A2", [[today_date, round_no, tag, numbers]])
    print(f"✅ 강제 저장 성공: {today_date}, {round_no}, {tag}, {numbers}")

# Flask 앱 정의
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    round_no, actual_numbers = get_latest_numbers()

    # 간단한 테스트로 데이터 저장
    save_recommended_numbers_test(round_no + 1, "01,02,03,04,05,06,07,08,09,10", "Test")

    return "Google Sheets 테스트 완료!", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
