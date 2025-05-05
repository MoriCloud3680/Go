import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import random
from flask import Flask

# 구글 인증
def authenticate_google():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# 최신 실제 번호 가져오기
def get_latest_numbers():
    client = authenticate_google()
    sheet = client.open("Go").worksheet("Actual22")
    df = pd.DataFrame(sheet.get_all_records())
    df['Round'] = pd.to_numeric(df['Round'])
    latest_row = df.loc[df['Round'].idxmax()]

    actual_numbers = latest_row['Actual22']
    if isinstance(actual_numbers, (int, float)):
        actual_numbers = str(int(actual_numbers)).zfill(44)
        actual_numbers = ",".join([actual_numbers[i:i+2] for i in range(0, len(actual_numbers), 2)])

    return latest_row['Round'], actual_numbers

# 추천 번호 저장 (정상적으로 아래에 추가)
def save_recommended_numbers(round_no, numbers, tag):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("F10")
    today_date = pd.Timestamp.now().strftime("%Y-%m-%d")

    if isinstance(numbers, list):
        numbers = ",".join([f"{int(num):02d}" for num in numbers])
    else:
        numbers = ",".join([f"{int(num):02d}" for num in numbers.split(",")])

    round_no = int(round_no)

    sheet.append_row([today_date, round_no, tag, numbers])
    print(f"✅ 저장 성공: {today_date}, {round_no}, {tag}, {numbers}")

# GA 모델 함수 (추천 번호 생성)
def run_ga_model(actual_numbers):
    actual_numbers = str(actual_numbers)
    actual_pool = [int(n) for n in actual_numbers.split(",")]

    def fitness(combo):
        return len(set(combo) & set(actual_pool))

    def generate_combo():
        return random.sample(range(1, 71), 10)

    population_size = 100
    generations = 30
    mutation_rate = 0.1

    population = [generate_combo() for _ in range(population_size)]

    for _ in range(generations):
        population.sort(key=fitness, reverse=True)
        next_generation = population[:10]

        while len(next_generation) < population_size:
            parents = random.sample(population[:50], 2)
            crossover_point = random.randint(1, 9)
            child = parents[0][:crossover_point] + parents[1][crossover_point:]

            if random.random() < mutation_rate:
                mutation_index = random.randint(0, 9)
                child[mutation_index] = random.randint(1, 70)

            child = list(set(child))
            while len(child) < 10:
                new_num = random.randint(1, 70)
                if new_num not in child:
                    child.append(new_num)

            next_generation.append(child)

        population = next_generation

    best_combination = max(population, key=fitness)
    formatted_best = ",".join(sorted([f"{num:02d}" for num in best_combination]))

    return formatted_best

# 대안 조합 생성
def generate_alternative(existing_combinations):
    while True:
        new_combo = random.sample(range(1, 71), 10)
        formatted_new_combo = ",".join(sorted([f"{num:02d}" for num in new_combo]))
        if formatted_new_combo not in existing_combinations:
            return formatted_new_combo

# 메인 함수 (추천번호 1개 + 대안 2개 생성)
def update_after_input():
    round_no, actual_numbers = get_latest_numbers()

    # 최적 조합 생성
    recommended_numbers = run_ga_model(actual_numbers)
    save_recommended_numbers(round_no + 1, recommended_numbers, "Best")

    # 대안 조합 2개 생성
    existing = {recommended_numbers}
    for i in range(1, 3):
        alt_combo = generate_alternative(existing)
        save_recommended_numbers(round_no + 1, alt_combo, f"Alternative {i}")
        existing.add(alt_combo)

# Flask 앱 정의
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    update_after_input()  # 실제 번호로 추천번호 및 대안번호 생성 및 저장
    return "GA 모델이 성공적으로 실행되었습니다.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
