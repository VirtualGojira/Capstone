import matplotlib
matplotlib.use("Agg")  # Fixes the renderer issue
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit, Aer, transpile
from qiskit.visualization import plot_bloch_multivector, circuit_drawer
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
    Generate random bit-basis pairs, create circuits, and save visualizations as EPS files.
    """
    test_cases = [(0, 'Z'), (1, 'Z'), (0, 'X'), (1, 'X')]
    simulator = AerSimulator()

    for bit, base in test_cases:
        qc = create_bb84_circuit(bit, base)
        qc.save_statevector()  # Save quantum state

        # Simulate the circuit
        compiled_circuit = transpile(qc, simulator)
        result = simulator.run(compiled_circuit).result()
        statevector = result.get_statevector()

        # Save Bloch Sphere as EPS
        fig_bloch = plot_bloch_multivector(statevector)
        bloch_filename = f"bloch_{bit}_{base}.eps"
        fig_bloch.savefig(bloch_filename, format="eps", dpi=600)
        plt.close(fig_bloch)  # Close figure to prevent memory leak
        print(f"Saved Bloch sphere as {bloch_filename}")

        # Save Circuit Diagram as EPS
        circuit_filename = f"circuit_{bit}_{base}.eps"
        fig_circuit = qc.draw(output='mpl')  # Matplotlib-based drawing
        fig_circuit.savefig(circuit_filename, format="eps", dpi=600)
        plt.close(fig_circuit)  # Close figure to prevent memory leak
        print(f"Saved circuit diagram as {circuit_filename}")

# Run the visualization
visualize_bb84()
