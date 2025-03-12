import random
from qiskit import QuantumCircuit, Aer, execute
import time
start_time = time.time()

# Step 1: Alice generates random secret bits and bases
alice_bits = [random.getrandbits(1) for _ in range(500)]  # Alice's 500 secret bits (0 or 1)
alice_bases = [random.choice(['Z', 'X']) for _ in range(500)]  # Alice's random bases ('Z' or 'X')
print(f"alice bases:")
print("".join(map(str, alice_bases)))
print(f"alice bits:")
print("".join(map(str, alice_bits)))

# Step 2: Encoding Alice's qubits with Phase Gates and Controlled-NOT instead of X and H gates
encoded_qubits = []
for i in range(500):
    bit = alice_bits[i]
    base = alice_bases[i]
    
    qc = QuantumCircuit(1, 1)  # 1 qubit, 1 classical bit

    if base == 'Z':
        if bit == 1:
            qc.x(0)  
    else:  # base == 'X'
        if bit == 0:
            qc.t(0)  
        else:
            qc.x(0)  
            qc.t(0)  

    # Append the quantum circuit representing this qubit
    encoded_qubits.append(qc)


# Step 3: Bob chooses random measurement bases
bob_bases = [random.choice(['Z', 'X']) for _ in range(500)]  # Bob's random bases ('Z' or 'X')
print(f"bob bases:")
print("".join(map(str, bob_bases)))

# Step 4: Bob measures Alice's qubits
bob_bits = []
backend = Aer.get_backend('qasm_simulator')  # Using the QASM simulator to simulate measurements

for i in range(500):
    qc = encoded_qubits[i]
    base = bob_bases[i]
    
    if base == 'Z':
        qc.measure(0, 0)  # Measure in the Z basis (no gate needed)
    else:  # base == 'X'
        qc.t(0)  
        qc.measure(0, 0)

    # Execute the quantum circuit on the simulator
    job = execute(qc, backend, shots=1)
    result = job.result()
    counts = result.get_counts()

    # Get the measured bit (most likely outcome)
    measured_bit = int(list(counts.keys())[0], 2)
    bob_bits.append(measured_bit)

# Step 6: Generating secret keys
alice_key = [alice_bits[i] for i in range(500) if alice_bases[i] == bob_bases[i]]
bob_key = [bob_bits[i] for i in range(500) if alice_bases[i] == bob_bases[i]]

print(f"alice key:")
print("".join(map(str, alice_key)))
print(f"bob key:")
print("".join(map(str, bob_key)))

# Step 7: Key verification
if alice_key == bob_key:
    print("Keys match! Secure key established.")
else:
    print("Keys do not match. Something went wrong.")

end_time = time.time()
time_taken_ms = (end_time - start_time) * 1000
print(f"Time taken: {time_taken_ms} ms")