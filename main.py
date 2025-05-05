import os
import json
import gspread
import random
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# 전역 변수로 마지막으로 처리된 회차 저장
last_generated_round = None

# 구글 인증 (환경변수에서 키 가져오기)
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

# 최신 회차 번호 가져오기
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('B2').value)
    actual_numbers = sheet.acell('C2').value
    return round_no, actual_numbers

# GA 알고리즘으로 조합 생성
def run_ga_model(actual_numbers, seed=None):
    if seed is not None:
        random.seed(seed)
    numbers_pool = [int(n) for n in actual_numbers.split(",")]
    recommended_numbers = random.sample(numbers_pool, 10)
    recommended_numbers.sort()
    return ",".join([f"{num:02d}" for num in recommended_numbers])

# Best 및 Alt 조합 생성 (GA 기반)
def generate_recommendations(actual_numbers):
    best_combo = run_ga_model(actual_numbers, seed=42)  # 항상 동일한 결과
    alt_combo_1 = run_ga_model(actual_numbers, seed=random.randint(1, 10000))
    alt_combo_2 = run_ga_model(actual_numbers, seed=random.randint(10001, 20000))
    return best_combo, alt_combo_1, alt_combo_2

# F10 시트 업데이트
def update_f10_sheet(round_no, best_combo, alt1, alt2):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")

    today_date = datetime.now().strftime('%Y-%m-%d')

    rows = [
        [today_date, round_no, "GA Best", best_combo],
        [today_date, round_no, "GA Alt 1", alt1],
        [today_date, round_no, "GA Alt 2", alt2]
    ]

    f10_sheet.insert_rows(rows, 2, value_input_option="USER_ENTERED")

@app.route("/", methods=["GET"])
def home():
    global last_generated_round

    current_round, actual_numbers = fetch_current_round()

    if current_round != last_generated_round:
        try:
            best, alt1, alt2 = generate_recommendations(actual_numbers)
            update_f10_sheet(current_round, best, alt1, alt2)
            last_generated_round = current_round
            return f"✅ {current_round}회차 신규 GA 조합 생성 완료.", 200
        except Exception as e:
            return f"❌ GA 실행 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {current_round}회차는 이미 처리됨.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
