import os
import json
import gspread
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random

app = Flask(__name__)

# 전역변수로 최근 생성한 회차 기록
last_generated_round = None

# 구글 인증 함수
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    credentials_dict = json.loads(google_credentials_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

# 최신회차 데이터 불러오기
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('B2').value)
    actual_numbers = sheet.acell('C2').value
    return round_no, actual_numbers

# 기존방식 prev_best (랜덤 10개 추출)
def prev_best(actual_numbers):
    numbers_pool = [int(n) for n in actual_numbers.split(",")]
    selected_numbers = sorted(random.sample(numbers_pool, 10))
    return ",".join([f"{num:02d}" for num in selected_numbers])

# GA Best (최근 5회차 가장 많이 나온 번호 기반)
def ga_recent_best():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    recent_data = sheet.get('C2:C6')  # 최근 5개 회차
    num_freq = {}
    for data in recent_data:
        for num in data[0].split(","):
            num_freq[num] = num_freq.get(num, 0) + 1
    top_numbers = sorted(num_freq, key=num_freq.get, reverse=True)[:10]
    top_numbers = sorted([int(n) for n in top_numbers])
    return ",".join([f"{num:02d}" for num in top_numbers])

# GA Best (기존 방식: 최근 1회차 고정 번호로 하고 나머지 랜덤)
def ga_best(actual_numbers):
    recent_nums = [int(n) for n in actual_numbers.split(",")]
    fixed_nums = random.sample(recent_nums, 5)
    remaining_pool = [n for n in range(1, 71) if n not in fixed_nums]
    random_nums = random.sample(remaining_pool, 5)
    combined_nums = sorted(fixed_nums + random_nums)
    return ",".join([f"{num:02d}" for num in combined_nums])

# 시트 업데이트 함수
def update_recommendations(round_no, numbers, tag):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")
    today_date = datetime.now().strftime('%Y-%m-%d')
    f10_sheet.insert_row([today_date, round_no, tag, numbers], 2, value_input_option="USER_ENTERED")

@app.route("/", methods=["GET"])
def home():
    global last_generated_round

    current_round, actual_numbers = fetch_current_round()

    if current_round != last_generated_round:
        try:
            # 딱 3개 조합만 생성 (prev_best, GA best, GA recent5 best)
            pb_numbers = prev_best(actual_numbers)
            ga_numbers = ga_best(actual_numbers)
            ga_recent_numbers = ga_recent_best()

            update_recommendations(current_round, pb_numbers, "Prev Best")
            update_recommendations(current_round, ga_numbers, "GA Best")
            update_recommendations(current_round, ga_recent_numbers, "GA Recent5 Best")

            last_generated_round = current_round

            return f"✅ {current_round}회차 조합 생성 완료.", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {current_round}회차는 이미 처리됨.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
