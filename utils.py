import random

# 강력한 Real GA Optimized 전략 (population & generations 대폭 증가)
def real_ga_optimized(actual_numbers):
    actual_pool = [int(n) for n in actual_numbers.split(",")]

    def fitness(combo):
        return len(set(combo) & set(actual_pool))

    def generate_combo():
        return random.sample(range(1, 71), 10)

    population_size = 200  # 대폭 증가
    generations = 50       # 대폭 증가
    mutation_rate = 0.1

    # 초기 population 생성
    population = [generate_combo() for _ in range(population_size)]

    for _ in range(generations):
        population.sort(key=fitness, reverse=True)
        next_generation = population[:population_size // 2]

        while len(next_generation) < population_size:
            parents = random.sample(population[:population_size // 2], 2)
            crossover_point = random.randint(1, 9)
            child = parents[0][:crossover_point] + parents[1][crossover_point:]

            if random.random() < mutation_rate:
                mutation_index = random.randint(0, 9)
                new_num = random.randint(1, 70)
                while new_num in child:
                    new_num = random.randint(1, 70)
                child[mutation_index] = new_num

            # 중복 완벽 방지
            child = list(set(child))
            while len(child) < 10:
                extra_num = random.randint(1, 70)
                if extra_num not in child:
                    child.append(extra_num)

            next_generation.append(child)

        population = next_generation

    best_combination = max(population, key=fitness)
    return ",".join([f"{num:02d}" for num in sorted(best_combination)])
