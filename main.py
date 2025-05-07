import os
import json
import random
import gspread
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

last_generated_round = None

# 구글 인증 함수
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

# 최신 회차 번호 및 데이터 가져오기
def fetch_current_round():
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Actual22")
    round_no = int(sheet.acell('A2').value)
    actual_numbers = sheet.acell('B2').value.replace(" ", "")
    return round_no, actual_numbers

# GA Recent5 Best 조합 생성 함수
def ga_recent5_best():
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN
