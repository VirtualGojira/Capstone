from qiskit import QuantumCircuit, Aer, execute
import numpy as np

# Function to simulate Alice's and Bob's random basis choices
def alice_basis_choice(circuit, qubit):
    if np.random.choice([0, 1]) == 0:  # Z basis (no gate)
        pass
    else:  # X basis (apply Hadamard)
        circuit.h(qubit)

def bob_basis_choice(circuit, qubit):
    if np.random.choice([0, 1]) == 0:  # Z basis (no gate)
        pass
    else:  # X basis (apply Hadamard)
        circuit.h(qubit)

# Number of bits to share
n_bits = 10

# Create a quantum circuit with 2 * n_bits qubits (Alice and Bob each have n_bits qubits)
qc = QuantumCircuit(2 * n_bits, 2 * n_bits)  # 2 * n_bits qubits, 2 * n_bits classical bits

# Apply entangling gates to create Bell states for each pair of qubits
for i in range(n_bits):
    qc.h(i)  # Apply Hadamard to create superposition
    qc.cx(i, i + n_bits)  # Apply CNOT to entangle qubits

# Alice's random basis choice for each qubit
for i in range(n_bits):
    alice_basis_choice(qc, i)

# Bob's random basis choice for each qubit
for i in range(n_bits):
    bob_basis_choice(qc, i + n_bits)

# Measure qubits (Alice and Bob both measure their respective qubits)
qc.measure(range(n_bits), range(n_bits))  # Alice's qubits measured to classical bits 0 to n_bits-1
qc.measure(range(n_bits, 2 * n_bits), range(n_bits, 2 * n_bits))  # Bob's qubits measured to classical bits n_bits to 2*n_bits-1

# Simulate the circuit using Aer
simulator = Aer.get_backend('qasm_simulator')

# Execute the circuit and get the result
result = execute(qc, simulator, shots=1024).result()

# Get the counts of the measurement outcomes
counts = result.get_counts(qc)
print("Measurement outcomes:", counts)

# Here, we will simulate the key generation by comparing Alice's and Bob's results.
# In a real QKD protocol, they would compare their results and discard any mismatched bits.
# For simplicity, let's assume they discard bits where they measured in different bases.
