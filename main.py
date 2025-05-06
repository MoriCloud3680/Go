from flask import Flask
from utils import fetch_current_round, prev_best, update_recommendations

app = Flask(__name__)

last_generated_round = None

@app.route("/", methods=["GET"])
def home():
    global last_generated_round
    current_round, actual_numbers = fetch_current_round()
    next_round = current_round + 1

    if next_round != last_generated_round:
        try:
            # 메인 Prev Best 전략 1개 + Alt 2개 조합 생성
            main_combo = prev_best(actual_numbers)
            alt_combo1 = prev_best(actual_numbers)
            alt_combo2 = prev_best(actual_numbers)

            # 구글 시트 업데이트
            update_recommendations(next_round, main_combo, "Prev Best Main")
            update_recommendations(next_round, alt_combo1, "Prev Best Alt 1")
            update_recommendations(next_round, alt_combo2, "Prev Best Alt 2")

            last_generated_round = next_round

            return f"✅ {next_round}회차 Prev Best 조합(메인+Alt) 생성 완료.", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {next_round}회차는 이미 처리됨.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
