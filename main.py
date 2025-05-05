import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import random
from flask import Flask

# Google 인증 (client 캐싱 적용)
client = None
def authenticate_google():
    global client
    if client is None:
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

# 최신 실제 번호 가져오기 (Round 최신순)
def get_latest_numbers():
    client = authenticate_google()
    sheet = client.open("Go").worksheet("Actual22")
    
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])  # 명시적으로 헤더를 첫 행으로 설정
    
    df['Round'] = pd.to_numeric(df['Round'], errors='coerce')
    df.dropna(subset=['Round'], inplace=True)

    latest_row = df.loc[df['Round'].idxmax()]

    actual_numbers = latest_row['Actual22']
    if pd.isnull(actual_numbers) or actual_numbers == "":
        raise ValueError("Actual22 데이터가 비어있습니다.")

    actual_numbers = str(actual_numbers).replace(" ", "")
    if len(actual_numbers.split(",")) != 22:
        raise ValueError(f"Actual22 번호 개수가 22개가 아닙니다. 실제 데이터: '{actual_numbers}'")

    return int(latest_row['Round']), actual_numbers

# 추천 번호 저장 (Google Sheets)
def save_recommended_numbers(round_no, numbers, tag):
    try:
        client = authenticate_google()
        sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
        sheet = client.open_by_key(sheet_id).worksheet("F10")
        today_date = pd.Timestamp.now().strftime("%Y-%m-%d")

        if isinstance(numbers, list):
            numbers = ",".join([f"{int(num):02d}" for num in sorted(numbers)])
        else:
            numbers = ",".join(sorted([f"{int(num):02d}" for num in numbers.split(",")]))

        round_no = int(round_no)

        sheet.append_row([today_date, round_no, tag, numbers], value_input_option="USER_ENTERED")
        print(f"✅ 저장 성공: {today_date}, {round_no}, {tag}, {numbers}")

    except Exception as e:
        print(f"❌ 저장 실패: {e}")

# GA 모델 함수
def run_ga_model(actual_numbers):
    actual_pool = [int(n) for n in actual_numbers.split(",")]

    def fitness(combo):
        return len(set(combo) & set(actual_pool))

    def generate_combo():
        return random.sample(range(1, 71), 10)

    # 반복 횟수 임시적으로 감소 (성능테스트용 아님, 속도만 확인)
    population_size = 20  # 원래는 100
    generations = 5       # 원래는 30
    mutation_rate = 0.1

    population = [generate_combo() for _ in range(population_size)]

    for _ in range(generations):
        population.sort(key=fitness, reverse=True)
        next_generation = population[:10]

        while len(next_generation) < population_size:
            parents = random.sample(population[:10], 2)  
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
    return sorted(best_combination)

# 대안 조합 생성
def generate_alternative(existing_combinations):
    while True:
        new_combo = random.sample(range(1, 71), 10)
        formatted_new_combo = ",".join(sorted([f"{num:02d}" for num in new_combo]))
        if formatted_new_combo not in existing_combinations:
            return new_combo

# 메인 작업 함수
def update_after_input():
    round_no, actual_numbers = get_latest_numbers()

    # 최적 조합
    recommended_numbers = run_ga_model(actual_numbers)
    save_recommended_numbers(round_no + 1, recommended_numbers, "Best")

    # 대안 조합 2개
    existing = {",".join([f"{num:02d}" for num in recommended_numbers])}
    for i in range(1, 3):
        alt_combo = generate_alternative(existing)
        save_recommended_numbers(round_no + 1, alt_combo, f"Alternative {i}")
        existing.add(",".join([f"{num:02d}" for num in alt_combo]))

# Flask 설정
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    try:
        update_after_input()
        return "GA 모델이 성공적으로 실행되었습니다.", 200
    except Exception as e:
        return f"GA 모델 실행 중 오류 발생: {str(e)}", 500

# 👉 디버그용 추가 라우트 (아래 코드 추가!)
@app.route("/debug_sheet")
def debug_sheet():
    try:
        client = authenticate_google()
        sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
        sheet = client.open_by_key(sheet_id).worksheet("F10")
        sheet.append_row(["2025-05-05", "999999", "DebugTest", "01,02,03,04,05"], value_input_option="USER_ENTERED")
        return "✅ 직접 추가 성공", 200
    except Exception as e:
        return f"❌ 직접 추가 실패: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 10000)))

