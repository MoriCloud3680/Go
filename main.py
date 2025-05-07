from flask import Flask
from utils import fetch_current_round, ga_recent_best, update_recommendations

app = Flask(__name__)

last_generated_round = None

@app.route("/", methods=["GET"])
def home():
    global last_generated_round

    current_round = fetch_current_round()
    next_round = current_round + 1

    if next_round != last_generated_round:
        try:
            recent_best_numbers = ga_recent_best()
            update_recommendations(next_round, recent_best_numbers, "GA Recent5 Best")
            last_generated_round = next_round
            return f"✅ {next_round}회차 GA Recent5 Best 조합 생성 완료.", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {next_round}회차는 이미 처리됨.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
