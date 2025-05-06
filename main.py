import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from utils import real_ga_optimized

# 구글 인증
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    credentials_dict = json.loads(google_credentials_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    return gspread.authorize(creds)

# 최신회차 데이터 불러오기
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('B2').value)
    actual_numbers = sheet.acell('C2').value
    return round_no, actual_numbers

# 시트 업데이트 함수
def update_recommendation(round_no, numbers, tag):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")
    today_date = datetime.now().strftime('%Y-%m-%d')
    f10_sheet.insert_row([today_date, round_no, tag, numbers], 2, value_input_option="USER_ENTERED")

def main():
    current_round, actual_numbers = fetch_current_round()
    next_round = current_round + 1

    # 딱 1개 조합만 생성 후 종료
    optimized_numbers = real_ga_optimized(actual_numbers)
    update_recommendation(next_round, optimized_numbers, "Real GA Optimized")

    print(f"✅ {next_round}회차 Real GA Optimized 조합 생성 완료: {optimized_numbers}")

if __name__ == "__main__":
    main()
