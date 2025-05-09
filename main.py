import os
import json
import gspread
from flask import Flask
from oauth2client.service_account import ServiceAccountCredentials
from collections import defaultdict
from functools import lru_cache

app = Flask(__name__)

@lru_cache(maxsize=1)
def authenticate_google():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    return gspread.authorize(creds)

def fetch_latest_round():
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Actual22")
    round_no = int(sheet.acell('A2').value)
    actual_numbers = list(map(int, sheet.acell('B2').value.replace(" ", "").split(",")))
    return round_no, actual_numbers

def get_last_generated_round():
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Status")
    last_round = sheet.acell('A2').value
    return int(last_round) if last_round else 0

def update_last_generated_round(round_no):
    client = authenticate_google()
    sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("Status")
    sheet.update('A2', str(round_no))

def update_recommendations(round_no, numbers, tag):
    client = authenticate_google()
    f10_sheet = client.open_by_key("1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo").worksheet("F10")
    numbers_str = ",".join(map(str, numbers))
    f10_sheet.insert_row([round_no, tag, numbers_str], 2, value_input_option="USER_ENTERED")

def high_density_cluster_strategy(numbers):
    intervals = defaultdict(list)
    for num in numbers:
        interval = (num - 1) // 10
        intervals[interval].append(num)

    dense_intervals = [nums for nums in intervals.values() if len(nums) >= 3]
    dense_numbers = [num for nums in dense_intervals for num in nums]

    candidate_numbers = []
    for num in numbers[:10]:
        if num in dense_numbers:
            candidate_numbers.append(num)
        else:
            mirror_num = 70 - num
            candidate_numbers.append(mirror_num if 1 <= mirror_num <= 70 else num)

    return sorted(candidate_numbers)

@app.route("/", methods=["GET"])
def home():
    current_round, actual_numbers = fetch_latest_round()
    next_round = current_round + 1
    last_generated_round = get_last_generated_round()

    if next_round != last_generated_round:
        try:
            recommended_numbers = high_density_cluster_strategy(actual_numbers)
            update_recommendations(next_round, recommended_numbers, "High-Density Cluster")
            update_last_generated_round(next_round)
            return f"✅ {next_round}회차 High-Density Cluster 조합 생성 완료", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {next_round}회차 이미 생성됨", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
