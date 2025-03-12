import socket
import json
from qiskit import QuantumCircuit, Aer, execute
import numpy as np

# Function to recursively convert numpy.int64 to native Python int
def convert_int64_to_int(d):
    if isinstance(d, dict):
        return {k: convert_int64_to_int(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [convert_int64_to_int(i) for i in d]
    elif isinstance(d, np.int64):
        return int(d) 
    else:
        return d  

# Function to create and return the E91 entangled state (Bell state)
def create_bell_state(n_bits):
    qc = QuantumCircuit(2 * n_bits, 2 * n_bits) 
    for i in range(n_bits):
        qc.h(i)
        qc.cx(i, i + n_bits)  
    return qc

# Bob's random basis choice (0 for Z-basis, 1 for X-basis)
def bob_basis_choice():
    return np.random.choice([0, 1])  # 0: Z basis, 1: X basis

# Function to perform Bob's measurements
def bob_measurement(qc, n_bits):
    bases = []  
    for i in range(n_bits):
        basis = bob_basis_choice()
        bases.append(basis)
        if basis == 1: 
            qc.h(i + n_bits)
    qc.measure(range(n_bits, 2 * n_bits), range(n_bits, 2 * n_bits)) 
    return bases  

# Bob's client to handle key exchange
def bob_client():
    n_bits = 100  # Number of qubits for key exchange
    qc = create_bell_state(n_bits) 

    bob_bases = bob_measurement(qc, n_bits)

    # Simulate the quantum circuit using Aer
    simulator = Aer.get_backend('qasm_simulator')
    result = execute(qc, simulator, shots=1024).result()

    bob_counts = result.get_counts(qc)
    print(f"Bob's Measurement Counts: {bob_counts}")

    # Convert all numpy.int64 to native Python int in bob_counts and bob_bases
    bob_counts = convert_int64_to_int(bob_counts)
    bob_bases = convert_int64_to_int(bob_bases)

    # Prepare data to send
    bob_data = {
        'bob_counts': bob_counts,
        'bob_bases': bob_bases
    }

    # Convert to JSON string and send
    json_data = json.dumps(bob_data)

    # Create a client socket and send Bob's measurement data
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 65432))

    # Send serialized data
    client_socket.sendall(json_data.encode())
    client_socket.close()

if __name__ == "__main__":
    bob_client()
