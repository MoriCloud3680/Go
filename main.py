import os
import json
import gspread
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
import random
from functools import lru_cache

app = Flask(__name__)

@lru_cache(maxsize=1)
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    return gspread.authorize(creds)

def fetch_latest_rounds(n=3):
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Actual22")
    data = sheet.get(f'A2:B{n+1}')
    rounds_numbers = [list(map(int, row[1].replace(" ", "").split(","))) for row in data if len(row) > 1]
    current_round = int(data[0][0])
    return current_round, rounds_numbers

def get_last_confirmed_round():
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Status")
    last_round = sheet.acell('A2').value
    return int(last_round) if last_round else 0

def update_last_confirmed_round(round_no):
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Status")
    sheet.update('A2', [[str(round_no)]])

def update_recommendation(round_no, tag, numbers):
    client = authenticate_google()
    f10_sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("F10")
    numbers_str = ",".join(map(str, numbers))
    f10_sheet.insert_row([round_no, tag, numbers_str], 2, value_input_option="USER_ENTERED")

def adaptive_overlap_ga(previous_numbers_sets):
    all_prev_nums = set().union(*previous_numbers_sets)

    optimal_overlap = random.choice([3, 4, 5, 6, 7])

    def fitness(candidate):
        overlap = len(set(candidate) & all_prev_nums)
        if overlap == optimal_overlap:
            return 10
        else:
            return -abs(overlap - optimal_overlap)

    population_size = 150
    generations = 40
    mutation_rate = 0.1

    def generate_candidate():
        overlap_nums = random.sample(list(all_prev_nums), optimal_overlap)
        remaining_nums = random.sample([n for n in range(1, 71) if n not in overlap_nums], 10 - len(overlap_nums))
        return sorted(overlap_nums + remaining_nums)

    population = [generate_candidate() for _ in range(population_size)]

    for _ in range(generations):
        population.sort(key=fitness, reverse=True)
        next_generation = population[:10]

        while len(next_generation) < population_size:
            parents = random.sample(population[:30], 2)
            cross_point = random.randint(3, 7)
            child = parents[0][:cross_point] + parents[1][cross_point:]
            child = list(set(child))

            if random.random() < mutation_rate:
                child[random.randint(0, len(child)-1)] = random.randint(1, 70)

            while len(child) < 10:
                num = random.randint(1, 70)
                if num not in child:
                    child.append(num)

            next_generation.append(sorted(child))

        population = next_generation

    return sorted(max(population, key=fitness))

@app.route("/", methods=["GET"])
def home():
    current_round, previous_numbers_sets = fetch_latest_rounds()
    last_confirmed_round = get_last_confirmed_round()

    if current_round != last_confirmed_round:
        try:
            # 중복실행 방지를 위해 먼저 회차를 업데이트
            update_last_confirmed_round(current_round)

            # 첫 번째 GA 조합 생성 및 업데이트
            ga_numbers1 = adaptive_overlap_ga(previous_numbers_sets)
            update_recommendation(current_round + 1, "Adaptive Overlap Dynamic #1", ga_numbers1)

            # 두 번째 GA 조합 생성 및 업데이트
            ga_numbers2 = adaptive_overlap_ga(previous_numbers_sets)
            update_recommendation(current_round + 1, "Adaptive Overlap Dynamic #2", ga_numbers2)

            return f"✅ {current_round + 1}회차 Adaptive Overlap (Dynamic) 조합 2개 생성 완료", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {current_round + 1}회차 이미 생성됨", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
