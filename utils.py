import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 구글 인증
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

# 최신 회차 데이터 가져오기
def fetch_current_round():
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    sheet = client.open_by_key(sheet_id).worksheet("Actual22")
    round_no = int(sheet.acell('B2').value)
    actual_numbers = sheet.acell('C2').value.replace(" ", "")
    return round_no, actual_numbers

# 구글시트 업데이트 (F10)
def update_recommendations(round_no, numbers, tag):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")
    # 날짜 제외하고 Round, Tag, Numbers 만 입력
    f10_sheet.insert_row([round_no, tag, numbers], 2, value_input_option="USER_ENTERED")

# Adaptive GA 구현 (직전 회차 활용)
def run_adaptive_ga(actual_numbers):
    actual_pool = [int(n) for n in actual_numbers.split(",")]

    # 적합도 함수
    def fitness(combo):
        return len(set(combo) & set(actual_pool))

    # 초기 조합 생성 함수
    def generate_combo():
        return random.sample(range(1, 71), 10)

    # GA 하이퍼파라미터 (적당히 효율적 설정)
    population_size = 150
    generations = 40
    mutation_rate = 0.1

    population = [generate_combo() for _ in range(population_size)]

    for _ in range(generations):
        # 적합도 기준 내림차순 정렬
        population.sort(key=fitness, reverse=True)
        next_generation = population[:10]  # Elite 유지 (상위 10개 조합)

        # 새 세대 생성 (crossover + mutation)
        while len(next_generation) < population_size:
            parents = random.sample(population[:20], 2)  # 상위 20개 내에서만 부모 선택
            crossover_point = random.randint(1, 9)
            child = parents[0][:crossover_point] + parents[1][crossover_point:]

            # Mutation 적용
            if random.random() < mutation_rate:
                mutation_index = random.randint(0, 9)
                child[mutation_index] = random.randint(1, 70)

            # 중복 제거 및 개수 보정
            child = list(set(child))
            while len(child) < 10:
                new_num = random.randint(1, 70)
                if new_num not in child:
                    child.append(new_num)

            next_generation.append(child)

        population = next_generation

    # 최종 최적 조합 선택
    best_combination = max(population, key=fitness)
    return sorted(best_combination)
