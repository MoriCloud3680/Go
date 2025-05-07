import os
import json
import gspread
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
import random

app = Flask(__name__)

last_generated_round = None

def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    return gspread.authorize(creds)

def fetch_latest_round():
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Actual22")
    round_no = int(sheet.acell('A2').value)
    actual_numbers = list(map(int, sheet.acell('B2').value.replace(" ", "").split(",")))
    return round_no, actual_numbers

def adaptive_overlap_ga(previous_numbers):
    def fitness(candidate):
        overlap = len(set(candidate) & set(previous_numbers))
        # 4~6개 정도의 overlap 이 최적으로 판단됨
        return -abs(5 - overlap)  

    population_size = 200
    generations = 50
    mutation_rate = 0.1

    def generate_candidate():
        overlap_count = random.randint(4, 6)  # overlap 숫자 범위
        overlap_nums = random.sample(previous_numbers, overlap_count)
        remaining_nums = random.sample([n for n in range(1, 71) if n not in overlap_nums], 10 - overlap_count)
        return sorted(overlap_nums + remaining_nums)

    population = [generate_candidate() for _ in range(population_size)]

    for _ in range(generations):
        population.sort(key=fitness, reverse=True)
        next_generation = population[:20]

        while len(next_generation) < population_size:
            parents = random.sample(population[:50], 2)
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

def update_recommendation(round_no, tag, numbers):
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("F10")
    numbers_str = ','.join(f"{num:02d}" for num in numbers)
    sheet.insert_row([round_no, tag, numbers_str], 2, value_input_option="USER_ENTERED")

@app.route("/", methods=["GET"])
def home():
    global last_generated_round
    current_round, previous_numbers = fetch_latest_round()
    next_round = current_round + 1

    if next_round != last_generated_round:
        try:
            ga_numbers = adaptive_overlap_ga(previous_numbers)
            update_recommendation(next_round, "Adaptive Overlap", ga_numbers)
            last_generated_round = next_round
            return f"✅ {next_round}회차 Adaptive Overlap 조합 생성 완료", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {next_round}회차 이미 생성됨", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
