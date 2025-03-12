import os
import csv
import gc
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from prept5 import avg_100_runs
from multiprocessing import Pool, cpu_count

# Only available on Unix-like systems.
try:
    import resource
except ImportError:
    resource = None

# Set memory limit to 16 GB (16 * 1024^3 bytes)
def set_memory_limit(limit_bytes=16 * 1024 * 1024 * 1024):
    if resource:
        try:
            # RLIMIT_AS limits the total available virtual memory.
            resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, resource.RLIM_INFINITY))
            print(f"Memory limit set to {limit_bytes / (1024**3)} GB")
        except Exception as e:
            print("Could not set memory limit:", e)
    else:
        print("Resource module not available on this platform. Memory limiting is not enforced.")

# Parameter ranges and settings
DISTANCE_MIN, DISTANCE_MAX = 1, 200
TIMEOUT_MIN, TIMEOUT_MAX = 1, 1e9
MAX_RETRIES_MIN, MAX_RETRIES_MAX = 1, 10
NO_OF_BITS = 24


# Get available CPU cores and limit to 90%
NUM_PROCESSES = max(1, int(0.9 * cpu_count()))

# Directory for CSV files
CSV_DIR = "batches_csv"
os.makedirs(CSV_DIR, exist_ok=True)

# Function to evaluate accuracy (fitness) for given parameters
def evaluate_accuracy(params):
    distance, timeout, max_retries = params
    return avg_100_runs(NO_OF_BITS, distance, timeout, max_retries)

# Generator function to yield batches of parameter combinations
def generate_parameter_grid_batches(batch_size):
    distance_values = np.linspace(DISTANCE_MIN, DISTANCE_MAX, 50)
    timeout_values = np.linspace(TIMEOUT_MIN, TIMEOUT_MAX, 50)
    max_retries_values = np.linspace(MAX_RETRIES_MIN, MAX_RETRIES_MAX, 10)
    
    batch = []
    for d in distance_values:
        for t in timeout_values:
            for m in max_retries_values:
                batch.append((d, t, m))
                if len(batch) == batch_size:
                    yield batch
                    batch = []
    if batch:
        yield batch

# Process batches, evaluate fitness, write each batch to its own CSV file,
# and force garbage collection after each batch.
def process_batches_and_write_csv():
    total_params = 20*20*10
    batch_size = max(1, total_params // (NUM_PROCESSES * 2))
    
    batch_number = 0
    for batch in generate_parameter_grid_batches(batch_size):
        batch_number += 1
        # Create a new pool for each batch with maxtasksperchild set
        with Pool(processes=NUM_PROCESSES, maxtasksperchild=10) as pool:
            fitness_results = pool.map(evaluate_accuracy, batch)
        
        csv_filename = os.path.join(CSV_DIR, f"batch_{batch_number:03d}.csv")
        with open(csv_filename, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["distance", "timeout", "fitness", "max_retries"])
            for (d, t, m), fitness in zip(batch, fitness_results):
                writer.writerow([d, t, fitness, m])
        print(f"Wrote {csv_filename}")
        
        # Explicitly delete temporary objects and force garbage collection.
        del batch, fitness_results
        gc.collect()


# Read all CSV files and aggregate the data for plotting
def generate_4d_fitness_landscape_from_csv():
    X_list, Y_list, Z_list, C_list = [], [], [], []
    csv_files = sorted([f for f in os.listdir(CSV_DIR) if f.endswith('.csv')])
    
    for csv_file in csv_files:
        filepath = os.path.join(CSV_DIR, csv_file)
        with open(filepath, mode='r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            for row in reader:
                d, t, fitness, m = row
                X_list.append(float(d))
                Y_list.append(float(t))
                Z_list.append(float(fitness))
                C_list.append(float(m))
    
    return np.array(X_list), np.array(Y_list), np.array(Z_list), np.array(C_list)

# Plot the 4D fitness landscape with color representing max_retries
def plot_4d_fitness_landscape_from_csv():
    X, Y, Z, C = generate_4d_fitness_landscape_from_csv()
    
    fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111, projection='3d')
    
    sc = ax.scatter(X, Y, Z, c=C, cmap='plasma', marker='o')
    plt.colorbar(sc, label="Max Retries")
    
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Timeout (ns)")
    ax.set_zlabel("Fitness (Accuracy %)")
    ax.set_title("Optimized 4D Fitness Landscape (Color = Max Retries)")
    
    plt.savefig('fitness_landscape.eps', format='eps', dpi=600)
    plt.close()
    print("Saved optimized_fitness_landscape_4d.png")

def main():
    # Attempt to set the memory limit before processing
    set_memory_limit()

    # Phase 1: Process batches and write results to CSV files
    process_batches_and_write_csv()
    
    # Phase 2: Read CSV files and generate the 4D fitness landscape plot
    plot_4d_fitness_landscape_from_csv()

if __name__ == "__main__":
    main()
