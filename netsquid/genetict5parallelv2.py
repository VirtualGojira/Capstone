import numpy as np
import random
from joblib import Parallel, delayed
from prept5 import avg_100_runs


# Parameters for the genetic algorithm and KEM protocol
DISTANCE_MIN = 1   # Minimum distance (in meters)
DISTANCE_MAX = 200  # Maximum distance (in meters)
TIMEOUT_MIN = 1  # Minimum timeout (in ns)
TIMEOUT_MAX = 1e9  # Maximum timeout (in ns)
MAX_RETRIES_MIN = 1 # Minimum max_retries
MAX_RETRIES_MAX = 10# Maximum max_retries
NO_OF_BITS = 24     #no of bits
POPULATION_SIZE = 20# Size of the population
GENERATIONS = 20    # Number of generations for the genetic algorithm
MUTATION_RATE = 0.1 # Mutation rate
ACCURACY_THRESHOLD = 95  # Accuracy threshold to aim for

# Function to evaluate the accuracy based on the current parameters
def evaluate_accuracy(n_bits, distance, timeout, max_retries):
    success_count = avg_100_runs(n_bits, distance, timeout, max_retries)
    accuracy = (success_count / 100) * 100  # Return accuracy as a percentage
    return accuracy

# Function to generate a random chromosome (combination of parameters)
def create_chromosome():
    distance = random.randint(DISTANCE_MIN, DISTANCE_MAX)  # Random distance between 50 and 500 meters
    timeout = random.uniform(TIMEOUT_MIN, TIMEOUT_MAX)  # Random timeout between 1e10 and 1e12 ns
    max_retries = random.randint(MAX_RETRIES_MIN, MAX_RETRIES_MAX)  # Random max_retries between 5 and 20
    return [distance, timeout, max_retries]

# Function for crossover between two parents
def crossover(parent1, parent2):
    crossover_point = random.randint(1, 2)  # Random crossover point between distance, timeout, max_retries
    offspring1 = parent1[:crossover_point] + parent2[crossover_point:]
    offspring2 = parent2[:crossover_point] + parent1[crossover_point:]
    return offspring1, offspring2

# Function for mutation
def mutate(chromosome):
    mutation_point = random.randint(0, 2)  # Choose a parameter to mutate (distance, timeout, max_retries)
    if mutation_point == 0:  # Mutate distance
        chromosome[0] = random.randint(DISTANCE_MIN, DISTANCE_MAX)
    elif mutation_point == 1:  # Mutate timeout
        chromosome[1] = random.uniform(TIMEOUT_MIN, TIMEOUT_MAX)
    else:  # Mutate max_retries
        chromosome[2] = random.randint(MAX_RETRIES_MIN, MAX_RETRIES_MAX)
    return chromosome

# Function to evaluate the fitness of a single chromosome
def evaluate_fitness(chromosome, n_bits=NO_OF_BITS):
    distance, timeout, max_retries = chromosome
    accuracy = evaluate_accuracy(n_bits, distance, timeout, max_retries)
    return accuracy, chromosome

# Genetic Algorithm function to optimize distance, timeout, and max_retries
def genetic_algorithm(n_bits, population_size=POPULATION_SIZE, generations=GENERATIONS, mutation_rate=MUTATION_RATE, accuracy_threshold=ACCURACY_THRESHOLD):
    population = [create_chromosome() for _ in range(population_size)]
    best_solution = None
    best_accuracy = 0
    
    for generation in range(generations):
        print(f"Generation {generation+1}/{generations}")
        
        # Parallelize fitness evaluation using Joblib
        fitness_values = Parallel(n_jobs=-1)(delayed(evaluate_fitness)(chromosome) for chromosome in population)
        
        # Sort the population by fitness (accuracy)
        fitness_values.sort(reverse=True, key=lambda x: x[0])
        
        # Update the best solution
        if fitness_values[0][0] > best_accuracy:
            best_accuracy = fitness_values[0][0]
            best_solution = fitness_values[0][1]
        
        # Selection: Select the top 50% of the population based on fitness
        selected_population = [chromosome for _, chromosome in fitness_values[:population_size // 2]]
        
        # Crossover: Generate new population by crossover
        new_population = []
        while len(new_population) < population_size:
            parent1, parent2 = random.sample(selected_population, 2)
            offspring1, offspring2 = crossover(parent1, parent2)
            new_population.append(offspring1)
            new_population.append(offspring2)
        
        # Mutation: Apply mutation to the new population
        for i in range(len(new_population)):
            if random.random() < mutation_rate:
                new_population[i] = mutate(new_population[i])
        
        # Update the population with the new population
        population = new_population

    # Return the best solution found after all generations
    return best_solution, best_accuracy

# Run the genetic algorithm to optimize the parameters
best_solution, best_accuracy = genetic_algorithm(n_bits=NO_OF_BITS, population_size=POPULATION_SIZE, generations=GENERATIONS)

print(f"Best solution: Distance = {best_solution[0]} meters, Timeout = {best_solution[1]} ns, Max Retries = {best_solution[2]}")
print(f"Best accuracy: {best_accuracy}%")
