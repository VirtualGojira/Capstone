import socket
import json
import numpy as np
from qiskit import QuantumCircuit, Aer, execute

# Function to measure qubits in BB84 states (Z or X basis)
def measure_qubit(basis):
    qc = QuantumCircuit(1, 1)
    if basis == 1:  # Apply Hadamard if measuring in the X basis
        qc.h(0)
    qc.measure(0, 0)
    return qc

# Bob's client to receive qubits from Alice, measure them, and send the results back
def bob_client():
    n_bits = 100  # Number of bits to exchange
    bob_bases = []  # Bob's random basis choices
    bob_measurements = []  # Bob's measurement results

    # Create a socket to connect to Alice's server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 65432))

    # Receive Alice's data (basis choices, measurement outcomes)
    data = client_socket.recv(1024).decode()
    bob_data = json.loads(data)

    alice_bases = bob_data['alice_bases']
    alice_bits = bob_data['alice_bits']
    alice_counts = bob_data['alice_counts']

    print(f"Received Alice's Data:\nAlice's Bases: {alice_bases}\nAlice's Bits: {alice_bits}")

    # Generate Bob's random basis choices and measure qubits
    for _ in range(n_bits):
        basis = np.random.choice([0, 1])  # Random basis choice: 0 for Z, 1 for X
        bob_bases.append(basis)

    # Simulate the quantum circuit using Aer (no actual qubits here, just measurement simulation)
    qubits = []
    for i in range(n_bits):
        qubit = measure_qubit(bob_bases[i])
        qubits.append(qubit)

    # Combine all Bob's qubit measurement circuits
    qc = qubits[0]
    for qubit in qubits[1:]:
        qc = qc + qubit

    # Simulate Bob's measurements using Aer
    simulator = Aer.get_backend('qasm_simulator')
    result = execute(qc, simulator, shots=1024).result()

    # Get the counts (measurement outcomes) from Bob's qubits
    bob_counts = result.get_counts(qc)

    print(f"Bob's Measurement Counts: {bob_counts}")

    # Now compare bases and generate the shared key
    shared_key = []
    for i in range(n_bits):
        if alice_bases[i] == bob_bases[i]:  # Bases match
            # Extract bit from the measurement result
            alice_bit = alice_bits[i]
            bob_bit = list(bob_counts.keys())[0][i]  # Extract the bit from Bob's result
            if alice_bit == int(bob_bit):  # If the bits match, keep it
                shared_key.append(str(alice_bit))

    # Print the most frequent shared key
    print(f"Most Frequent Shared Key: {''.join(shared_key)}")

    client_socket.close()

if __name__ == "__main__":
    bob_client()
