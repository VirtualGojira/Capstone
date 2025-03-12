import os
import csv
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # Required for 3D plotting

# Directory containing the batch CSV files
CSV_DIR = "batches_csv"

def read_batch_csv():
    """
    Reads all CSV files in CSV_DIR and aggregates the data.
    Each CSV file should have the header:
    "distance", "timeout", "fitness", "max_retries"
    
    Returns four numpy arrays:
      - distance values (X axis)
      - timeout values (Y axis)
      - max_retries values (Z axis)
      - fitness (accuracy) values (to be shown as a color gradient)
    """
    distance_list, timeout_list, max_retries_list, fitness_list = [], [], [], []
    csv_files = sorted([f for f in os.listdir(CSV_DIR) if f.endswith('.csv')])
    
    if not csv_files:
        print("No CSV files found in directory:", CSV_DIR)
        return None, None, None, None

    for csv_file in csv_files:
        filepath = os.path.join(CSV_DIR, csv_file)
        with open(filepath, mode='r') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header row
            for row in reader:
                try:
                    d, t, fitness, m = row
                    distance_list.append(float(d))
                    timeout_list.append(float(t))
                    fitness_list.append(float(fitness))
                    max_retries_list.append(float(m))
                except ValueError:
                    print(f"Skipping invalid row in {csv_file}: {row}")
    
    return (np.array(distance_list), np.array(timeout_list), 
            np.array(max_retries_list), np.array(fitness_list))

def plot_3d_scatter(distance, timeout, max_retries, fitness):
    """
    Creates a 3D scatter plot where:
      - X axis: distance
      - Y axis: timeout
      - Z axis: max_retries
    The fitness/accuracy values are represented by the color of each point using a color gradient.
    """
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Create a 3D scatter plot with color representing fitness
    sc = ax.scatter(distance, timeout, max_retries, c=fitness, cmap='viridis')
    cbar = fig.colorbar(sc, shrink=0.5, aspect=10, label='Fitness (Accuracy %)')
    
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Timeout (ns)")
    ax.set_zlabel("Max Retries")
    ax.set_title("3D Scatter: Distance, Timeout, Max Retries (Color = Fitness)")
    
    # Save the plot to a file
    plt.savefig('fitness_3d_scatter.png', dpi=300)
    print("Saved fitness_3d_scatter.png")
    plt.close()

def main():
    distance, timeout, max_retries, fitness = read_batch_csv()
    if distance is None:
        return
    plot_3d_scatter(distance, timeout, max_retries, fitness)

if __name__ == "__main__":
    main()
