import numpy as np
import random
import matplotlib.pyplot as plt
from prept5 import avg_100_runs
from multiprocessing import Pool

# Parameters for the genetic algorithm and KEM protocol
DISTANCE_MIN = 1
DISTANCE_MAX = 200
TIMEOUT_MIN = 1
TIMEOUT_MAX = 1e9
MAX_RETRIES_MIN = 1
MAX_RETRIES_MAX = 10
NO_OF_BITS = 24
POPULATION_SIZE = 20
GENERATIONS = 50
MUTATION_RATE = 0.1
ACCURACY_THRESHOLD = 95

# Function to evaluate the accuracy based on the current parameters
def evaluate_accuracy(n_bits, distance, timeout, max_retries):
    success_count = avg_100_runs(n_bits, distance, timeout, max_retries)
    return success_count  # Return accuracy as a percentage

# Function to generate a random chromosome
def create_chromosome():
    distance = random.randint(DISTANCE_MIN, DISTANCE_MAX)
    timeout = random.uniform(TIMEOUT_MIN, TIMEOUT_MAX)
    max_retries = random.randint(MAX_RETRIES_MIN, MAX_RETRIES_MAX)
    return [distance, timeout, max_retries]

# Function for crossover
def crossover(parent1, parent2):
    crossover_point = random.randint(1, 2)
    offspring1 = parent1[:crossover_point] + parent2[crossover_point:]
    offspring2 = parent2[:crossover_point] + parent1[crossover_point:]
    return offspring1, offspring2

# Function for mutation
def mutate(chromosome):
    mutation_point = random.randint(0, 2)
    if mutation_point == 0:
        chromosome[0] = random.randint(DISTANCE_MIN, DISTANCE_MAX)
    elif mutation_point == 1:
        chromosome[1] = random.uniform(TIMEOUT_MIN, TIMEOUT_MAX)
    else:
        chromosome[2] = random.randint(MAX_RETRIES_MIN, MAX_RETRIES_MAX)
    return chromosome

# Function to evaluate the fitness of a chromosome
def evaluate_fitness(chromosome):
    distance, timeout, max_retries = chromosome
    accuracy = evaluate_accuracy(NO_OF_BITS, distance, timeout, max_retries)
    return accuracy, chromosome

# Genetic Algorithm function
def genetic_algorithm(n_bits, population_size=POPULATION_SIZE, generations=GENERATIONS, mutation_rate=MUTATION_RATE):
    population = [create_chromosome() for _ in range(population_size)]
    best_solution = None
    best_accuracy = 0
    
    best_fitness_values = []
    avg_fitness_values = []
    worst_fitness_values = []

    for generation in range(generations):
        print(f"Generation {generation+1}/{generations}")
        
        with Pool() as pool:
            fitness_values = pool.map(evaluate_fitness, population)
        
        fitness_values.sort(reverse=True, key=lambda x: x[0])
        
        accuracies = [x[0] for x in fitness_values]
        best_fitness_values.append(max(accuracies))
        avg_fitness_values.append(sum(accuracies) / len(accuracies))
        worst_fitness_values.append(min(accuracies))

        if fitness_values[0][0] > best_accuracy:
            best_accuracy = fitness_values[0][0]
            best_solution = fitness_values[0][1]
        
        selected_population = [chromosome for _, chromosome in fitness_values[:population_size // 2]]
        
        new_population = []
        while len(new_population) < population_size:
            parent1, parent2 = random.sample(selected_population, 2)
            offspring1, offspring2 = crossover(parent1, parent2)
            new_population.append(offspring1)
            new_population.append(offspring2)
        
        for i in range(len(new_population)):
            if random.random() < mutation_rate:
                new_population[i] = mutate(new_population[i])
        
        population = new_population

    # Plot fitness evolution
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, generations+1), best_fitness_values, label="Best Fitness", color="blue")
    plt.plot(range(1, generations+1), avg_fitness_values, label="Average Fitness", color="green")
    plt.plot(range(1, generations+1), worst_fitness_values, label="Worst Fitness", color="red")
    
    plt.xlabel("Generation")
    plt.ylabel("Fitness (Accuracy)")
    plt.title("Genetic Algorithm: Population Fitness Evolution")
    plt.legend()
    plt.grid()

    # Save the plot as a PNG file
    plt.savefig('fitness_evolution.eps', format='eps', dpi=600)
    plt.close()  # Close the figure to free memory

    print("Plot saved as 'fitness_evolution.png'")

    return best_solution, best_accuracy

# Run the genetic algorithm
best_solution, best_accuracy = genetic_algorithm(n_bits=NO_OF_BITS)

print(f"Best solution: Distance = {best_solution[0]} meters, Timeout = {best_solution[1]} ns, Max Retries = {best_solution[2]}")
print(f"Best accuracy: {best_accuracy}%")
