from qiskit import QuantumCircuit, Aer, transpile
from qiskit.visualization import plot_bloch_multivector, circuit_drawer
from qiskit.providers.aer import AerSimulator
import matplotlib.pyplot as plt
import random

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
    Generate random bit-basis pairs, create circuits, and visualize Bloch sphere.
    """
    test_cases = [(0, 'Z'), (1, 'Z'), (0, 'X'), (1, 'X')]
    simulator = AerSimulator()

    for i, (bit, base) in enumerate(test_cases):
        print(f"\nVisualizing Bit={bit}, Base={base}")
        qc = create_bb84_circuit(bit, base)
        qc.save_statevector()  # Save quantum state

        # Simulate the circuit
        compiled_circuit = transpile(qc, simulator)
        result = simulator.run(compiled_circuit).result()
        statevector = result.get_statevector()

        # Visualize Bloch Sphere
        plot_bloch_multivector(statevector)
        plt.title(f"Bit={bit}, Base={base}")
        plt.show()

        # Visualize circuit
        print(qc.draw())

# Run the visualization
visualize_bb84()
