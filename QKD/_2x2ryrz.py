import matplotlib
matplotlib.use("Agg")  # Fixes renderer issue
import matplotlib.pyplot as plt
from PIL import Image  # To load images
from qiskit import QuantumCircuit, Aer, transpile
from qiskit.visualization import plot_bloch_multivector
from qiskit.providers.aer import AerSimulator
import random
import math
import time

pi = math.pi
start_time = time.time()

def create_combined_bb84_circuit(bit, alice_base, bob_base):
    """
    Create a single quantum circuit that includes:
    - Alice's preparation using an alternative Hadamard:
      H ∝ R_y(π/2) then R_z(π)
    - Bob's measurement using the same transformation if his basis is X.
    """
    qc = QuantumCircuit(1, 1)  # 1 qubit, 1 classical bit

    # Alice's preparation
    if alice_base == 'Z':
        if bit == 1:
            qc.x(0)  # For Z basis, flip qubit to |1> if bit is 1
    else:  # Alice in X basis
        if bit == 0:
            qc.ry(pi/2, 0)
            qc.rz(pi, 0)  # Produces state equivalent to |+>
        else:
            qc.x(0)      # Flip to |1>
            qc.ry(pi/2, 0)
            qc.rz(pi, 0)  # Produces state equivalent to |->

    # Bob's measurement: if Bob's chosen basis is X, apply the same sequence
    if bob_base == 'X':
        qc.ry(pi/2, 0)
        qc.rz(pi, 0)
    qc.measure(0, 0)
    
    return qc

def save_bb84_visuals():
    """
    Generate bit-basis pairs, create combined Alice-Bob circuits, simulate Bloch spheres,
    and save images as PNG files.
    """
    test_cases = [(0, 'Z'), (1, 'Z'), (0, 'X'), (1, 'X')]
    simulator = AerSimulator()

    for bit, alice_base in test_cases:
        for bob_base in ['Z', 'X']:  # Bob randomly picks Z or X basis
            tag = f"{bit}_{alice_base}_to_{bob_base}"

            # Create the combined Alice-Bob circuit
            qc_combined = create_combined_bb84_circuit(bit, alice_base, bob_base)
            fig_circuit = qc_combined.draw(output='mpl')
            fig_circuit.savefig(f"combined_circuit_{tag}.png", format="png", dpi=600)
            plt.close(fig_circuit)
            print(f"Saved combined Alice-Bob circuit as combined_circuit_{tag}.png")

            # Simulate the statevector (before measurement) and plot Bloch sphere
            qc_combined.save_statevector()
            compiled_circuit = transpile(qc_combined, simulator)
            result = simulator.run(compiled_circuit).result()
            statevector = result.get_statevector()
            fig_bloch = plot_bloch_multivector(statevector)
            fig_bloch.savefig(f"bloch_{tag}.png", format="png", dpi=600)
            plt.close(fig_bloch)
            print(f"Saved Bloch sphere as bloch_{tag}.png")

def visualize_grid(image_type, title):
    """
    Create a 2x2 grid for displaying either the combined circuits or Bloch spheres.
    :param image_type: "combined_circuit" or "bloch"
    """
    test_cases = [(0, 'Z'), (1, 'Z'), (0, 'X'), (1, 'X')]
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    fig.suptitle(title, fontsize=16)

    for i, (bit, alice_base) in enumerate(test_cases):
        bob_base = 'Z'  # For grid visualization, assume Bob uses the Z basis
        tag = f"{bit}_{alice_base}_to_{bob_base}"
        img = Image.open(f"{image_type}_{tag}.png")
        row, col = divmod(i, 2)
        axes[row, col].imshow(img)
        axes[row, col].axis("off")
        axes[row, col].set_title(f"Bit={bit}, Alice={alice_base}, Bob={bob_base}")

    plt.tight_layout()
    plt.subplots_adjust(top=0.9)
    output_filename = f"bb84_{image_type}_grid.png"
    plt.savefig(output_filename, dpi=600)
    plt.show()
    print(f"Saved {image_type} grid as {output_filename}")

# Run the visualization pipeline
save_bb84_visuals()

# Generate grids for combined circuits and Bloch spheres
visualize_grid("combined_circuit", "BB84 Combined Circuit Grid")
visualize_grid("bloch", "BB84 Bloch Sphere Grid")

end_time = time.time()
print(f"Total time taken: {(end_time - start_time) * 1000} ms")
