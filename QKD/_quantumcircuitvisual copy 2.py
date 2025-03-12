import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit, Aer, transpile
from qiskit.visualization import plot_bloch_multivector
from qiskit.providers.aer import AerSimulator

def create_bb84_circuit(bit, base):
    """
    Create a BB84 quantum circuit based on a given bit (0/1) and basis (Z/X).
    """
    qc = QuantumCircuit(1, 1)  # 1 qubit, 1 classical bit

    if base == 'Z':
        if bit == 1:
            qc.x(0)  # Flip to |1> if bit is 1
    else:  # base == 'X'
        if bit == 0:
            qc.h(0)  # |+> state if bit is 0
        else:
            qc.x(0)
            qc.h(0)  # |-> state if bit is 1

    return qc

def visualize_bb84():
    """
    Generate bit-basis pairs, create circuits, and plot all Bloch spheres in a grid.
    """
    test_cases = [(0, 'Z'), (1, 'Z'), (0, 'X'), (1, 'X')]
    simulator = AerSimulator()

    fig, axes = plt.subplots(2, 2, figsize=(10, 10))  # Create 2x2 grid
    fig.suptitle("BB84 Quantum State Visualization", fontsize=16)

    for i, (bit, base) in enumerate(test_cases):
        row, col = divmod(i, 2)  # Determine grid position
        qc = create_bb84_circuit(bit, base)
        qc.save_statevector()  # Save quantum state

        # Simulate the circuit
        compiled_circuit = transpile(qc, simulator)
        result = simulator.run(compiled_circuit).result()
        statevector = result.get_statevector()

        # Generate Bloch sphere and store it in an image
        bloch_fig = plot_bloch_multivector(statevector)

        # Save the figure temporarily and read it as an image
        temp_filename = f"bloch_{bit}_{base}.png"
        bloch_fig.savefig(temp_filename, dpi=600)
        plt.close(bloch_fig)  # Close figure to prevent memory leak

        # Load the saved image and plot it in the grid
        img = plt.imread(temp_filename)
        axes[row, col].imshow(img)
        axes[row, col].axis("off")  # Hide axes
        axes[row, col].set_title(f"Bit={bit}, Base={base}")

    plt.tight_layout()
    plt.subplots_adjust(top=0.9)  # Adjust title spacing
    plt.savefig("bb84_bloch_grid.png", dpi=600)  # Save high-resolution image
    plt.show()

# Run the visualization
visualize_bb84()
