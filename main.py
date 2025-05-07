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

# Google 인증 함수
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    credentials_dict = json.loads(google_credentials_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

# 최신 회차 데이터 불러오기
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('B2').value)
    actual_numbers = sheet.acell('C2').value.replace(" ", "")
    return round_no, actual_numbers

# Adaptive GA 모델 (중복방지 및 홀짝 비율 추가)
def run_adaptive_ga(actual_numbers):
    actual_pool = [int(n) for n in actual_numbers.split(",")]

    def fitness(combo):
        return len(set(combo) & set(actual_pool))

    def generate_combo():
        while True:
            combo = random.sample(range(1, 71), 10)
            odd = len([num for num in combo if num % 2 == 1])
            even = 10 - odd
            if odd >= 3 and even >= 3:
                return combo

    population_size = 150
    generations = 50
    mutation_rate = 0.1

    population = [generate_combo() for _ in range(population_size)]

    for _ in range(generations):
        population.sort(key=fitness, reverse=True)
        next_generation = population[:10]

        while len(next_generation) < population_size:
            parents = random.sample(population[:20], 2)
            crossover_point = random.randint(1, 9)
            child = parents[0][:crossover_point] + parents[1][crossover_point:]

            # mutation
            if random.random() < mutation_rate:
                mutation_index = random.randint(0, 9)
                new_number = random.randint(1, 70)
                while new_number in child:
                    new_number = random.randint(1, 70)
                child[mutation_index] = new_number

            # 중복 방지
            child = list(dict.fromkeys(child))
            while len(child) < 10:
                new_num = random.randint(1, 70)
                if new_num not in child:
                    child.append(new_num)

            # 홀짝 비율 제한 (최소 3홀/3짝)
            odd = len([num for num in child if num % 2 == 1])
            even = 10 - odd
            if odd >= 3 and even >= 3:
                next_generation.append(child)

        population = next_generation

    best_combination = max(population, key=fitness)
    return sorted(best_combination)

# Google Sheets에 업데이트
def update_recommendations(round_no, numbers, tag):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")
    f10_sheet.insert_row([round_no, tag, numbers], 2, value_input_option="USER_ENTERED")

@app.route("/", methods=["GET"])
def home():
    global last_generated_round

    current_round, actual_numbers = fetch_current_round()
    next_round = current_round + 1

    if next_round != last_generated_round:
        try:
            ga_numbers = run_adaptive_ga(actual_numbers)
            formatted_ga_numbers = ",".join([f"{num:02d}" for num in ga_numbers])

            update_recommendations(next_round, formatted_ga_numbers, "Adaptive GA Optimized")
            last_generated_round = next_round

            return f"✅ {next_round}회차 조합 생성 완료.", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {next_round}회차는 이미 처리됨.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
