import random, gspread
from oauth2client.service_account import ServiceAccountCredentials

def run_ga_and_save():
    # 번호 생성 (랜덤으로 22개 숫자)
    numbers = sorted(random.sample(range(1, 71), 22))
    
    # Google Sheets 연결
    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    
    sheet = client.open('GA_Results').sheet1
    sheet.append_row(numbers)
