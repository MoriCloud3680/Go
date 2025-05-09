from flask import Flask
from itertools import combinations
from collections import Counter
from utils import authenticate_google, fetch_latest_rounds, get_last_generated_round, update_last_generated_round, update_recommendations
import traceback

app = Flask(__name__)

def find_pairwise_relations(numbers_history):
    pair_relations = {}
    for i in range(len(numbers_history) - 1):
        current_round_nums = numbers_history[i]
        next_round_nums = numbers_history[i + 1]
        for pair in combinations(current_round_nums, 2):
            if pair not in pair_relations:
                pair_relations[pair] = Counter()
            pair_relations[pair].update(next_round_nums)
    return pair_relations

def recommend_pairwise(prev_round_nums, pair_relations, top_n=10):
    recommended_counter = Counter()
    prev_pairs = combinations(prev_round_nums, 2)
    
    for pair in prev_pairs:
        if pair in pair_relations:
            recommended_counter.update(pair_relations[pair])

    # 만약 페어링 기반 추천이 없다면, 전체 가장 빈도 높은 번호를 사용
    if not recommended_counter:
        # 최근 회차의 전체 번호 빈도 집계 (페어 관계가 없을 때 대비용)
        all_numbers = [num for nums in pair_relations.values() for num in nums]
        recommended_counter = Counter(all_numbers)
    
    # 그래도 번호가 없으면 임의로 번호를 생성
    if not recommended_counter:
        return random.sample(range(1, 71), top_n)

    recommended_numbers = [num for num, _ in recommended_counter.most_common(top_n)]
    return recommended_numbers

    recommended_numbers = [num for num, _ in recommended_counter.most_common(top_n)]
    return recommended_numbers

@app.route("/", methods=["GET"])
def home():
    current_round, previous_numbers_sets = fetch_latest_rounds(n=30)
    next_round = current_round + 1
    last_generated_round = get_last_generated_round()

    if next_round != last_generated_round:
        try:
            pair_relations = find_pairwise_relations(previous_numbers_sets)
            prev_round_numbers = previous_numbers_sets[0]  # 직전 1회차만 참조
            recommended_numbers = recommend_pairwise(prev_round_numbers, pair_relations)

            update_recommendations(next_round, recommended_numbers, "Pairwise Strategy")
            update_last_generated_round(next_round)

            return f"✅ {next_round}회차 Pairwise 전략 조합 생성 완료: {recommended_numbers}", 200
        except Exception as e:
            detailed_error = traceback.format_exc()
            return f"❌ 오류 발생: {str(e)}<br><pre>{detailed_error}</pre>", 500
    else:
        return f"⚠️ {next_round}회차 이미 생성됨", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
from itertools import combinations
from collections import Counter
from utils import authenticate_google, fetch_latest_rounds, get_last_generated_round, update_last_generated_round, update_recommendations
import traceback

app = Flask(__name__)

def find_pairwise_relations(numbers_history):
    pair_relations = {}
    for i in range(len(numbers_history) - 1):
        current_round_nums = numbers_history[i]
        next_round_nums = numbers_history[i + 1]
        for pair in combinations(current_round_nums, 2):
            if pair not in pair_relations:
                pair_relations[pair] = Counter()
            pair_relations[pair].update(next_round_nums)
    return pair_relations

def recommend_pairwise(prev_round_nums, pair_relations, top_n=10):
    recommended_counter = Counter()
    prev_pairs = combinations(prev_round_nums, 2)
    for pair in prev_pairs:
        if pair in pair_relations:
            recommended_counter.update(pair_relations[pair])

    recommended_numbers = [num for num, _ in recommended_counter.most_common(top_n)]
    return recommended_numbers

@app.route("/", methods=["GET"])
def home():
    current_round, previous_numbers_sets = fetch_latest_rounds(n=30)
    next_round = current_round + 1
    last_generated_round = get_last_generated_round()

    if next_round != last_generated_round:
        try:
            pair_relations = find_pairwise_relations(previous_numbers_sets)
            prev_round_numbers = previous_numbers_sets[0]  # 직전 1회차만 참조
            recommended_numbers = recommend_pairwise(prev_round_numbers, pair_relations)

            update_recommendations(next_round, recommended_numbers, "Pairwise Strategy")
            update_last_generated_round(next_round)

            return f"✅ {next_round}회차 Pairwise 전략 조합 생성 완료: {recommended_numbers}", 200
        except Exception as e:
            detailed_error = traceback.format_exc()
            return f"❌ 오류 발생: {str(e)}<br><pre>{detailed_error}</pre>", 500
    else:
        return f"⚠️ {next_round}회차 이미 생성됨", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
