import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np
import pandas as pd
import joblib
from tensorflow.keras.models import load_model

def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    client = gspread.authorize(creds)
    return client

def fetch_latest_data():
    client = authenticate_google()
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo/edit#gid=0").worksheet("ActualNumbers")
    round_no = int(sheet.acell("A2").value)
    numbers_str = sheet.acell("B2").value
    numbers = list(map(int, numbers_str.replace(" ", "").split(",")))
    return round_no, numbers

def update_predictions(round_no, predicted_numbers):
    client = authenticate_google()
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo/edit#gid=0").worksheet("Predicted")
    numbers_str = ",".join(map(str, predicted_numbers))
    sheet.insert_row([round_no, numbers_str], 2, value_input_option="USER_ENTERED")

def update_status(round_no):
    client = authenticate_google()
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo/edit#gid=0").worksheet("Status")
    sheet.update_acell("A2", round_no)
