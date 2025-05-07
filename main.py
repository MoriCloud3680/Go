import os
import json
import gspread
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import random

app = Flask(__name__)

# 전역 변수로 중복 실행 방지
last_generated_round = None

def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

# 최근 회차 데이터 가져오기
def fetch_current_round():
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Actual22")
    round_no = int(sheet.acell('A2').value)
    actual_numbers = sheet.acell('B2').value.replace(" ", "")
    return round_no, actual_numbers

# 최근 5회차 데이터 가져오기 (Adaptive GA용)
def fetch_recent_numbers(count=5):
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Actual22")
    recent_numbers = sheet.get(f'B2:B{1+count}')
    recent_numbers = [list(map(int, row[0].split(','))) for row in recent_numbers if row]
    if len(recent_numbers) < 2:
        raise ValueError("최소 2회차 데이터가 필요합니다.")
    return recent_numbers

# GA 모델 실행
def adaptive_ga_model(recent_numbers):
    pool = set(num for nums in recent_numbers for num in nums)

    def fitness(combo):
        return sum(len(set(combo) & set(nums)) for nums in recent_numbers)

    population_size = 200
    generations = 50
    mutation_rate = 0.1

    def generate_combo():
        return random.sample(list(pool), 10)

    population = [generate_combo() for _ in range(population_size)]

    for _ in range(generations):
        population.sort(key=fitness, reverse=True)
        next_generation = population[:10]

        while len(next_generation) < population_size:
            parents = random.sample(population[:20], 2)
            crossover_point = random.randint(1, 9)
            child = parents[0][:crossover_point] + parents[1][crossover_point:]

            if random.random() < mutation_rate:
                child[random.randint(0, 9)] = random.choice(list(pool))

            child = list(set(child))
            while len(child) < 10:
                num = random.choice(list(pool))
                if num not in child:
                    child.append(num)

            next_generation.append(child)

        population = next_generation

    return sorted(max(population, key=fitness))

# 시트 업데이트 (F10 시트 구조 수정)
def update_recommendations(round_no, numbers, tag):
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("F10")
    sheet.insert_row([round_no, tag, numbers], 2, value_input_option="USER_ENTERED")

@app.route("/", methods=["GET"])
def home():
    global last_generated_round

    current_round, _ = fetch_current_round()
    next_round = current_round + 1

    if next_round != last_generated_round:
        try:
            recent_numbers = fetch_recent_numbers(5)
            ga_numbers = adaptive_ga_model(recent_numbers)
            formatted_numbers = ",".join([f"{num:02d}" for num in ga_numbers])

            update_recommendations(next_round, formatted_numbers, "Adaptive GA Optimized")
            last_generated_round = next_round

            return f"✅ {next_round}회차 조합 생성 완료.", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {next_round}회차 이미 생성됨.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
