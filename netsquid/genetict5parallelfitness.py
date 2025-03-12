import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from prept5 import avg_100_runs
from multiprocessing import Pool, cpu_count

# Parameter ranges
DISTANCE_MIN, DISTANCE_MAX = 1, 200
TIMEOUT_MIN, TIMEOUT_MAX = 1, 1e9
MAX_RETRIES_MIN, MAX_RETRIES_MAX = 1, 11
NO_OF_BITS = 24

# Get available CPU cores and limit to 90%
NUM_PROCESSES = max(1, int(0.9 * cpu_count()))

# Function to evaluate accuracy (fitness) for given parameters
def evaluate_accuracy(params):
    distance, timeout, max_retries = params
    return avg_100_runs(NO_OF_BITS, distance, timeout, max_retries)

# Generate parameter grid with reduced resolution for efficiency
def generate_parameter_grid():
    distance_values = np.linspace(DISTANCE_MIN, DISTANCE_MAX, 10)  # Reduced from 15
    timeout_values = np.linspace(TIMEOUT_MIN, TIMEOUT_MAX, 10)  # Reduced from 15
    max_retries_values = np.linspace(MAX_RETRIES_MIN, MAX_RETRIES_MAX, 10)  # Reduced from 10

    param_list = [(d, t, m) for d in distance_values for t in timeout_values for m in max_retries_values]
    return param_list

# Process in batches to reduce memory usage
def generate_4d_fitness_landscape():
    param_list = generate_parameter_grid()
    batch_size = max(1, len(param_list) // (NUM_PROCESSES * 2))  # Adjust batch size for memory efficiency

    fitness_values = []
    with Pool(processes=NUM_PROCESSES) as pool:
        for i in range(0, len(param_list), batch_size):
            batch = param_list[i : i + batch_size]
            fitness_values.extend(pool.map(evaluate_accuracy, batch))

    # Extract values for plotting
    X, Y, Z, C = zip(*[(p[0], p[1], fitness_values[i], p[2]) for i, p in enumerate(param_list)])
    return np.array(X), np.array(Y), np.array(Z), np.array(C)

# Plot the 4D fitness landscape with memory efficiency
def plot_4d_fitness_landscape():
    X, Y, Z, C = generate_4d_fitness_landscape()

    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')

    sc = ax.scatter(X, Y, Z, c=C, cmap='plasma', marker='o')  # Color represents max_retries
    plt.colorbar(sc, label="Max Retries")

    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Timeout (ns)")
    ax.set_zlabel("Fitness (Accuracy %)")
    ax.set_title("Optimized 4D Fitness Landscape (Color = Max Retries)")

    plt.savefig('fitness_landscape.eps', format='eps', dpi=600)
    plt.close()
    print("Saved optimized_fitness_landscape_4d.png")

# Run the optimized 4D plot function
plot_4d_fitness_landscape()
