import socket
import json
import numpy as np
from qiskit import QuantumCircuit, Aer, execute

# Function to prepare qubits in BB84 states (Z or X basis)
def prepare_qubit(qc, basis, bit, qubit_index):
    if basis == 0:  # Z basis
        if bit == 1:
            qc.x(qubit_index)  # Apply X gate to get |1⟩
    else:  # X basis
        if bit == 1:
            qc.h(qubit_index)  # Apply Hadamard to get |+⟩
        else:
            qc.h(qubit_index)  # Apply Hadamard to get |+⟩
    return qc

# Alice's server to prepare qubits and send them to Bob
def alice_server():
    n_bits = 100  # Number of bits to exchange
    alice_bases = []  # Alice's random basis choices
    alice_bits = []  # Alice's random bit choices
    qubits = QuantumCircuit(2 * n_bits, n_bits)  # Create a quantum circuit with 2 * n_bits qubits for Alice (and one classical bit per qubit)

    # Prepare Alice's qubits in random bases and bits
    for i in range(n_bits):
        basis = np.random.choice([0, 1])  # Random basis choice: 0 for Z, 1 for X
        bit = np.random.choice([0, 1])  # Random bit choice: 0 or 1
        alice_bases.append(basis)
        alice_bits.append(bit)
        qubits = prepare_qubit(qubits, basis, bit, i)

    # Simulate the quantum circuit using Aer
    simulator = Aer.get_backend('qasm_simulator')
    result = execute(qubits, simulator, shots=1024).result()

    # Get the counts (measurement outcomes) from Alice's qubits
    alice_counts = result.get_counts()

    # Create a socket to communicate with Bob
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 65432))
    server_socket.listen()

    print("Alice's Measurement Counts:", alice_counts)

    # Wait for Bob to connect
    conn, addr = server_socket.accept()
    with conn:
        print(f"Connected by {addr}")

        # Send Alice's basis choices and the measurement results to Bob
        data = {
            'alice_bases': alice_bases,
            'alice_bits': alice_bits,
            'alice_counts': alice_counts
        }
        json_data = json.dumps(data)
        conn.sendall(json_data.encode())

        print("Sent data to Bob.")

if __name__ == "__main__":
    alice_server()
