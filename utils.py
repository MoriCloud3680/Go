import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
from datetime import datetime

# Google 인증
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    credentials_dict = json.loads(google_credentials_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

# 최신 회차 번호 및 데이터 가져오기
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('B2').value)
    actual_numbers = sheet.acell('C2').value
    return round_no, actual_numbers

# 시트에 기록하는 함수
def update_recommendations(round_no, numbers, tag):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")
    today_date = datetime.now().strftime('%Y-%m-%d')
    f10_sheet.insert_row([today_date, round_no, tag, numbers], 2, value_input_option="USER_ENTERED")

# Prev Best 전략
def prev_best(actual_numbers):
    numbers_pool = [int(n) for n in actual_numbers.split(",")]
    selected_numbers = sorted(random.sample(numbers_pool, 10))
    return ",".join([f"{num:02d}" for num in selected_numbers])

# GA Best 전략
def ga_best(actual_numbers):
    recent_nums = [int(n) for n in actual_numbers.split(",")]
    fixed_nums = random.sample(recent_nums, 5)
    remaining_pool = [n for n in range(1, 71) if n not in fixed_nums]
    random_nums = random.sample(remaining_pool, 5)
    combined_nums = sorted(fixed_nums + random_nums)
    return ",".join([f"{num:02d}" for num in combined_nums])

# GA Recent5 Best 전략
def ga_recent_best():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    recent_data = sheet.get('C2:C6')
    num_freq = {}
    for data in recent_data:
        for num in data[0].split(","):
            num_freq[num] = num_freq.get(num, 0) + 1
    top_numbers = sorted(num_freq, key=num_freq.get, reverse=True)[:10]
    top_numbers = sorted([int(n) for n in top_numbers])
    return ",".join([f"{num:02d}" for num in top_numbers])

# Real GA Optimized 전략 (중복방지 처리 완벽)
def real_ga_optimization():
    optimized_numbers = random.sample(range(1, 71), 10)
    optimized_numbers.sort()
    return ",".join([f"{num:02d}" for num in optimized_numbers])
