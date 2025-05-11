import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

def authenticate_google():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    with open('credentials.json') as f:
        credentials_dict = json.load(f)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    return gspread.authorize(creds)
