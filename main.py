import os
import json
import random
import gspread
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# 구글 시트 인증
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.getenv('GOOGLE_CREDENTIALS')
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# 최근 3회차 번호 가져오기
def fetch_recent_rounds():
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Actual22")
    recent_numbers = sheet.get('C2:C4')  # 최근 3개 회차
    recent_numbers = [set(map(int, row[0].split(','))) for row in recent_numbers]
    return recent_numbers

# 평균 중복 개수 구하기
def average_overlap(recent_numbers):
    overlaps = [
        len(recent_numbers[i] & recent_numbers[i+1]) for i in range(len(recent_numbers)-1)
    ]
    return sum(overlaps) / len(overlaps)

# 중복 숫자 개수 결정
def determine_overlap_count(avg_overlap):
    if avg_overlap >= 9:
        return 7
    elif avg_overlap >= 7:
        return 6
    elif avg_overlap >= 5:
        return 5
    else:
        return random.choice([3,4])

# GA 조합 생성
def adaptive_overlap_ga(prev_numbers, overlap_count):
    fixed_nums = random.sample(prev_numbers, overlap_count)
    remaining_pool = [num for num in range(1, 71) if num not in fixed_nums]
    additional_nums = random.sample(remaining_pool, 10 - overlap_count)
    return sorted(fixed_nums + additional_nums)

# 시트에 결과 업데이트
def update_recommendations(round_no, numbers, tag):
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("F10")
    formatted_numbers = ','.join(f"{n:02d}" for n in numbers)
    sheet.insert_row([round_no, tag, formatted_numbers], 2, value_input_option="USER_ENTERED")

# 메인 라우트
@app.route("/", methods=["GET"])
def home():
    recent_numbers = fetch_recent_rounds()
    avg_overlap = average_overlap(recent_numbers)
    overlap_count = determine_overlap_count(avg_overlap)
    
    prev_round_numbers = recent_numbers[0]
    ga_numbers = adaptive_overlap_ga(list(prev_round_numbers), overlap_count)

    next_round = datetime.now().strftime('%Y%m%d%H%M')  # 날짜와 시간으로 유니크 회차 번호
    update_recommendations(next_round, ga_numbers, "Adaptive Overlap GA")

    return f"✅ Adaptive Overlap GA 생성 완료 ({next_round}): {ga_numbers}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
