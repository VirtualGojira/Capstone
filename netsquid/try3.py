import os
import csv
import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # For 3D plotting
from scipy.interpolate import griddata

# Directory containing the batch CSV files
CSV_DIR = "batches_csv"

def read_batch_csv():
    """
    Reads all CSV files in CSV_DIR and aggregates the data.
    Each CSV file is expected to have the header:
    "distance", "timeout", "fitness", "max_retries"
    
    Returns four numpy arrays:
      - X: distance
      - Y: timeout
      - Z: fitness (accuracy)
      - C: max_retries
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
            next(reader)  # Skip header
            for row in reader:
                try:
                    d, t, fitness, m = row
                    X_list.append(float(d))
                    Y_list.append(float(t))
                    Z_list.append(float(fitness))
                    C_list.append(float(m))
                except ValueError:
                    print(f"Skipping invalid row in {csv_file}: {row}")
    return np.array(X_list), np.array(Y_list), np.array(Z_list), np.array(C_list)

def plot_3d_surfaces_grid(X, Y, Z, C):
    """
    For each unique max_retries value, creates a 3D surface plot of fitness versus distance and timeout.
    All surface plots are arranged in a grid in one figure with a common colorbar representing fitness.
    """
    unique_retries = np.unique(C)
    n = len(unique_retries)
    cols = 5
    rows = math.ceil(n / cols)
    
    # Create the figure and a grid of 3D subplots.
    fig = plt.figure(figsize=(5 * cols, 4 * rows))
    axes = []
    for i in range(n):
        ax = fig.add_subplot(rows, cols, i + 1, projection='3d')
        axes.append(ax)
    
    # Determine the global min and max fitness values for a common z-axis range and color normalization.
    zmin, zmax = Z.min(), Z.max()
    
    # Loop over each unique max_retries value and create a 3D surface plot.
    for i, m_val in enumerate(unique_retries):
        # Filter the data for this max_retries value.
        mask = (C == m_val)
        X_sub = X[mask]
        Y_sub = Y[mask]
        Z_sub = Z[mask]
        
        # Skip if there is not enough data.
        if len(X_sub) < 3:
            axes[i].set_title(f"max_retries = {m_val}\n(not enough data)")
            continue
        
        # Create a grid over the (distance, timeout) domain.
        xi = np.linspace(X_sub.min(), X_sub.max(), 100)
        yi = np.linspace(Y_sub.min(), Y_sub.max(), 100)
        xi, yi = np.meshgrid(xi, yi)
        
        # Interpolate fitness values onto the grid.
        zi = griddata((X_sub, Y_sub), Z_sub, (xi, yi), method='cubic')
        
        # Plot the 3D surface.
        surf = axes[i].plot_surface(xi, yi, zi, cmap='plasma', edgecolor='none')
        axes[i].set_title(f"max_retries = {m_val}")
        axes[i].set_xlabel("Distance (m)")
        axes[i].set_ylabel("Timeout (ns)")
        axes[i].set_zlabel("Fitness")
        axes[i].set_zlim(zmin, zmax)
    
    # Remove any empty subplots if total subplots (rows*cols) exceeds the number of surfaces.
    for j in range(n, rows * cols):
        fig.delaxes(fig.add_subplot(rows, cols, j + 1))
    
    # Create a scalar mappable for the common colormap and add a common colorbar.
    mappable = plt.cm.ScalarMappable(cmap='plasma')
    mappable.set_array(np.linspace(zmin, zmax, 100))
    mappable.set_clim(zmin, zmax)
    fig.colorbar(mappable, ax=axes, shrink=0.6, aspect=20, label="Fitness (Accuracy %)")
    
    plt.tight_layout()
    plt.savefig("fitness_3d_surfaces_grid.png", dpi=300)
    plt.close()
    print("Saved fitness_3d_surfaces_grid.png")

def main():
    X, Y, Z, C = read_batch_csv()
    if X is None:
        return
    plot_3d_surfaces_grid(X, Y, Z, C)

if __name__ == "__main__":
    main()
