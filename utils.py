import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
from datetime import datetime
import numpy as np

def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_credentials_json = os.getenv('GOOGLE_CREDENTIALS')
    credentials_dict = json.loads(google_credentials_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('B2').value)
    actual_numbers = sheet.acell('C2').value
    return round_no, actual_numbers

def prev_best(actual_numbers):
    numbers_pool = [int(n) for n in actual_numbers.split(",")]
    selected_numbers = sorted(random.sample(numbers_pool, 10))
    return ",".join([f"{num:02d}" for num in selected_numbers])

def ga_best(actual_numbers):
    recent_nums = [int(n) for n in actual_numbers.split(",")]
    fixed_nums = random.sample(recent_nums, 5)
    remaining_pool = [n for n in range(1, 71) if n not in fixed_nums]
    random_nums = random.sample(remaining_pool, 5)
    combined_nums = sorted(fixed_nums + random_nums)
    return ",".join([f"{num:02d}" for num in combined_nums])

def ga_recent_best():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    recent_data = sheet.get('C2:C6')
    num_freq = {}
    for data in recent_data:
        for num in data[0].split(","):
            num_freq[num] = num_freq.get(num, 0) + 1
    top_numbers = sorted(num_freq, key=num_freq.get, reverse=True)[:10]
    top_numbers = sorted([int(n) for n in top_numbers])
    return ",".join([f"{num:02d}" for num in top_numbers])

# ✅ 실제 GA 전략 구현 (최적화된 번호 10개 선택)
def real_ga_optimization():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    recent_data = sheet.get('C2:C11')  # 최근 10회차 데이터 사용
    num_freq = {}
    for data in recent_data:
        for num in data[0].split(","):
            num_freq[int(num)] = num_freq.get(int(num), 0) + 1

    population = [random.sample(range(1, 71), 10) for _ in range(100)]
    generations = 50

    def fitness(chromosome):
        return sum(num_freq.get(num, 0) for num in chromosome)

    for _ in range(generations):
        population.sort(key=fitness, reverse=True)
        next_gen = population[:20]  # 상위 20개 선택 (엘리트 유지)

        while len(next_gen) < 100:
            parents = random.sample(population[:50], 2)
            crossover_point = random.randint(3, 7)
            child = parents[0][:crossover_point] + parents[1][crossover_point:]
            
            # 돌연변이
            if random.random() < 0.1:
                mutate_idx = random.randint(0, 9)
                child[mutate_idx] = random.choice(range(1, 71))

            child = list(set(child))
            while len(child) < 10:
                child.append(random.choice(range(1, 71)))
            next_gen.append(child)

        population = next_gen

    best_chromosome = sorted(population[0])
    return ",".join([f"{num:02d}" for num in best_chromosome])

def update_recommendations(round_no, numbers, tag):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")
    today_date = datetime.now().strftime('%Y-%m-%d')
    f10_sheet.insert_row([today_date, round_no, tag, numbers], 2, value_input_option="USER_ENTERED")
