from flask import Flask
from utils import fetch_current_round, prev_best, update_recommendations, is_round_processed

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    current_round, actual_numbers = fetch_current_round()
    next_round = current_round + 1

    # 이미 처리된 회차면 생성하지 않음
    if is_round_processed(next_round):
        return f"⚠️ {next_round}회차는 이미 생성된 회차입니다.", 200

    try:
        # 단 하나의 Prev Best 조합만 생성
        main_combo = prev_best(actual_numbers)

        # 구글 시트에 기록
        update_recommendations(next_round, main_combo, "Prev Best Main")

        return f"✅ {next_round}회차 Prev Best Main 조합 생성 완료: {main_combo}", 200

    except Exception as e:
        return f"❌ 오류 발생: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
