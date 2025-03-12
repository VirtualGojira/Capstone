import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
from multiprocessing import Pool
from prept5 import avg_100_runs

# Parameters for the genetic algorithm and KEM protocol
DISTANCE_MIN = 1   # Minimum distance (in meters)
DISTANCE_MAX = 200  # Maximum distance (in meters)
TIMEOUT_MIN = 1  # Minimum timeout (in ns)
TIMEOUT_MAX = 1e9  # Maximum timeout (in ns)
MAX_RETRIES_MIN = 1 # Minimum max_retries
MAX_RETRIES_MAX = 10# Maximum max_retries
NO_OF_BITS = 24     #no of bits
POPULATION_SIZE = 20 # Size of the population
GENERATIONS = 50    # Number of generations for the genetic algorithm
MUTATION_RATE = 0.1 # Mutation rate
ACCURACY_THRESHOLD = 95  # Accuracy threshold to aim for

# Store population history for visualization
population_history = []
best_fitness_history = []

def evaluate_accuracy(n_bits, distance, timeout, max_retries):
    success_count = avg_100_runs(n_bits, distance, timeout, max_retries)
    return success_count # Return accuracy as a percentage

def create_chromosome():
    distance = random.randint(DISTANCE_MIN, DISTANCE_MAX)  # Random distance between 50 and 500 meters
    timeout = random.uniform(TIMEOUT_MIN, TIMEOUT_MAX)  # Random timeout between 1e10 and 1e12 ns
    max_retries = random.randint(MAX_RETRIES_MIN, MAX_RETRIES_MAX)  # Random max_retries between 5 and 20
    return [distance, timeout, max_retries]

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

# Function to evaluate the fitness of a single chromosome (used for parallelization)
def evaluate_fitness(chromosome):
    distance, timeout, max_retries = chromosome
    accuracy = evaluate_accuracy(NO_OF_BITS, distance, timeout, max_retries)
    return accuracy, chromosome

def compute_similarity_matrix(population):
    """ Computes a similarity matrix based on distance between chromosomes."""
    size = len(population)
    similarity_matrix = np.zeros((size, size))
    
    for i in range(size):
        for j in range(size):
            similarity_matrix[i, j] = np.linalg.norm(np.array(population[i]) - np.array(population[j]))
    
    return similarity_matrix

def plot_population_similarity():
    """ Generates a heatmap of the population similarity matrix."""
    avg_matrix = np.mean([compute_similarity_matrix(gen) for gen in population_history], axis=0)
    plt.figure(figsize=(10, 8))
    sns.heatmap(avg_matrix, cmap="coolwarm", annot=False)
    plt.title("Population Similarity Heatmap")
    plt.xlabel("Individual Index")
    plt.ylabel("Individual Index")
    plt.savefig("population_heatmap.png")
    plt.show()

def update_animation(frame):
    """ Updates the plot for each frame in the animation."""
    plt.cla()
    plt.plot(range(frame + 1), best_fitness_history[:frame + 1], marker='o', linestyle='-')
    plt.title("Best Accuracy Evolution Over Generations")
    plt.xlabel("Generation")
    plt.ylabel("Best Accuracy (%)")
    plt.ylim(0, 100)

def generate_animation():
    """ Generates an animated GIF showing evolution progression."""
    fig = plt.figure()
    ani = animation.FuncAnimation(fig, update_animation, frames=len(best_fitness_history), repeat=False)
    ani.save("evolution_animation.gif", writer="pillow", fps=3)
    plt.show()

# Modify the genetic algorithm function to store population and best fitness history
def genetic_algorithm(n_bits, population_size, generations, mutation_rate=MUTATION_RATE, accuracy_threshold=ACCURACY_THRESHOLD):
    global population_history, best_fitness_history
    population = [create_chromosome() for _ in range(population_size)]
    best_solution = None
    best_accuracy = 0
    
    for generation in range(generations):
        print(f"Generation {generation+1}/{generations}")
        with Pool() as pool:
            fitness_values = pool.map(evaluate_fitness, population)
        
        fitness_values.sort(reverse=True, key=lambda x: x[0])
        if fitness_values[0][0] > best_accuracy:
            best_accuracy = fitness_values[0][0]
            best_solution = fitness_values[0][1]
        
        best_fitness_history.append(best_accuracy)
        population_history.append(population[:])
        
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
    
    return best_solution, best_accuracy

# After running the genetic algorithm, generate visualizations
best_solution, best_accuracy = genetic_algorithm(n_bits=NO_OF_BITS, population_size=POPULATION_SIZE, generations=GENERATIONS)
plot_population_similarity()
generate_animation()
