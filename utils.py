import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 구글 인증 함수
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    credentials_dict = json.loads(google_credentials_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

# 최신 회차 번호 가져오기
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('B2').value)
    return round_no

# 최근 5회차의 최다 출현 번호 계산
def ga_recent_best():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    recent_data = sheet.get('C2:C6')  # 최근 5개 회차

    num_freq = {}
    for data in recent_data:
        numbers = data[0].replace(" ", "").split(",")
        for num in numbers:
            num_freq[num] = num_freq.get(num, 0) + 1

    top_numbers = sorted(num_freq, key=num_freq.get, reverse=True)[:10]
    return ",".join(sorted(top_numbers, key=lambda x: int(x)))

# 결과를 시트에 업데이트
def update_recommendations(round_no, numbers, tag):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")
    # 날짜 없이 기록
    f10_sheet.insert_row([round_no, tag, numbers], 2, value_input_option="USER_ENTERED")
