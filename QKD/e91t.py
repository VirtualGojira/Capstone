import random
from qiskit import QuantumCircuit, Aer, execute
import time

start_time = time.time()

# Step 1: Alice and Bob prepare entangled pair (Bell state)
qc = QuantumCircuit(2, 2)  # Two qubits for Alice and Bob, two classical bits for measurement results

# Create the entangled pair (Bell state) |Φ+> = (|00> + |11>) / sqrt(2)
qc.h(0)           # Apply Hadamard gate to Alice's qubit
qc.cx(0, 1)       # Apply CNOT gate (entangling operation) from Alice's qubit to Bob's qubit

# Step 2: Alice generates random bases and measures her qubit
alice_bases = [random.choice(['Z', 'X']) for _ in range(500)]  # Alice's random bases
alice_bits = [random.getrandbits(1) for _ in range(500)]  # Alice's random bits (0 or 1)

print(f"Alice bases: {''.join(map(str, alice_bases))}")
print(f"Alice bits: {''.join(map(str, alice_bits))}")

# Step 3: Bob chooses random bases
bob_bases = [random.choice(['Z', 'X']) for _ in range(500)]  # Bob's random bases
print(f"Bob bases: {''.join(map(str, bob_bases))}")

# Step 4: Measure and record the results for Alice and Bob
backend = Aer.get_backend('qasm_simulator')  # Using the QASM simulator to simulate measurements
alice_results = []
bob_results = []

for i in range(500):
    # Copy the entanglement for each round
    qc_temp = qc.copy()

    # Alice's measurement
    if alice_bases[i] == 'Z':
        qc_temp.measure(0, 0)  # Measure Alice's qubit in the Z basis
    else:  # Alice measures in the X basis
        qc_temp.h(0)  # Rotate the basis by applying Hadamard gate
        qc_temp.measure(0, 0)

    # Bob's measurement
    if bob_bases[i] == 'Z':
        qc_temp.measure(1, 1)  # Measure Bob's qubit in the Z basis
    else:  # Bob measures in the X basis
        qc_temp.h(1)  # Rotate the basis by applying Hadamard gate
        qc_temp.measure(1, 1)

    # Execute the quantum circuit on the simulator
    job = execute(qc_temp, backend, shots=1)
    result = job.result()
    counts = result.get_counts()

    # Extract the result (measured bits from Alice and Bob)
    measured = list(counts.keys())[0]
    alice_measured_bit = int(measured[0])  # Alice's bit is the first bit of the result
    bob_measured_bit = int(measured[1])    # Bob's bit is the second bit of the result

    # Store the results
    alice_results.append(alice_measured_bit)
    bob_results.append(bob_measured_bit)

# Step 5: Generate secret keys by comparing bases
alice_key = [alice_bits[i] for i in range(500) if alice_bases[i] == bob_bases[i]]
bob_key = [bob_results[i] for i in range(500) if alice_bases[i] == bob_bases[i]]

print(f"Alice's key: {''.join(map(str, alice_key))}")
print(f"Bob's key: {''.join(map(str, bob_key))}")

# Step 6: Key verification
if alice_key == bob_key:
    print("Keys match! Secure key established.")
else:
    print("Keys do not match. Something went wrong.")

end_time = time.time()
time_taken_ms = (end_time - start_time) * 1000
print(f"Time taken: {time_taken_ms} ms")
