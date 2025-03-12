import numpy as np
import random
import csv
from prept5 import avg_100_runs
from multiprocessing import Pool

# Parameters for the genetic algorithm and KEM protocol
DISTANCE_MIN = 1   # Minimum distance (in meters)
DISTANCE_MAX = 200  # Maximum distance (in meters)
TIMEOUT_MIN = 1  # Minimum timeout (in ns)
TIMEOUT_MAX = 1e9  # Maximum timeout (in ns)
MAX_RETRIES_MIN = 1 # Minimum max_retries
MAX_RETRIES_MAX = 10# Maximum max_retries
POPULATION_SIZE = 20 # Size of the population
GENERATIONS = 50    # Number of generations for the genetic algorithm
MUTATION_RATE = 0.1 # Mutation rate
ACCURACY_THRESHOLD = 90  # Accuracy threshold to aim for

# Function to evaluate the accuracy based on the current parameters
def evaluate_accuracy(n_bits, distance, timeout, max_retries):
    success_count = avg_100_runs(n_bits, distance, timeout, max_retries)
    return success_count # Return accuracy as a percentage

# Function to generate a random chromosome (combination of parameters)
def create_chromosome():
    distance = random.randint(DISTANCE_MIN, DISTANCE_MAX)
    timeout = random.uniform(TIMEOUT_MIN, TIMEOUT_MAX)
    max_retries = random.randint(MAX_RETRIES_MIN, MAX_RETRIES_MAX)
    return [distance, timeout, max_retries]

# Function for crossover between two parents
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

# Function to evaluate the fitness of a single chromosome
def evaluate_fitness(chromosome, n_bits):
    distance, timeout, max_retries = chromosome
    accuracy = evaluate_accuracy(n_bits, distance, timeout, max_retries)
    fitness_value = distance if accuracy >= ACCURACY_THRESHOLD else (distance * (accuracy / 100))
    return (fitness_value, chromosome, accuracy)

# Genetic Algorithm function
def genetic_algorithm(n_bits, population_size=POPULATION_SIZE, generations=GENERATIONS, mutation_rate=MUTATION_RATE):
    population = [create_chromosome() for _ in range(population_size)]
    best_solution = None
    best_accuracy = 0
    
    for generation in range(generations):
        print(f"Generation {generation+1}/{generations} for {n_bits} bits")
        
        with Pool() as pool:
            fitness_values = pool.starmap(evaluate_fitness, [(chromosome, n_bits) for chromosome in population])
        
        fitness_values.sort(reverse=True, key=lambda x: x[0])
        
        if fitness_values[0][2] > best_accuracy:
            best_accuracy = fitness_values[0][2]
            best_solution = fitness_values[0][1]
        
        selected_population = [chromosome for _, chromosome, _ in fitness_values[:population_size // 2]]
        
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
    
    return best_solution, best_accuracy

# Run the genetic algorithm for different bit sizes and save results
bit_sizes = [2**i for i in range(1, 9)]  # 2, 4, 8, ..., 256
results = []

for bits in bit_sizes:
    best_solution, best_accuracy = genetic_algorithm(n_bits=bits)
    results.append([bits, best_solution[0], best_solution[1], best_solution[2], best_accuracy])
    print(f"Best for {bits} bits: Distance = {best_solution[0]}, Timeout = {best_solution[1]}, Max Retries = {best_solution[2]}, Accuracy = {best_accuracy}%")

# Save results to CSV
csv_filename = "genetic_algorithm_results.csv"
with open(csv_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Bits", "Distance", "Timeout (ns)", "Max Retries", "Accuracy (%)"])
    writer.writerows(results)

print(f"Results saved to {csv_filename}")
