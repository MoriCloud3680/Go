import os
import json
import gspread
from google.oauth2.service_account import Credentials

# OAuth scope 설정 추가 (이 부분이 핵심!)
def get_gspread_client():
    creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file"
    ]
    creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
    client = gspread.authorize(creds)
    return client

# 기존 코드 유지 (run_ga_and_save 함수)
def run_ga_and_save():
    client = get_gspread_client()
    sheet = client.open('GA_Results').sheet1

    # 너가 작성한 기존 GA 로직을 여기에 유지하면 돼.
