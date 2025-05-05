import os
import json
import gspread
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random

app = Flask(__name__)

# 전역변수
last_generated_round = None

# 구글 인증
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    return gspread.authorize(creds)

# 현재 회차와 번호 가져오기
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('B2').value)
    actual_numbers = sheet.acell('C2').value
    return round_no, actual_numbers

# 기존 방식 조합 생성 (직전 회차 22개 중)
def generate_previous_based_combinations(actual_numbers, num_combinations=3):
    pool = [int(n) for n in actual_numbers.split(",")]
    combinations = []
    for _ in range(num_combinations):
        combo = random.sample(pool, 10)
        combo.sort()
        combinations.append(",".join([f"{num:02d}" for num in combo]))
    return combinations

# GA 최적 조합 찾기 (전체 번호 중에서 직전 번호와 가장 많이 겹치는 조합 찾기)
def fitness(combo, actual_set):
    return len(set(combo).intersection(actual_set))

def run_ga(actual_numbers, generations=100, population_size=50):
    actual_set = set(int(n) for n in actual_numbers.split(","))
    population = [random.sample(range(1, 71), 10) for _ in range(population_size)]

    for _ in range(generations):
        population.sort(key=lambda combo: fitness(combo, actual_set), reverse=True)
        next_gen = population[:10]

        while len(next_gen) < population_size:
            parents = random.sample(population[:20], 2)
            crossover = list(set(parents[0][:5] + parents[1][5:]))
            while len(crossover) < 10:
                new_num = random.randint(1, 70)
                if new_num not in crossover:
                    crossover.append(new_num)
            next_gen.append(crossover)

        population = next_gen

    best_combo = population[0]
    best_combo.sort()
    return ",".join([f"{num:02d}" for num in best_combo])

# GA 방식 조합 3개 생성
def generate_ga_combinations(actual_numbers, num_combinations=3):
    combinations = set()
    while len(combinations) < num_combinations:
        combo = run_ga(actual_numbers)
        combinations.add(combo)
    return list(combinations)

# 전체 실행 및 구글 시트 업데이트
def update_google_sheet():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")

    round_no, actual_numbers = fetch_current_round()
    today_date = datetime.now().strftime('%Y-%m-%d')

    # 기존 방식
    prev_combos = generate_previous_based_combinations(actual_numbers)
    tags_prev = ["Prev Best", "Prev Alt 1", "Prev Alt 2"]

    # GA 방식
    ga_combos = generate_ga_combinations(actual_numbers)
    tags_ga = ["GA Best", "GA Alt 1", "GA Alt 2"]

    # 구글 시트에 업데이트
    for tag, numbers in zip(tags_prev + tags_ga, prev_combos + ga_combos):
        f10_sheet.insert_row([today_date, round_no + 1, tag, numbers], 2, value_input_option="USER_ENTERED")

@app.route("/")
def home():
    global last_generated_round

    current_round, _ = fetch_current_round()
    if current_round != last_generated_round:
        try:
            update_google_sheet()
            last_generated_round = current_round
            return f"✅ {current_round + 1}회차 신규 조합 6개 생성 완료.", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {current_round}회차는 이미 처리됨.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
