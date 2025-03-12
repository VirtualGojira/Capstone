import os
import csv
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

CSV_DIR = "batches_csv"

def read_batch_csv():
    """
    Read all CSV files in CSV_DIR and aggregate the data.
    Each CSV file is expected to have the header:
    "distance", "timeout", "fitness", "max_retries"
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
                    Z_list.append(float(fitness))   # We'll call fitness "Z" here
                    C_list.append(float(m))
                except ValueError:
                    print(f"Skipping invalid row in {csv_file}: {row}")
    return np.array(X_list), np.array(Y_list), np.array(Z_list), np.array(C_list)

def plot_slices_by_max_retries(X, Y, Z, C):
    """
    Create a grid of 2D contour plots for each unique max_retries value.
    Each subplot shows Distance vs. Timeout, with Fitness as a color.
    """
    # Identify unique max_retries values (assumed to be integers 1..10)
    unique_retries = np.unique(C)
    n = len(unique_retries)
    
    # Set up subplot grid (e.g., 2 rows x 5 columns for 10 slices)
    cols = 5
    rows = (n + cols - 1) // cols  # enough rows to fit n subplots
    fig, axes = plt.subplots(rows, cols, figsize=(20, 8), sharex=True, sharey=True)
    axes = axes.flatten()  # Make it easier to iterate
    
    # We'll keep track of global min/max for consistent color scaling
    zmin, zmax = Z.min(), Z.max()

    for i, m_val in enumerate(unique_retries):
        ax = axes[i]
        # Filter data for this max_retries
        mask = (C == m_val)
        X_sub = X[mask]
        Y_sub = Y[mask]
        Z_sub = Z[mask]
        
        # If there's not enough data for this m_val, skip
        if len(X_sub) < 3:
            ax.set_title(f"max_retries={m_val} (not enough data)")
            continue

        # Create a grid over the distance & timeout range
        xi = np.linspace(X_sub.min(), X_sub.max(), 200)
        yi = np.linspace(Y_sub.min(), Y_sub.max(), 200)
        xi, yi = np.meshgrid(xi, yi)
        
        # Interpolate Z (fitness) onto the grid
        zi = griddata((X_sub, Y_sub), Z_sub, (xi, yi), method='cubic')
        
        # Plot contour or contourf
        contour = ax.contourf(xi, yi, zi, levels=50, vmin=zmin, vmax=zmax, cmap='plasma')
        ax.set_title(f"max_retries = {m_val}")
        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("Timeout (ns)")
    
    # Remove extra subplots if we have fewer than rows*cols slices
    for j in range(i+1, rows*cols):
        fig.delaxes(axes[j])
    
    # Add a colorbar that applies to all subplots
    cbar = fig.colorbar(contour, ax=axes.tolist(), shrink=0.8)
    cbar.set_label("Fitness (Accuracy %)")

    plt.tight_layout()
    plt.savefig("fitness_slices_by_max_retries.png", dpi=300)
    plt.close()
    print("Saved fitness_slices_by_max_retries.png")

def main():
    X, Y, Z, C = read_batch_csv()
    if X is None:
        return
    plot_slices_by_max_retries(X, Y, Z, C)

if __name__ == "__main__":
    main()
