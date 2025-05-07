import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    credentials_dict = json.loads(google_credentials_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('A2').value)  # A2 셀에서 회차 번호를 가져옴
    return round_no

def ga_recent_best():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    recent_data = sheet.get('B2:B6')  # 최근 5개 회차 번호 데이터 (B2:B6)

    num_freq = {}
    for data in recent_data:
        numbers = data[0].replace(" ", "").split(",")
        for num in numbers:
            num_freq[num] = num_freq.get(num, 0) + 1

    top_numbers = sorted(num_freq, key=num_freq.get, reverse=True)[:10]
    return ",".join(sorted(top_numbers, key=lambda x: int(x)))

def update_recommendations(round_no, numbers, tag):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")
    f10_sheet.insert_row([round_no, tag, numbers], 2, value_input_option="USER_ENTERED")
