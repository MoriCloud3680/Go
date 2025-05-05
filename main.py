import os
import json
import random
import gspread
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# 전역변수로 최근 생성한 회차 기록
last_generated_round = None

# 구글 인증 함수
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # 환경변수에서 JSON 키 로드
    google_credentials_json = os.getenv('GOOGLE_CREDENTIALS')

    # JSON 문자열을 dict로 파싱
    credentials_dict = json.loads(google_credentials_json)

    # 인증 설정
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)

    return client

# 현재 최신 회차 가져오기 (B2 셀 기준)
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = sheet.acell('B2').value
    return int(round_no)

# GA 모델로 최적 조합 찾기 (직전 회차 번호 기반)
def run_ga_model(actual_numbers, n_iter=1000, pool_size=50):
    actual_set = set(int(n) for n in actual_numbers.split(","))
    population = [sorted(random.sample(range(1, 71), 10)) for _ in range(pool_size)]

    def fitness(combo):
        return len(set(combo) & actual_set)

    for _ in range(n_iter):
        population.sort(key=fitness, reverse=True)
        next_gen = population[:10]
        while len(next_gen) < pool_size:
            parent1, parent2 = random.sample(population[:20], 2)
            crossover_point = random.randint(1, 9)
            child = sorted(set(parent1[:crossover_point] + parent2[crossover_point:]))
            while len(child) < 10:
                new_num = random.randint(1, 70)
                if new_num not in child:
                    child.append(new_num)
            next_gen.append(sorted(child))
        population = next_gen

    best_combo = population[0]
    alt_combos = random.sample(population[1:10], 2)

    best_combo.sort()
    for combo in alt_combos:
        combo.sort()

    return {
        "best": ",".join(f"{num:02d}" for num in best_combo),
        "alt": [",".join(f"{num:02d}" for num in combo) for combo in alt_combos]
    }

# 실제 사용하는 코드에서 GA 호출하는 부분
def update_after_input():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")
    actual22_sheet = client.open_by_key(sheet_id).worksheet("Actual22")

    today_date = datetime.now().strftime('%Y-%m-%d')
    round_no = int(actual22_sheet.acell('B2').value)
    actual_numbers = actual22_sheet.acell('C2').value

    # GA 실행
    ga_results = run_ga_model(actual_numbers)

    # GA 조합을 각각 다른 태그로 기록
    f10_sheet.insert_row([today_date, round_no + 1, "GA Best", ga_results["best"]], 2, value_input_option="USER_ENTERED")
    for idx, alt_combo in enumerate(ga_results["alt"], start=1):
        f10_sheet.insert_row([today_date, round_no + 1, f"GA Alt {idx}", alt_combo], 3, value_input_option="USER_ENTERED")

@app.route("/", methods=["GET"])
def home():
    global last_generated_round

    current_round = fetch_current_round()

    if current_round != last_generated_round:
        try:
            update_after_input()
            last_generated_round = current_round
            return f"✅ {current_round + 1}회차 신규 조합 생성 완료.", 200
        except Exception as e:
            return f"❌ GA 모델 실행 중 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ 이미 {current_round + 1}회차 조합 생성 완료됨. 추가 생성하지 않음.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
