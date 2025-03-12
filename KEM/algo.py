from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, Aer, execute
from qiskit.circuit.library import RXGate, RYGate
import numpy as np

# Define parameters for encryption rounds
NUM_ROUNDS = 1

def substitution_layer(qc, qubits):
    for qubit in qubits:
        qc.h(qubit)
        qc.ry(np.pi / 4, qubit)

def mix_columns_layer(qc, qubits):
    for i in range(len(qubits) - 1):
        qc.cx(qubits[i], qubits[i + 1])
        qc.ry(np.pi / 3, qubits[i])

def permutation_layer(qc, qubits):
    for i in range(len(qubits) - 1, 0, -1):
        qc.swap(qubits[i], qubits[i - 1])

def encryption_round(qc, qubits):
    substitution_layer(qc, qubits)
    mix_columns_layer(qc, qubits)
    permutation_layer(qc, qubits)

def decryption_round(qc, qubits):
    for i in range(1, len(qubits)):
        qc.swap(qubits[i], qubits[i - 1])
    for i in range(len(qubits) - 2, -1, -1):
        qc.ry(-np.pi / 3, qubits[i])
        qc.cx(qubits[i], qubits[i + 1])
    for qubit in qubits:
        qc.rx(-np.pi / 4, qubit)
        qc.h(qubit)

def quantum_encrypt(qc, qubits):
    for _ in range(NUM_ROUNDS):
        encryption_round(qc, qubits)

def quantum_decrypt(qc, qubits):
    for _ in range(NUM_ROUNDS):
        decryption_round(qc, qubits)

def string_to_binary(text):
    """Convert string to binary."""
    return ''.join(format(ord(c), '08b') for c in text)

def binary_to_string(binary):
    """Convert binary string to ASCII text."""
    text = ''
    for i in range(0, len(binary), 8):
        byte = binary[i:i+8]
        text += chr(int(byte, 2))
    return text

# Message to encrypt
message = "Hello"
binary_message = string_to_binary(message)
print("Binary message:", binary_message)

# Quantum Circuit Initialization
num_qubits = len(binary_message)
qr = QuantumRegister(num_qubits, 'q')
cr = ClassicalRegister(num_qubits, 'c')
qc = QuantumCircuit(qr, cr)

# Encode binary message into qubit states
for i, bit in enumerate(binary_message):
    if bit == '1':
        qc.x(qr[i])  # Apply X gate for '1' bit

# Encryption process
quantum_encrypt(qc, qr)

# Measure encrypted state (to simulate an encrypted readout)
encrypted_circuit = qc.copy()
encrypted_circuit.measure(qr, cr)

# Execute encryption
simulator = Aer.get_backend('qasm_simulator')
job = execute(encrypted_circuit, simulator, shots=100)  # Increased shots for better results
result = job.result()
counts = result.get_counts(encrypted_circuit)
encrypted_binary = max(counts, key=counts.get)  # Get the most likely outcome

print("Encrypted binary message:", encrypted_binary)

# Add decryption process
quantum_decrypt(qc, qr)

# Measure to get decrypted message
qc.measure(qr, cr)

# Execute decryption
job = execute(qc, simulator, shots=100)
result = job.result()
counts = result.get_counts(qc)
decrypted_binary = max(counts, key=counts.get)  # Get the most likely outcome

# Convert binary to string to get the original message
decrypted_message = binary_to_string(decrypted_binary)
print("Decrypted binary message:", decrypted_binary)
print("Decrypted text message:", decrypted_message)
