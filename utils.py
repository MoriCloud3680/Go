import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Google 인증
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

# 가장 최근의 회차 번호와 당첨번호 불러오기
def get_latest_numbers():
    client = authenticate_google()
    sheet = client.open("Go").worksheet("Actual22")
    df = pd.DataFrame(sheet.get_all_records())
    df['Round'] = pd.to_numeric(df['Round'])
    latest_row = df.loc[df['Round'].idxmax()]
    return int(latest_row['Round']), latest_row['Actual22']

# GA (유전자 알고리즘) 모델 구현 (네가 이미 쓰던 코드)
def run_ga_model(actual_numbers):
    # 실제 GA 모델 코드 삽입 (이전 conversation에서 사용한 코드)
    import random
    numbers_pool = [int(n) for n in actual_numbers.split(",")]
    recommended_numbers = random.sample(numbers_pool, 10)  # 이 부분을 너의 GA 모델로 변경해야 함
    recommended_numbers.sort()
    return ",".join([f"{num:02d}" for num in recommended_numbers])

# 여러 조합 생성 (실제 GA 기반)
def generate_multiple_recommendations(actual_numbers, num_combinations=3):
    recommendations = []
    for _ in range(num_combinations):
        combo = run_ga_model(actual_numbers)
        recommendations.append(combo)
    return recommendations

# 추천번호 저장
def save_recommended_numbers(round_no, numbers_list):
    client = authenticate_google()
    sheet = client.open("Go").worksheet("F10")
    today_date = pd.Timestamp.now().strftime("%Y-%m-%d")

    for numbers in numbers_list:
        sheet.append_row([today_date, round_no, numbers])

# 메인 함수 (Render에서 실행될 부분)
def update_after_input():
    latest_round, actual_numbers = get_latest_numbers()
    recommended_numbers_list = generate_multiple_recommendations(actual_numbers, num_combinations=3)
    save_recommended_numbers(latest_round + 1, recommended_numbers_list)
