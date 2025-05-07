from flask import Flask
from utils import fetch_current_round, update_recommendations, get_last_generated_round, update_last_generated_round
import random

app = Flask(__name__)

def ga_recent_best(actual_numbers):
    recent_nums = [int(n) for n in actual_numbers.split(",")]
    fixed_nums = random.sample(recent_nums, 5)
    remaining_pool = [n for n in range(1, 71) if n not in fixed_nums]
    random_nums = random.sample(remaining_pool, 5)
    combined_nums = sorted(fixed_nums + random_nums)
    return ",".join([f"{num:02d}" for num in combined_nums])

@app.route("/", methods=["GET"])
def home():
    current_round, actual_numbers = fetch_current_round()
    next_round = current_round + 1

    last_generated_round = get_last_generated_round()

    if next_round != last_generated_round:
        try:
            numbers = ga_recent_best(actual_numbers)
            update_recommendations(next_round, numbers, "GA Recent5 Best")
            update_last_generated_round(next_round)
            return f"✅ {next_round}회차 조합 생성 완료: {numbers}", 200
        except Exception as e:
            return f"❌ 오류 발생: {str(e)}", 500
    else:
        return f"⚠️ {next_round}회차는 이미 생성 완료됨.", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
