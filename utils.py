import os
import json
import gspread
from google.oauth2.service_account import Credentials

def get_gspread_client():
    creds_json = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
    creds = Credentials.from_service_account_info(creds_json)
    client = gspread.authorize(creds)
    return client

def run_ga_and_save():
    client = get_gspread_client()
    sheet = client.open('GA_Results').sheet1
    # 네 기존 GA 작업 진행 (예측 결과 저장 로직 등...)
