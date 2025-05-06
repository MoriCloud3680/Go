from flask import Flask
from utils import fetch_current_round, prev_best, ga_best, ga_recent_best, real_ga_optimization, update_recommendations

app = Flask(__name__)

# 최근 생성한 회차 기록 (전역변수)
last_generated_round = None

@app.route("/", methods=["GET"])
def home():
    global last_generated_round

    current_round, actual_numbers = fetch_current_round()
    next_round = current_round + 1

    # 이미 처리된 회차는 다시 실행되지 않음
    if next_round != last_generated_round:
        try:
            # 전략별 번호 생성 (각각 1회씩만)
            pb_numbers = prev_best(actual_numbers)
            ga_numbers = ga_best(actual_numbers)
            ga_recent_numbers = ga_recent_best()
            real_ga_numbers = real_ga_optimization()

            # Google Sheet에 저장
            update_recommendations(next_round, pb_numbers, "Prev Best")
            update_recommendations(next_round, ga_numbers, "GA Best")
            update_recommendations(next_round, ga_recent_numbers, "GA Recent5 Best")
            update_recommendations(next_round, real_ga_numbers, "Real GA Optimized")

            last_generated_round = next_round

            return f"✅ {next_round}회차 조합 생성 완료.", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {next_round}회차는 이미 처리됨.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
