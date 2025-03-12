import matplotlib
matplotlib.use("Agg")  # Fixes the renderer issue
import matplotlib.pyplot as plt
from PIL import Image  # To load images
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

def save_bb84_visuals():
    """
    Generate bit-basis pairs, create circuits, and save visualizations as PNG files.
    """
    test_cases = [(0, 'Z'), (1, 'Z'), (0, 'X'), (1, 'X')]
    simulator = AerSimulator()

    for bit, base in test_cases:
        qc = create_bb84_circuit(bit, base)

        # Save Circuit Diagram as PNG
        circuit_filename = f"circuit_{bit}_{base}.png"
        fig_circuit = qc.draw(output='mpl')  # Matplotlib-based drawing
        fig_circuit.savefig(circuit_filename, format="png", dpi=600)
        plt.close(fig_circuit)  # Close figure to prevent memory leak
        print(f"Saved circuit diagram as {circuit_filename}")

        # Simulate and Save Bloch Sphere as PNG
        qc.save_statevector()  # Save quantum state
        compiled_circuit = transpile(qc, simulator)
        result = simulator.run(compiled_circuit).result()
        statevector = result.get_statevector()

        bloch_filename = f"bloch_{bit}_{base}.png"
        fig_bloch = plot_bloch_multivector(statevector)
        fig_bloch.savefig(bloch_filename, format="png", dpi=600)
        plt.close(fig_bloch)  # Close figure to prevent memory leak
        print(f"Saved Bloch sphere as {bloch_filename}")

def visualize_grid(image_type):
    """
    Create a 2x2 grid for either circuit diagrams or Bloch spheres.
    :param image_type: "circuit" or "bloch"
    """
    test_cases = [(0, 'Z'), (1, 'Z'), (0, 'X'), (1, 'X')]
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))  # Create a 2x2 grid
    fig.suptitle(f"BB84 {image_type.capitalize()} Grid", fontsize=16)

    for i, (bit, base) in enumerate(test_cases):
        row, col = divmod(i, 2)  # Determine grid position
        img = Image.open(f"{image_type}_{bit}_{base}.png")

        axes[row, col].imshow(img)
        axes[row, col].axis("off")
        axes[row, col].set_title(f"Bit={bit}, Base={base}")

    plt.tight_layout()
    plt.subplots_adjust(top=0.9)  # Adjust title spacing
    output_filename = f"bb84_{image_type}_grid.png"
    plt.savefig(output_filename, dpi=600)  # Save the combined grid as PNG
    plt.show()
    print(f"Saved {image_type} grid as {output_filename}")

# Run the visualization pipeline
save_bb84_visuals()  # Save all circuit and Bloch sphere images
visualize_grid("circuit")  # Create and display the circuit grid
visualize_grid("bloch")  # Create and display the Bloch sphere grid
