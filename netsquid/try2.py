import os
import csv
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # Required for 3D plotting
from scipy.interpolate import griddata

# Directory containing the batch CSV files
CSV_DIR = "batches_csv"

def read_batch_csv():
    """
    Read all CSV files in CSV_DIR and aggregate the data.
    Each CSV file is expected to have the header:
    "distance", "timeout", "fitness", "max_retries"
    
    Returns four numpy arrays:
      - X (distance)
      - Y (timeout)
      - Z (fitness)
      - C (max_retries)
    """
    X_list, Y_list, Z_list, C_list = [], [], [], []
    csv_files = sorted([f for f in os.listdir(CSV_DIR) if f.endswith('.csv')])
    
    if not csv_files:
        print("No CSV files found in directory:", CSV_DIR)
        return None, None, None, None

    for csv_file in csv_files:
        filepath = os.path.join(CSV_DIR, csv_file)
        with open(filepath, mode='r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header row
            for row in reader:
                try:
                    d, t, fitness, m = row
                    X_list.append(float(d))
                    Y_list.append(float(t))
                    Z_list.append(float(fitness))
                    C_list.append(float(m))
                except ValueError:
                    print(f"Skipping invalid row in {csv_file}: {row}")
    
    return (np.array(X_list), np.array(Y_list), 
            np.array(Z_list), np.array(C_list))

def plot_3d_surfaces_by_max_retries(X, Y, Z, C):
    """
    For each unique value of max_retries in C, create a 3D surface plot of:
      - X-axis: distance
      - Y-axis: timeout
      - Z-axis: fitness (interpolated)
    The parameter max_retries is held fixed for each surface.
    
    A separate figure is generated (and saved) for each max_retries value.
    """
    # Find the unique max_retries values
    unique_retries = np.unique(C)
    print("Unique max_retries values:", unique_retries)
    
    for m_val in unique_retries:
        # Filter rows where max_retries == m_val (within a small tolerance if needed)
        mask = (C == m_val)
        X_sub = X[mask]
        Y_sub = Y[mask]
        Z_sub = Z[mask]

        # If there's insufficient data for interpolation, skip
        if len(X_sub) < 3:
            print(f"Skipping max_retries={m_val} (not enough data points).")
            continue
        
        # Create a grid over the distance & timeout range
        xi = np.linspace(X_sub.min(), X_sub.max(), 200)
        yi = np.linspace(Y_sub.min(), Y_sub.max(), 200)
        xi, yi = np.meshgrid(xi, yi)
        
        # Interpolate fitness values (Z) onto the grid
        # Using 'cubic' interpolation; you can also try 'linear' or 'nearest'
        zi = griddata((X_sub, Y_sub), Z_sub, (xi, yi), method='cubic')
        
        # Create the 3D surface plot
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot the surface with a colormap
        surface = ax.plot_surface(xi, yi, zi, cmap='plasma', edgecolor='none')
        fig.colorbar(surface, shrink=0.5, aspect=10, label='Fitness (Accuracy %)')

        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("Timeout (ns)")
        ax.set_zlabel("Fitness (Accuracy %)")
        ax.set_title(f"3D Fitness Surface (max_retries = {m_val})")
        
        # Save each figure with a distinct filename
        filename = f"fitness_3d_surface_maxRetries_{int(m_val)}.png"
        plt.savefig(filename, dpi=300)
        plt.close()
        print(f"Saved {filename}")

def main():
    X, Y, Z, C = read_batch_csv()
    if X is None:
        return
    plot_3d_surfaces_by_max_retries(X, Y, Z, C)

if __name__ == "__main__":
    main()
