import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid

def visualize_bb84_grid():
    """
    Load EPS images directly and arrange them in a 2x2 grid.
    """
    test_cases = [(0, 'Z'), (1, 'Z'), (0, 'X'), (1, 'X')]
    fig = plt.figure(figsize=(10, 10))
    grid = ImageGrid(fig, 111,  # Create 2x2 grid
                     nrows_ncols=(2, 2),
                     axes_pad=0.5,  # Padding between images
                     aspect=False)

    for ax, (bit, base) in zip(grid, test_cases):
        eps_filename = f"bloch_{bit}_{base}.eps"
        img = plt.imread(eps_filename)  # Load EPS
        ax.imshow(img)  # Display image
        ax.axis("off")  # Hide axes
        ax.set_title(f"Bit={bit}, Base={base}")

    plt.suptitle("BB84 Quantum State Visualization", fontsize=16)
    plt.savefig("bb84_bloch_grid.eps", format='eps', dpi=600)  # Save final grid as EPS
    plt.show()

# Run the visualization
visualize_bb84_grid()
