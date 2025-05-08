import os
import json
import gspread
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
import random
from functools import lru_cache
from collections import Counter, defaultdict
from sklearn.cluster import KMeans
import numpy as np

app = Flask(__name__)

@lru_cache(maxsize=1)
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    return gspread.authorize(creds)

def fetch_latest_rounds(n=30):
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Actual22")
    data = sheet.get(f'A2:B{n+1}')
    rounds_numbers = [list(map(int, row[1].replace(" ", "").split(","))) for row in data if len(row) > 1]
    current_round = int(data[0][0])
    return current_round, rounds_numbers

def get_last_generated_round():
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Status")
    last_round = sheet.acell('A2').value
    return int(last_round) if last_round else 0

def update_last_generated_round(round_no):
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Status")
    sheet.update('A2', [[str(round_no)]])

def update_recommendation(round_no, tag, numbers):
    client = authenticate_google()
    f10_sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("F10")
    numbers_str = ",".join(map(str, numbers))
    f10_sheet.insert_row([round_no, tag, numbers_str], 2, value_input_option="USER_ENTERED")

# 번호 군집화, 위치별 빈도, Hot/Cold 번호 및 번호 간격 분석 추가
def number_analysis(numbers_history):
    positional_freq = [Counter() for _ in range(22)]
    num_occurrences = defaultdict(int)
    last_seen_round = defaultdict(lambda: -100)
    current_round_idx = len(numbers_history)

    for idx, round_nums in enumerate(numbers_history):
        for position, num in enumerate(round_nums):
            positional_freq[position][num] += 1
            num_occurrences[num] += 1
            last_seen_round[num] = idx

    num_array = np.array(list(num_occurrences.keys())).reshape(-1, 1)
    num_weights = np.array(list(num_occurrences.values()))
    kmeans = KMeans(n_clusters=5, random_state=42).fit(num_array, sample_weight=num_weights)

    clusters = defaultdict(list)
    for num, label in zip(num_occurrences.keys(), kmeans.labels_):
        clusters[label].append(num)

    recent_numbers = numbers_history[:5]
    recent_flat = [num for nums in recent_numbers for num in nums]
    recent_counts = Counter(recent_flat)
    hot_numbers = [num for num, cnt in recent_counts.items() if cnt >= 3]
    cold_numbers = [num for num, cnt in recent_counts.items() if cnt == 1]

    # 번호 간격 분석
    gaps = {num: current_round_idx - last_seen_round[num] for num in range(1, 71)}

    return clusters, positional_freq, hot_numbers, cold_numbers, gaps

def adaptive_overlap_ga(previous_numbers_sets, clusters, positional_freq, hot_numbers, cold_numbers, gaps):
    all_prev_nums = set().union(*previous_numbers_sets)

    def fitness(candidate):
        overlap = len(set(candidate) & all_prev_nums)
        cluster_score = sum(any(num in clusters[label] for num in candidate) for label in clusters)
        positional_score = sum(positional_freq[i][num] for i, num in enumerate(candidate) if num in positional_freq[i])
        hot_cold_score = sum(2 if num in hot_numbers else -1 if num in cold_numbers else 0 for num in candidate)
        gap_score = sum(gaps[num] for num in candidate)
        return (overlap + cluster_score + positional_score + hot_cold_score + (gap_score * 0.1)) if 4 <= overlap <= 6 else -100

    population_size = 100
    generations = 50
    mutation_rate = 0.15

    def generate_candidate():
        candidate = []
        for i in range(10):
            if positional_freq[i]:
                top_nums = [num for num, _ in positional_freq[i].most_common(3)]
                candidate.append(random.choice(top_nums))
            else:
                candidate.append(random.randint(1, 70))
        candidate = list(set(candidate))
        while len(candidate) < 10:
            candidate.append(random.randint(1, 70))
        return sorted(candidate[:10])

    population = [generate_candidate() for _ in range(population_size)]

    for _ in range(generations):
        population.sort(key=fitness, reverse=True)
        next_generation = population[:10]

        while len(next_generation) < population_size:
            parents = random.sample(population[:20], 2)
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
    next_round = current_round + 1
    last_generated_round = get_last_generated_round()

    if next_round != last_generated_round:
        try:
            clusters, positional_freq, hot_numbers, cold_numbers, gaps = number_analysis(previous_numbers_sets)
            ga_numbers = adaptive_overlap_ga(previous_numbers_sets, clusters, positional_freq, hot_numbers, cold_numbers, gaps)
            update_recommendation(next_round, "GA+Cluster+PosFreq+HotCold+Gaps", ga_numbers)
            update_last_generated_round(next_round)
            return f"✅ {next_round}회차 GA+Cluster+PosFreq+HotCold+Gaps 조합 생성 완료", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {next_round}회차 이미 생성됨", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
