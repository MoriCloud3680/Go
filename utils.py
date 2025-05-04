import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

def authenticate_google():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('키파일이름.json', scope)
    client = gspread.authorize(creds)
    return client

# 실제 번호 가져오기
def get_latest_numbers():
    client = authenticate_google()
    sheet = client.open("너의 구글시트이름").worksheet("실제번호입력")
    data = sheet.get_all_records()
    latest_row = data[-1]
    return latest_row['Round'], latest_row['Numbers(22개)']

# 추천 번호 저장하기
def save_recommended_numbers(round_no, numbers):
    client = authenticate_google()
    sheet = client.open("너의 구글시트이름").worksheet("자동추천번호")
    today_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    sheet.append_row([today_date, round_no, numbers])

# 추천 로직 (기존 모델을 여기에 넣어!)
def generate_recommendation(actual_numbers):
    # 예시: 실제 모델 로직을 넣어야 해!
    recommended_10_numbers = actual_numbers.split(",")[:10] # 일단 앞에 10개 번호로 예시
    return ",".join(recommended_10_numbers)

# 이 함수를 Render Flask에서 호출하게 만들어
def update_after_input():
    round_no, actual_numbers = get_latest_numbers()
    recommended_numbers = generate_recommendation(actual_numbers)
    save_recommended_numbers(round_no + 1, recommended_numbers)
