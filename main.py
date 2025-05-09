from itertools import combinations
from collections import Counter
from utils import fetch_latest_rounds, update_recommendations, get_last_generated_round, update_last_generated_round

# 나머지 전략 코드 유지
current_round, previous_numbers_sets = fetch_latest_rounds(n=30)

# 이후 전략 로직 그대로 유지

# Step 1: Pairwise Relation Analysis

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

pair_relations = find_pairwise_relations(previous_numbers_sets)

# Step 2: Recommendation Based on Pairwise Relations

def recommend_pairwise(prev_round_nums, pair_relations, top_n=10):
    recommended_counter = Counter()
    prev_pairs = combinations(prev_round_nums, 2)
    for pair in prev_pairs:
        if pair in pair_relations:
            recommended_counter.update(pair_relations[pair])

    recommended_numbers = [num for num, _ in recommended_counter.most_common(top_n)]
    return recommended_numbers

# Step 3: Generate and Update Recommendations
next_round = current_round + 1
last_generated_round = get_last_generated_round()

if next_round != last_generated_round:
    try:
        prev_round_numbers = previous_numbers_sets[0]  # 직전 1회차만 참조
        recommended_numbers = recommend_pairwise(prev_round_numbers, pair_relations)

        update_recommendations(next_round, recommended_numbers, "Pairwise Strategy")
        update_last_generated_round(next_round)

        print(f"✅ {next_round}회차 Pairwise 전략 조합 생성 완료: {recommended_numbers}")

    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
else:
    print(f"⚠️ {next_round}회차 이미 생성됨")
