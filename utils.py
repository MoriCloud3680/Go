import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

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

# 최근 실제 추첨번호 22개 가져오기
def get_latest_numbers():
    client = authenticate_google()
    sheet = client.open("Go").worksheet("Actual22")
    data = sheet.get_all_records()
    if not data:
        raise ValueError("Actual22 시트에 데이터가 없습니다.")
    latest_row = data[-1]
    return latest_row['Round'], latest_row['Actual22']

# 자동 추천 번호(10개) 저장
def save_recommended_numbers(round_no, numbers):
    client = authenticate_google()
    sheet = client.open("Go").worksheet("F10")
    today_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    sheet.append_row([today_date, round_no, numbers])

def generate_recommendation(actual_numbers):
    # 숫자로 넘어올 수 있으니 강제로 문자열로 변환
    actual_numbers = str(actual_numbers)

    # 문자열 숫자 → 정수형 변환
    numbers_list = [int(num.strip()) for num in actual_numbers.split(",")]

    # 임시 로직: 앞 10개 숫자만 선택
    recommended_10_numbers = numbers_list[:10]

    # 다시 문자열로 변환 (앞에 0을 붙임)
    recommended_10_numbers_str = [f"{num:02d}" for num in recommended_10_numbers]

    return ",".join(recommended_10_numbers_str)


# Render에서 호출되는 주요 함수
def update_after_input():
    round_no, actual_numbers = get_latest_numbers()
    recommended_numbers = generate_recommendation(actual_numbers)
    save_recommended_numbers(round_no + 1, recommended_numbers)
