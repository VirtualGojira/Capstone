import os
import csv
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # Required for 3D plotting
from scipy.interpolate import griddata
import math
import matplotlib.colors as mcolors
import matplotlib.cm as cm

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

def plot_3d_surfaces_grid(X, Y, Z, C, interp_method):
    """
    Creates a single figure containing multiple 3D surface subplots
    using the specified interpolation method:
      - "nearest", "linear", or "cubic".
    Each subplot corresponds to one unique value of max_retries in C.
      - X-axis: distance
      - Y-axis: timeout
      - Z-axis: interpolated fitness
    All subplots share a single colorbar that indicates the fitness range.
    """
    # Identify unique max_retries values
    unique_retries = np.unique(C)
    n = len(unique_retries)
    print("Unique max_retries values found:", unique_retries)

    # Determine a grid layout for subplots (e.g., 4 columns)
    cols = 4
    rows = math.ceil(n / cols)

    # Create a figure sized to hold all subplots
    fig = plt.figure(figsize=(6 * cols, 5 * rows))

    # Global normalization for the colormap based on overall fitness values
    zmin, zmax = Z.min(), Z.max()
    norm = mcolors.Normalize(vmin=zmin, vmax=zmax)
    cmap = cm.plasma

    # Loop over each unique max_retries value
    for i, m_val in enumerate(unique_retries):
        ax = fig.add_subplot(rows, cols, i + 1, projection='3d')
        
        # Filter data for the current max_retries value
        mask = (C == m_val)
        X_sub = X[mask]
        Y_sub = Y[mask]
        Z_sub = Z[mask]

        # If there is insufficient data, skip plotting
        if len(X_sub) < 3:
            ax.set_title(f"max_retries={m_val}\nNot enough data")
            continue

        # Create a regular grid over the range of distance & timeout
        xi = np.linspace(X_sub.min(), X_sub.max(), 50)
        yi = np.linspace(Y_sub.min(), Y_sub.max(), 50)
        xi, yi = np.meshgrid(xi, yi)

        # Interpolate fitness values onto the grid using the chosen method
        zi = griddata((X_sub, Y_sub), Z_sub, (xi, yi), method=interp_method)

        # Map the interpolated fitness values through the colormap
        colors = cmap(norm(zi))
        ax.plot_surface(xi, yi, zi, facecolors=colors, 
                        rstride=1, cstride=1, linewidth=0, antialiased=True)
        
        ax.set_title(f"max_retries = {m_val}")
        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("Timeout (ns)")
        ax.set_zlabel("Fitness")

    # Create a single colorbar for all subplots
    mappable = cm.ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    cbar = fig.colorbar(mappable, ax=fig.axes, shrink=0.5, aspect=20)
    cbar.set_label("Fitness (Accuracy %)")

    plt.tight_layout()
    filename = f"fitness_3d_surfaces_grid_{interp_method}.png"
    plt.savefig(filename, dpi=300)
    plt.close()
    print(f"Saved {filename}")

def main():
    X, Y, Z, C = read_batch_csv()
    if X is None:
        return

    # List of interpolation methods to use
    interp_methods = ['nearest', 'linear', 'cubic']
    for method in interp_methods:
        plot_3d_surfaces_grid(X, Y, Z, C, method)

if __name__ == "__main__":
    main()
