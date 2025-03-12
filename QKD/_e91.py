from qiskit import QuantumCircuit, Aer, execute
import numpy as np
import time
start_time = time.time()

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

# Create a quantum circuit with Alice and Bob measuring in different bases
qc = QuantumCircuit(2, 2)  # 2 qubits, 2 classical bits

# Apply entangling gates to create a Bell state
qc.h(0)
qc.cx(0, 1)

# Alice's random basis choice
alice_basis_choice(qc, 0)

# Bob's random basis choice
bob_basis_choice(qc, 1)

# Measure qubits
qc.measure([0, 1], [0, 1])

# Simulate the circuit using Aer
simulator = Aer.get_backend('qasm_simulator')

# Execute the circuit and get the result
result = execute(qc, simulator, shots=1024).result()

# Get the counts of the measurement outcomes
counts = result.get_counts(qc)
print("Measurement outcomes:", counts)

end_time = time.time()
time_taken_ms = (end_time - start_time) * 10000
print(f"Time taken: {time_taken_ms} ms")