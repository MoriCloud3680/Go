import os
import json
import gspread
from google.oauth2.service_account import Credentials

# ↓ 이 부분만 추가해 주면 끝!
def get_gspread_client():
    creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds = Credentials.from_service_account_info(creds_json)
    client = gspread.authorize(creds)
    return client

# ↓ 기존의 너가 쓰던 코드 그대로 유지
def run_ga_and_save():
    client = get_gspread_client()  # 이 부분만 변경하면 돼!
    sheet = client.open('GA_Results').sheet1
    
    # 기존 너의 GA 작업 코드...
