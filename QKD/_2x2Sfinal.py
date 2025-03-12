import matplotlib
matplotlib.use("Agg")  # Fixes renderer issue
import matplotlib.pyplot as plt
from PIL import Image  # To load images
from qiskit import QuantumCircuit, Aer, transpile
from qiskit.visualization import plot_bloch_multivector
from qiskit.providers.aer import AerSimulator

def create_combined_bb84_circuit(bit, alice_base, bob_base):
    """
    Create a single quantum circuit that includes:
    - Alice's preparation (S gates instead of H)
    - Bob's measurement (S gates instead of H)
    """
    qc = QuantumCircuit(1, 1)  # 1 qubit, 1 classical bit

    # Alice's preparation
    if alice_base == 'Z':
        if bit == 1:
            qc.x(0)  # Flip to |1> if bit is 1
    else:  # Alice in X basis (Modified: Use S gate instead of H)
        if bit == 0:
            qc.s(0)  # Apply S gate (phase shift, not a full superposition)
        else:
            qc.x(0)
            qc.s(0)  # Apply S gate

    # Bob's measurement
    if bob_base == 'X':
        qc.s(0)  # Apply S gate before measurement (instead of H)
    qc.measure(0, 0)  # Bob measures

    return qc

def save_bb84_visuals():
    """
    Generate bit-basis pairs, create combined Alice-Bob circuits, simulate Bloch spheres, and save as PNG.
    """
    test_cases = [(0, 'Z'), (1, 'Z'), (0, 'X'), (1, 'X')]
    simulator = AerSimulator()

    for bit, alice_base in test_cases:
        for bob_base in ['Z', 'X']:  # Bob randomly picks Z or X basis
            tag = f"{bit}_{alice_base}_to_{bob_base}"

            # Step 1: Create the combined Alice-Bob circuit
            qc_combined = create_combined_bb84_circuit(bit, alice_base, bob_base)
            fig_circuit = qc_combined.draw(output='mpl')
            fig_circuit.savefig(f"combined_circuit_{tag}.png", format="png", dpi=600)
            plt.close(fig_circuit)
            print(f"Saved combined Alice-Bob circuit as combined_circuit_{tag}.png")

            # Step 2: Simulate Alice's state before measurement
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
    Create a 2x2 grid for circuits or Bloch spheres.
    :param image_type: "combined_circuit" or "bloch"
    """
    test_cases = [(0, 'Z'), (1, 'Z'), (0, 'X'), (1, 'X')]
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    fig.suptitle(title, fontsize=16)

    for i, (bit, alice_base) in enumerate(test_cases):
        bob_base = 'Z'  # Assuming Bob measures in Z basis for simplicity
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

# Generate grids
visualize_grid("combined_circuit", "BB84 Combined Circuit Grid with S Gate")
visualize_grid("bloch", "BB84 Bloch Sphere Grid with S Gate")
