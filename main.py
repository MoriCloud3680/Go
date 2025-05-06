from flask import Flask
from utils import fetch_current_round, prev_best, ga_best, ga_recent_best, update_recommendations, real_ga_optimization, authenticate_google
import gspread

app = Flask(__name__)

# 이번 회차가 이미 존재하는지 체크하는 함수
def check_already_generated(round_no):
    client = authenticate_google()
    sheet_id = "1P-kCWRZk0YJFokgQuwVpxg_dKz78xN0PqwBmgtf63fo"
    f10_sheet = client.open_by_key(sheet_id).worksheet("F10")
    existing_rounds = f10_sheet.col_values(2)  # B열 (round_no) 전체값 가져오기
    return str(round_no) in existing_rounds

@app.route("/", methods=["GET"])
def home():
    current_round, actual_numbers = fetch_current_round()
    next_round = current_round + 1

    # 이미 생성된 회차인지 확인
    if check_already_generated(next_round):
        return f"⚠️ {next_round}회차는 이미 생성됨. 추가 생성 없음.", 200

    try:
        pb_numbers = prev_best(actual_numbers)
        ga_numbers = ga_best(actual_numbers)
        ga_recent_numbers = ga_recent_best()
        real_ga_numbers = real_ga_optimization()

        # 새 조합을 1회만 추가
        update_recommendations(next_round, pb_numbers, "Prev Best")
        update_recommendations(next_round, ga_numbers, "GA Best")
        update_recommendations(next_round, ga_recent_numbers, "GA Recent5 Best")
        update_recommendations(next_round, real_ga_numbers, "Real GA Optimized")

        return f"✅ {next_round}회차 조합 최초 1회 생성 완료.", 200

    except Exception as e:
        return f"❌ 오류 발생: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
