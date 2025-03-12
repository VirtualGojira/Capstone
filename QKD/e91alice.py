import socket
import json
from qiskit import QuantumCircuit, Aer, execute
import numpy as np
from collections import Counter

# Function to create and return the E91 entangled state (Bell state)
def create_bell_state(n_bits):
    qc = QuantumCircuit(2 * n_bits, 2 * n_bits)  
    for i in range(n_bits):
        qc.h(i)
        qc.cx(i, i + n_bits)
    return qc

# Alice's random basis choice (0 for Z-basis, 1 for X-basis)
def alice_basis_choice():
    return np.random.choice([0, 1])  # 0: Z basis, 1: X basis

# Function to perform Alice's measurements
def alice_measurement(qc, n_bits):
    bases = []  
    for i in range(n_bits):
        basis = alice_basis_choice()
        bases.append(basis)
        if basis == 1: 
            qc.h(i)
    qc.measure(range(n_bits), range(n_bits)) 
    return bases 

# Alice's server to handle key exchange
def alice_server():
    n_bits = 100  # Number of qubits for key exchange
    qc = create_bell_state(n_bits) 
    alice_bases = alice_measurement(qc, n_bits)

    # Simulate the quantum circuit using Aer
    simulator = Aer.get_backend('qasm_simulator')
    result = execute(qc, simulator, shots=1024).result()

    # Get the counts of Alice's measurement outcomes
    alice_counts = result.get_counts(qc)
    print(f"Alice's Measurement Counts: {alice_counts}")

    # Create a server socket and receive data from Bob
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 65432))
    server_socket.listen()

    conn, addr = server_socket.accept()
    with conn:
        print(f"Connected by {addr}")

        data = b""
        while True:
            packet = conn.recv(1024)
            if not packet:
                break
            data += packet

        # Deserialize Bob's data
        bob_data = json.loads(data.decode())
        bob_counts = bob_data['bob_counts']
        bob_bases = bob_data['bob_bases']

        print(f"Bob's Measurement Counts: {bob_counts}")
        print(f"Bob's Basis Choices: {bob_bases}")

        shared_key = []
        alice_most_frequent_outcome = max(alice_counts.items(), key=lambda x: x[1])[0]  # Get the outcome with the highest count
        bob_most_frequent_outcome = max(bob_counts.items(), key=lambda x: x[1])[0]  # Get the outcome with the highest count

        for i in range(n_bits):
            if alice_bases[i] == bob_bases[i]: 
                alice_bit = alice_most_frequent_outcome[i]  
                bob_bit = bob_most_frequent_outcome[i]  
                if alice_bit == bob_bit: 
                    shared_key.append(alice_bit)

        # Print the most frequent shared key
        print(f"Most Frequent Shared Key: {''.join(shared_key)}")

if __name__ == "__main__":
    alice_server()
