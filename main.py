import os
import json
import gspread
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random

app = Flask(__name__)

last_generated_round = None

# 구글 인증 함수
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    return gspread.authorize(creds)

# 최신 회차 및 숫자 가져오기
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('B2').value)
    actual_numbers = sheet.acell('C2').value
    return round_no, actual_numbers

# 기존 Prev Best 로직 (직전 회차 22개 숫자에서 10개 랜덤)
def generate_prev_best(actual_numbers):
    numbers_pool = [int(n) for n in actual_numbers.split(",")]
    selected = sorted(random.sample(numbers_pool, 10))
    return ",".join([f"{num:02d}" for num in selected])

# 기존 GA Best 로직 (직전 회차에서 GA 최적화 - 고정 5개 + 랜덤 5개)
def generate_existing_ga_best(actual_numbers):
    numbers_pool = [int(n) for n in actual_numbers.split(",")]
    fixed_numbers = random.sample(numbers_pool, 5)
    remaining_numbers = list(set(range(1, 71)) - set(fixed_numbers))
    random_numbers = random.sample(remaining_numbers, 5)
    combined_numbers = sorted(fixed_numbers + random_numbers)
    return ",".join([f"{num:02d}" for num in combined_numbers])

# 최근 5회차 GA Best 로직 (최근 5개 회차에서 가장 자주 나온 5개 + 랜덤 5개)
def generate_recent_ga_best(client):
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    actual22_sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    recent_numbers_list = actual22_sheet.get('C2:C6')

    freq = {}
    for row in recent_numbers_list:
        nums = row[0].split(",")
        for num in nums:
            freq[num] = freq.get(num, 0) + 1

    fixed_numbers = [int(num) for num, count in sorted(freq.items(), key=lambda x: -x[1])[:5]]
    remaining_numbers = list(set(range(1, 71)) - set(fixed_numbers))
    random_numbers = random.sample(remaining_numbers, 5)

    combined_numbers = sorted(fixed_numbers + random_numbers)
    return ",".join([f"{num:02d}" for num in combined_numbers])

# F10 시트 업데이트 함수
def update_after_input():
    client = authenticate_google()
    today_date = datetime.now().strftime('%Y-%m-%d')
    round_no, actual_numbers = fetch_current_round()

    prev_best_numbers = generate_prev_best(actual_numbers)
    existing_ga_best_numbers = generate_existing_ga_best(actual_numbers)
    recent_ga_best_numbers = generate_recent_ga_best(client)

    f10_sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("F10")

    # 결과 삽입 (다음 회차로 표기하기 위해 round_no + 1)
    f10_sheet.insert_rows([
        [today_date, round_no + 1, "Prev Best", prev_best_numbers],
        [today_date, round_no + 1, "GA Best", existing_ga_best_numbers],
        [today_date, round_no + 1, "GA Recent5 Best", recent_ga_best_numbers]
    ], row=2, value_input_option="USER_ENTERED")

@app.route("/", methods=["GET"])
def home():
    global last_generated_round
    current_round, _ = fetch_current_round()

    if current_round != last_generated_round:
        try:
            update_after_input()
            last_generated_round = current_round
            return f"✅ {current_round + 1}회차 Prev Best, GA Best, GA Recent5 Best 조합 생성 완료.", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {current_round + 1}회차는 이미 처리됨.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
