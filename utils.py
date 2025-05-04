import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import random

# Google 인증 및 클라이언트 생성
def authenticate_google():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']

    creds_json = os.getenv("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# 최신회차 번호와 실제 번호 가져오기
def get_latest_numbers():
    client = authenticate_google()
    sheet = client.open("Go").worksheet("Actual22")
    data = sheet.get_all_records()

    # 최신회차 번호로 구분
    latest_row = max(data, key=lambda x: x['Round'])
    return latest_row['Round'], latest_row['Actual22']

# 추천 번호 저장 (여러 조합 가능)
def save_recommended_numbers(round_no, recommended_numbers_list):
    client = authenticate_google()
    sheet = client.open("Go").worksheet("F10")
    today_date = pd.Timestamp.now().strftime("%Y-%m-%d")

    for numbers in recommended_numbers_list:
        numbers_formatted = ",".join(f"{num:02d}" for num in numbers)
        sheet.append_row([today_date, round_no, numbers_formatted])

# GA 모델을 이용한 추천 번호 생성 (실제 구현)
def run_ga_model(actual_numbers):
    # actual_numbers가 int라면 str로 변환
    if isinstance(actual_numbers, int):
        actual_numbers = str(actual_numbers)

    # 콤마가 있으면 분리, 없으면 숫자 2자리씩 분리
    if ',' in actual_numbers:
        numbers_pool = [int(n) for n in actual_numbers.split(",")]
    else:
        numbers_pool = [int(actual_numbers[i:i+2]) for i in range(0, len(actual_numbers), 2)]

    # 실제 GA 로직 (간단 예시)
    recommended_numbers = random.sample(numbers_pool, 10)
    return recommended_numbers

# 여러 개의 추천번호 생성
def generate_multiple_recommendations(actual_numbers, num_combinations=3):
    recommendations = []
    for _ in range(num_combinations):
        combo = run_ga_model(actual_numbers)
        recommendations.append(combo)
    return recommendations

# Render에서 호출되는 메인 함수
def update_after_input():
    round_no, actual_numbers = get_latest_numbers()
    recommended_numbers_list = generate_multiple_recommendations(actual_numbers, num_combinations=3)
    save_recommended_numbers(round_no + 1, recommended_numbers_list)
