import os
import json
import random
from flask import Flask
from utils import fetch_current_round, update_recommendations, run_adaptive_ga

app = Flask(__name__)
last_generated_round = None

@app.route("/", methods=["GET"])
def home():
    global last_generated_round

    current_round, actual_numbers = fetch_current_round()
    next_round = current_round + 1

    if next_round != last_generated_round:
        try:
            ga_numbers = run_adaptive_ga(actual_numbers)
            formatted_ga_numbers = ",".join([f"{num:02d}" for num in ga_numbers])

            update_recommendations(next_round, formatted_ga_numbers, "Adaptive GA Optimized")
            last_generated_round = next_round

            return f"✅ {next_round}회차 Adaptive GA 조합 생성 완료.", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {next_round}회차는 이미 처리됨.", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # Render의 환경변수 PORT를 사용하도록 수정
    app.run(host='0.0.0.0', port=port)
