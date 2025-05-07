import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random

# Google 인증
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    credentials_dict = json.loads(google_credentials_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

# 최신 회차 데이터 가져오기
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('A2').value)
    actual_numbers = sheet.acell('B2').value
    hot_numbers = [int(n) for n in sheet.acell('C2').value.split(",")]
    cold_numbers = [int(n) for n in sheet.acell('D2').value.split(",")]
    return round_no, actual_numbers, hot_numbers, cold_numbers

# 구글시트 업데이트 (날짜 제외)
def update_recommendations(round_no, numbers, tag):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")
    f10_sheet.insert_row([round_no, tag, numbers], 2, value_input_option="USER_ENTERED")

# Real GA Optimized (Hot/Cold) 전략
def real_ga_optimized(hot_numbers, cold_numbers):
    population_size = 200
    generations = 100
    mutation_rate = 0.1

    def generate_individual():
        combo = random.sample(hot_numbers, 4) + random.sample(cold_numbers, 2)
        remaining_pool = [n for n in range(1, 71) if n not in combo]
        combo += random.sample(remaining_pool, 4)
        return sorted(combo)

    population = [generate_individual() for _ in range(population_size)]

    for _ in range(generations):
        next_generation = population[:10]
        while len(next_generation) < population_size:
            parents = random.sample(population[:20], 2)
            crossover_point = random.randint(1, 8)
            child = parents[0][:crossover_point] + parents[1][crossover_point:]

            if random.random() < mutation_rate:
                mutation_index = random.randint(0, 9)
                mutation_pool = list(set(range(1, 71)) - set(child))
                child[mutation_index] = random.choice(mutation_pool)

            child = sorted(list(set(child)))
            while len(child) < 10:
                new_num = random.randint(1, 70)
                if new_num not in child:
                    child.append(new_num)

            next_generation.append(child)

        population = next_generation

    best_combination = sorted(random.choice(population[:5]))  # 상위 5개 중 랜덤 선택
    return ",".join(f"{num:02d}" for num in best_combination)
