import os
import json
import gspread
import random
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# 최근 생성한 회차 기록 (중복 방지용)
last_generated_round = None

# Google Sheets 인증
def authenticate_google():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    google_credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    credentials_dict = json.loads(google_credentials_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

# 현재 최신 회차 및 당첨번호 가져오기
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('B2').value)
    actual_numbers = sheet.acell('C2').value
    return round_no, actual_numbers

# 최근 5개 회차 번호 가져오기
def fetch_recent5_numbers():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    recent5_numbers = sheet.col_values(3)[1:6]
    return recent5_numbers

# 시트에 기록하기
def update_sheet(tag, numbers, current_round):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")
    today_date = datetime.now().strftime('%Y-%m-%d')
    f10_sheet.insert_row([today_date, current_round, tag, numbers], 2, value_input_option="USER_ENTERED")

# 기존 방식의 Prev Best (직전회차 번호 중 랜덤 10개 추출)
def generate_prev_best(actual_numbers):
    numbers_pool = [int(n) for n in actual_numbers.split(",")]
    selected_numbers = random.sample(numbers_pool, 10)
    selected_numbers.sort()
    return ",".join([f"{num:02d}" for num in selected_numbers])

# GA Best 로직 (고정 번호군 생성)
def run_ga_model(actual_numbers):
    numbers_pool = list(range(1, 71))
    fixed_numbers = [int(n) for n in actual_numbers.split(",")]
    remaining_numbers = [n for n in numbers_pool if n not in fixed_numbers]
    ga_selected = random.sample(remaining_numbers, 6)
    final_numbers = fixed_numbers[:4] + ga_selected
    final_numbers.sort()
    return ",".join([f"{num:02d}" for num in final_numbers])

# GA Recent5 Best (최근 5회차 번호 기반 최적 조합)
def run_ga_recent5(recent5_numbers):
    combined_pool = set()
    for nums in recent5_numbers:
        combined_pool.update(map(int, nums.split(",")))
    selected_numbers = random.sample(combined_pool, 10)
    selected_numbers.sort()
    return ",".join([f"{num:02d}" for num in selected_numbers])

@app.route("/", methods=["GET"])
def home():
    global last_generated_round

    current_round, actual_numbers = fetch_current_round()

    if current_round != last_generated_round:
        try:
            prev_best_combo = generate_prev_best(actual_numbers)
            update_sheet("Prev Best", prev_best_combo, current_round)

            ga_best_combo = run_ga_model(actual_numbers)
            update_sheet("GA Best", ga_best_combo, current_round)

            recent5_numbers = fetch_recent5_numbers()
            ga_recent5_combo = run_ga_recent5(recent5_numbers)
            update_sheet("GA Recent5 Best", ga_recent5_combo, current_round)

            last_generated_round = current_round

            return f"✅ {current_round}회차 조합 3개 생성 완료.", 200

        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {current_round}회차는 이미 처리됨. 중복 생성하지 않음.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
