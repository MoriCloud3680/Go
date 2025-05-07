from utils import fetch_current_round, update_recommendations, real_ga_optimized

def run_single_optimized_ga():
    current_round, _, hot_numbers, cold_numbers = fetch_current_round()
    next_round = current_round + 1

    # GA 전략 단 1회만 실행
    numbers = real_ga_optimized(hot_numbers, cold_numbers)
    update_recommendations(next_round, numbers, "Real GA Optimized (Hot/Cold)")

if __name__ == "__main__":
    run_single_optimized_ga()
