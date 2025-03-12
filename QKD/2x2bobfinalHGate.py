import matplotlib
matplotlib.use("Agg")  # Fixes renderer issue
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

def create_bob_measurement(qc, base):
    """
    Extend Alice's quantum circuit to include Bob's measurement in a given basis (Z/X).
    """
    bob_qc = qc.copy()  # Copy Alice's circuit

    # Bob measures in his randomly chosen basis
    if base == 'X':
        bob_qc.h(0)  # Apply H before measurement in X basis
    bob_qc.measure_all()

    return bob_qc

def save_bb84_visuals():
    """
    Generate bit-basis pairs, create circuits, simulate Bloch spheres, and save as PNG.
    """
    test_cases = [(0, 'Z'), (1, 'Z'), (0, 'X'), (1, 'X')]
    simulator = AerSimulator()

    for bit, alice_base in test_cases:
        for bob_base in ['Z', 'X']:  # Bob randomly picks Z or X basis
            tag = f"{bit}_{alice_base}_to_{bob_base}"

            # Step 1: Alice's Circuit
            qc_alice = create_bb84_circuit(bit, alice_base)
            fig_circuit_alice = qc_alice.draw(output='mpl')
            fig_circuit_alice.savefig(f"alice_circuit_{tag}.png", format="png", dpi=600)
            plt.close(fig_circuit_alice)
            print(f"Saved Alice's circuit as alice_circuit_{tag}.png")

            # Step 2: Simulate Alice's state before measurement
            qc_alice.save_statevector()
            compiled_circuit = transpile(qc_alice, simulator)
            result = simulator.run(compiled_circuit).result()
            statevector = result.get_statevector()
            fig_bloch_alice = plot_bloch_multivector(statevector)
            fig_bloch_alice.savefig(f"alice_bloch_{tag}.png", format="png", dpi=600)
            plt.close(fig_bloch_alice)
            print(f"Saved Alice's Bloch sphere as alice_bloch_{tag}.png")

            # Step 3: Bob's Measurement Circuit
            qc_bob = create_bob_measurement(qc_alice, bob_base)
            fig_circuit_bob = qc_bob.draw(output='mpl')
            fig_circuit_bob.savefig(f"bob_circuit_{tag}.png", format="png", dpi=600)
            plt.close(fig_circuit_bob)
            print(f"Saved Bob's circuit as bob_circuit_{tag}.png")

            # Step 4: Simulate Bob's state after measurement
            compiled_circuit_bob = transpile(qc_bob, simulator)
            result_bob = simulator.run(compiled_circuit_bob).result()
            statevector_bob = result_bob.get_statevector()
            fig_bloch_bob = plot_bloch_multivector(statevector_bob)
            fig_bloch_bob.savefig(f"bob_bloch_{tag}.png", format="png", dpi=600)
            plt.close(fig_bloch_bob)
            print(f"Saved Bob's Bloch sphere as bob_bloch_{tag}.png")

def visualize_grid(image_type, title):
    """
    Create a 2x2 grid for either Alice's or Bob's visualizations.
    :param image_type: "alice_circuit", "alice_bloch", "bob_circuit", or "bob_bloch"
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

# Generate separate grids
visualize_grid("alice_circuit", "Alice's BB84 Circuit Grid")
visualize_grid("alice_bloch", "Alice's BB84 Bloch Sphere Grid")
visualize_grid("bob_circuit", "Bob's BB84 Measurement Circuit Grid")
visualize_grid("bob_bloch", "Bob's BB84 Bloch Sphere Grid")
